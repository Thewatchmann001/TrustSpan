/**
 * Investment Flow Component
 * Handles USDC investment transactions
 */
import { useState } from "react";
import { Wallet, DollarSign, CheckCircle, ExternalLink, Copy, Check } from "lucide-react";
import toast from "react-hot-toast";

export default function InvestFlow({ startupId, investorId, onSuccess }) {
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Amount, 2: Confirm, 3: Success
  const [transactionData, setTransactionData] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleInvest = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error("Please enter a valid amount");
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/investments/usdc/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          investor_id: investorId,
          startup_id: startupId,
          amount_usdc: parseFloat(amount),
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Investment failed");
      }

      const data = await response.json();
      setTransactionData(data);
      setStep(3);
      toast.success("Investment successful!");
      if (onSuccess) {
        onSuccess(data);
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
    const txSignature = transactionData?.transaction_signature;
    const explorerUrl = getExplorerUrl(txSignature);
    
    return (
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-6">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-2xl font-bold mb-2">Investment Successful!</h3>
          <p className="text-gray-600">Your USDC investment has been recorded on the Solana blockchain.</p>
        </div>

        {/* Transaction Receipt */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h4 className="font-semibold text-lg mb-4">Transaction Receipt</h4>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Amount:</span>
              <span className="font-semibold">{transactionData?.amount_usdc || amount} USDC</span>
            </div>
            
            {txSignature && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Transaction Signature:</span>
                  <button
                    onClick={() => copyToClipboard(txSignature)}
                    className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
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

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Investment Amount (USDC)</label>
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
            You are about to invest <strong>{amount} USDC</strong> in this startup.
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
            disabled={!amount || parseFloat(amount) <= 0}
          >
            Continue
          </button>
        ) : (
          <>
            <button onClick={() => setStep(1)} className="btn-secondary">
              Back
            </button>
            <button
              onClick={handleInvest}
              className="btn-primary flex-1"
              disabled={loading}
            >
              {loading ? "Processing..." : "Confirm Investment"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

