/**
 * Investment Flow Component
 * Handles USDC investment transactions
 */
import { useMemo, useState, useEffect } from "react";
import {
  Wallet,
  DollarSign,
  CheckCircle,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import toast from "react-hot-toast";
import {
  Connection,
  PublicKey,
  Transaction,
  VersionedTransaction,
  TransactionMessage,
} from "@solana/web3.js";
import {
  createAssociatedTokenAccountInstruction,
  createTransferCheckedInstruction,
  getAssociatedTokenAddressSync,
} from "@solana/spl-token";
import bs58 from "bs58";
import { usePrivyAuth } from "../contexts/PrivyAuthContext";
import { useWallet, useConnection } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";

const PRIVY_ENABLED =
  typeof process.env.NEXT_PUBLIC_PRIVY_APP_ID === "string" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== "" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== "your-privy-app-id";

export default function InvestFlow({ startupId, investorId, onSuccess }) {
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Amount, 2: Confirm, 3: Success
  const [transactionData, setTransactionData] = useState(null);
  const [copied, setCopied] = useState(false);

  const privyAuth = usePrivyAuth();

  // Option 1: Use Wallet Adapter for signing (Phantom/Solflare)
  // Privy is only used for authentication (wallet address)
  const { publicKey, signTransaction, sendTransaction, connected } =
    useWallet();
  const { connection } = useConnection();

  // Get Solana address - prefer Wallet Adapter, fallback to Privy
  const solanaAddress =
    publicKey?.toBase58() || privyAuth?.solanaAddress || null;

  // Debug logging for wallet readiness
  useEffect(() => {
    console.log("🔍 Wallet status:", {
      walletAdapterConnected: connected,
      walletAdapterPublicKey: publicKey?.toBase58(),
      privyAuthenticated: privyAuth?.authenticated,
      privySolanaAddress: privyAuth?.solanaAddress,
      finalSolanaAddress: solanaAddress,
      hasSignTransaction: !!signTransaction,
      hasSendTransaction: !!sendTransaction,
    });
  }, [
    connected,
    publicKey,
    privyAuth?.authenticated,
    solanaAddress,
    signTransaction,
    sendTransaction,
  ]);

  const handleInvest = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    if (!investorId || !startupId) {
      toast.error("Missing investor or startup information");
      console.error("❌ Missing IDs:", { investorId, startupId });
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      // If Privy is enabled, prefer user-signed flow:
      // prepare (backend) -> sign/send (Privy) -> record (backend)
      if (PRIVY_ENABLED) {
        if (!privyAuth?.authenticated) {
          throw new Error(
            "Please login with Privy to invest (embedded wallet required).",
          );
        }

        // Ensure we have a connected wallet (Wallet Adapter) for signing
        if (!connected || !publicKey) {
          const errorMsg =
            "Please connect your Solana wallet (Phantom/Solflare) to invest. Click 'Connect Wallet' if available.";
          console.error("❌ Wallet not connected:", {
            connected,
            publicKey: publicKey?.toBase58(),
            privyAddress: privyAuth?.solanaAddress,
          });
          toast.error(errorMsg, { duration: 8000 });
          setLoading(false);
          return;
        }

        if (!solanaAddress) {
          throw new Error(
            "Solana wallet address not available. Please connect your wallet and try again.",
          );
        }

        console.log("✅ Wallet ready for transaction:", {
          solanaAddress,
          walletAdapterConnected: connected,
          hasSignTransaction: !!signTransaction,
        });

        const prepareRes = await fetch(
          `${apiUrl}/api/investments/usdc/prepare`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              investor_id: investorId,
              startup_id: startupId,
              amount_usdc: parseFloat(amount),
            }),
          },
        );
        if (!prepareRes.ok) {
          const err = await prepareRes.json();
          throw new Error(err.detail || "Failed to prepare investment");
        }
        const plan = await prepareRes.json();

        // Use connection from Wallet Adapter (already configured in _app.jsx)
        // Don't create a new Connection - use the one from useConnection()

        // Use connected Phantom wallet as investor (not the Privy wallet from database)
        // This ensures the signer matches the transaction authority
        const investorPubkey = publicKey; // Connected Phantom wallet
        const recipientPubkey = new PublicKey(plan.recipient_wallet);
        const mintPubkey = new PublicKey(plan.usdc_mint);

        const investorAta = getAssociatedTokenAddressSync(
          mintPubkey,
          investorPubkey,
          false,
        );
        const recipientAta = getAssociatedTokenAddressSync(
          mintPubkey,
          recipientPubkey,
          false,
        );

        // Build Transaction (using VersionedTransaction for Web3.js v2)
        let tx;
        let blockhash;
        let lastValidBlockHeight;
        try {
          // Get fresh blockhash (devnet blockhashes expire quickly)
          console.log("📤 Getting latest blockhash...");
          const result = await connection.getLatestBlockhash("confirmed");
          blockhash = result.blockhash;
          lastValidBlockHeight = result.lastValidBlockHeight;

          // Create instructions array
          const instructions = [];

          // Create ATAs if missing (user pays fees, user signs)
          const investorAtaInfo = await connection.getAccountInfo(investorAta);
          if (!investorAtaInfo) {
            console.log("Creating investor ATA:", {
              payer: publicKey.toString(),
              ata: investorAta.toString(),
              owner: investorPubkey.toString(),
              mint: mintPubkey.toString(),
            });
            instructions.push(
              createAssociatedTokenAccountInstruction(
                publicKey, // payer (connected wallet)
                investorAta,
                investorPubkey, // owner (from database)
                mintPubkey,
              ),
            );
          }

          const recipientAtaInfo =
            await connection.getAccountInfo(recipientAta);
          if (!recipientAtaInfo) {
            console.log("Creating recipient ATA:", {
              payer: publicKey.toString(),
              ata: recipientAta.toString(),
              owner: recipientPubkey.toString(),
              mint: mintPubkey.toString(),
            });
            instructions.push(
              createAssociatedTokenAccountInstruction(
                publicKey, // payer (connected wallet)
                recipientAta,
                recipientPubkey, // owner (startup wallet)
                mintPubkey,
              ),
            );
          }

          instructions.push(
            createTransferCheckedInstruction(
              investorAta,
              mintPubkey,
              recipientAta,
              investorPubkey, // authority (investor must authorize)
              BigInt(plan.amount_base_units),
              plan.decimals,
            ),
          );

          // Build message for VersionedTransaction (Web3.js v2 way)
          const message = new TransactionMessage({
            payerKey: publicKey,
            recentBlockhash: blockhash,
            instructions: instructions,
          }).compileToV0Message();

          // Create VersionedTransaction
          tx = new VersionedTransaction(message);
          console.log(
            "✓ VersionedTransaction created successfully with",
            instructions.length,
            "instructions",
          );
        } catch (e) {
          console.error("❌ Failed to create transaction:", e);
          throw new Error(`Transaction creation failed: ${e.message}`);
        }

        // Sign and send transaction using Wallet Adapter (Option 1: Recommended)
        // IMPORTANT: Use sendTransaction directly - it handles signing internally
        console.log(
          "📤 Sending transaction with Wallet Adapter (Phantom/Solflare)",
        );

        // Wrap in try-catch for graceful error handling
        let sigOut;
        try {
          if (!sendTransaction) {
            throw new Error(
              "Wallet sendTransaction function not available. Please ensure your wallet is connected.",
            );
          }

          // ✅ CORRECT: Let Wallet Adapter handle signing + sending
          // sendTransaction internally calls signTransaction and sends the transaction
          console.log(
            "✓ Using Wallet Adapter sendTransaction (handles signing internally)",
          );
          console.log("📝 Transaction details:", {
            version: tx.version,
            payerKey: tx.message?.staticAccountKeys?.[0]?.toString(),
            recentBlockhash: tx.message?.recentBlockhash,
            instructionCount: tx.message?.instructions?.length,
          });

          console.log("📝 Full VersionedTransaction object:", tx);

          let signature;
          try {
            console.log("🔍 About to send transaction, checking tx type...");
            console.log("Transaction class name:", tx.constructor.name);

            // Try method 1: Direct sendTransaction (recommended)
            console.log("🔄 Attempting sendTransaction...");
            signature = await sendTransaction(tx, connection, {
              skipPreflight: false,
              maxRetries: 3,
            });
            console.log("✅ sendTransaction succeeded:", signature);
          } catch (sendError) {
            console.error("❌ sendTransaction failed:", sendError);
            console.error("Error details:", {
              name: sendError.name,
              message: sendError.message,
              code: sendError.code,
              cause: sendError.cause,
            });

            // Fallback: Try manual sign + send approach
            console.log("🔄 Attempting fallback: manual sign + send...");

            if (!signTransaction) {
              console.error("❌ signTransaction also not available");
              throw sendError;
            }

            try {
              const signedTx = await signTransaction(tx);
              console.log("✓ Transaction signed by wallet");

              const serialized = Buffer.from(signedTx.serialize());
              signature = await connection.sendRawTransaction(serialized, {
                skipPreflight: false,
                maxRetries: 3,
              });

              console.log("✅ Manual sign+send succeeded:", signature);
            } catch (manualError) {
              console.error("❌ Manual sign+send also failed:", manualError);
              throw manualError;
            }
          }

          console.log("✓ Transaction sent, waiting for confirmation...");

          // Wait for confirmation with the last valid block height
          const confirmation = await connection.confirmTransaction(
            {
              signature,
              blockhash,
              lastValidBlockHeight,
            },
            "confirmed",
          );

          if (confirmation.value.err) {
            throw new Error(
              `Transaction failed: ${JSON.stringify(confirmation.value.err)}`,
            );
          }

          sigOut = {
            signature: signature,
            error: null,
          };

          console.log(
            "✅ Transaction confirmed via Wallet Adapter:",
            signature,
          );
        } catch (signError) {
          console.error("❌ Transaction signing error:", signError);
          const errorMsg =
            signError.message ||
            "Failed to sign transaction. Please try again.";
          toast.error(errorMsg, { duration: 6000 });
          setLoading(false);
          return; // Don't throw to prevent React crash
        }

        // Transaction signed successfully - record it
        if (!sigOut.error) {
          // Signature from Privy is already a string, from backend it's base58 encoded
          const txSignature =
            typeof sigOut.signature === "string"
              ? sigOut.signature
              : bs58.encode(sigOut.signature);

          console.log("📝 Recording investment:", {
            investor_id: investorId,
            startup_id: startupId,
            amount_usdc: parseFloat(amount),
            tx_signature: txSignature,
          });

          const recordRes = await fetch(
            `${apiUrl}/api/investments/usdc/record`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                investor_id: investorId,
                startup_id: startupId,
                amount_usdc: parseFloat(amount),
                tx_signature: txSignature,
              }),
            },
          );
          if (!recordRes.ok) {
            const err = await recordRes.json();
            console.error("❌ Record failed:", err);
            throw new Error(
              err.detail || "Failed to record investment receipt",
            );
          }
          const receipt = await recordRes.json();

          setTransactionData(receipt);
          setStep(3);
          toast.success("Investment successful! (Devnet)");
          if (onSuccess) onSuccess(receipt);
        } else {
          throw new Error(
            sigOut.error || "Transaction signing returned an error",
          );
        }
      }
    } catch (error) {
      toast.error(error.message || "Failed to process investment");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Transaction signature copied!");
    setTimeout(() => setCopied(false), 2000);
  };

  const getExplorerUrl = (txSignature) => {
    if (!txSignature || txSignature.startsWith("mock_")) return null;
    return `https://explorer.solana.com/tx/${txSignature}?cluster=devnet`;
  };

  if (step === 3) {
    const txSignature =
      transactionData?.transaction_signature || transactionData?.tx_signature;
    const explorerUrl =
      transactionData?.explorer_url || getExplorerUrl(txSignature);

    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-6">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-2xl font-bold mb-2">Investment Successful!</h3>
          <p className="text-gray-600">
            Your USDC investment has been recorded on the Solana blockchain.
          </p>
        </div>

        {/* Transaction Receipt */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h4 className="font-semibold text-lg mb-4">Transaction Receipt</h4>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Amount:</span>
              <span className="font-semibold">
                {transactionData?.amount_usdc || amount} USDC
              </span>
            </div>
            {transactionData?.recipient_wallet && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Recipient:</span>
                <span className="font-mono text-xs break-all">
                  {transactionData.recipient_wallet}
                </span>
              </div>
            )}

            {txSignature && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Transaction Signature:</span>
                  <button
                    onClick={() => copyToClipboard(txSignature)}
                    className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm"
                  >
                    {copied ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <div className="bg-white rounded p-3 font-mono text-xs break-all border">
                  {txSignature}
                </div>
              </div>
            )}

            {transactionData?.timestamp && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Timestamp:</span>
                <span className="text-sm">
                  {new Date(transactionData.timestamp).toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Solana Explorer Link */}
          {explorerUrl && (
            <div className="mt-6 pt-6 border-t">
              <a
                href={explorerUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-semibold"
              >
                <ExternalLink className="w-5 h-5" />
                View on Solana Explorer (Devnet)
              </a>
              <p className="text-xs text-gray-500 text-center mt-2">
                Click to view your transaction on the Solana blockchain
              </p>
            </div>
          )}
        </div>

        <button
          onClick={() => {
            setStep(1);
            setAmount("");
            setTransactionData(null);
          }}
          className="w-full btn-secondary"
        >
          Make Another Investment
        </button>
      </div>
    );
  }

  return (
    <div className="invest-flow bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center mb-6">
        <Wallet className="w-6 h-6 mr-2 text-blue-600" />
        <h2 className="text-2xl font-bold">Invest with USDC</h2>
      </div>

      {/* Wallet Connection Status */}
      {!connected && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="font-semibold text-yellow-800 mb-1">
                Connect Your Wallet
              </h4>
              <p className="text-sm text-yellow-700">
                Please connect your Solana wallet (Phantom or Solflare) to
                invest.
              </p>
            </div>
          </div>
          <div className="flex justify-center">
            <WalletMultiButton />
          </div>
          {solanaAddress && (
            <p className="text-xs text-yellow-600 mt-2 text-center">
              Your Privy wallet address: {solanaAddress.substring(0, 8)}...
              {solanaAddress.substring(solanaAddress.length - 8)}
            </p>
          )}
        </div>
      )}

      {connected && publicKey && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-green-800">
                ✅ Wallet Connected
              </p>
              <p className="text-xs text-green-600 mt-1">
                {publicKey.toBase58().substring(0, 8)}...
                {publicKey
                  .toBase58()
                  .substring(publicKey.toBase58().length - 8)}
              </p>
            </div>
            <WalletMultiButton />
          </div>
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Investment Amount (USDC)
        </label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
            min="0"
            step="0.01"
            disabled={!connected}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Zero fees, zero currency risk. Powered by Solana stablecoins.
        </p>
      </div>

      {step === 2 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h4 className="font-semibold mb-2">Confirm Investment</h4>
          <p className="text-sm">
            You are about to invest <strong>{amount} USDC</strong> in this
            startup.
          </p>
          <p className="text-xs text-gray-600 mt-2">
            This transaction will be recorded on the Solana blockchain.
          </p>
        </div>
      )}

      <div className="flex gap-2">
        {step === 1 ? (
          <button
            onClick={() => setStep(2)}
            className="btn-primary flex-1"
            disabled={!connected || !amount || parseFloat(amount) <= 0}
          >
            {!connected ? "Connect Wallet First" : "Continue"}
          </button>
        ) : (
          <>
            <button onClick={() => setStep(1)} className="btn-secondary">
              Back
            </button>
            <button
              onClick={handleInvest}
              className="btn-primary flex-1"
              disabled={loading || !connected}
            >
              {loading ? "Processing..." : "Confirm Investment"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
