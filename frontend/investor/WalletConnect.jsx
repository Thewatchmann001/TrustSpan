/**
 * Wallet Connect Component
 * Connects Solana wallet for USDC transactions
 */
import { useState, useEffect } from "react";
import { Wallet, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import { authAPI, api } from "../lib/api";
import { Keypair } from "@solana/web3.js";

const PRIVY_ENABLED =
  typeof process.env.NEXT_PUBLIC_PRIVY_APP_ID === "string" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== "" &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== "your-privy-app-id";

export default function WalletConnect({ userId, onConnect }) {
  const { user } = useAuth();
  const [walletAddress, setWalletAddress] = useState("");
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);

  // Always fetch from API first to ensure we have the latest data
  useEffect(() => {
    if (userId) {
      fetchUserWallet();
    } else if (user?.wallet_address) {
      // Fallback to context if no userId
      setWalletAddress(user.wallet_address);
      setLoading(false);
      if (onConnect) {
        onConnect(user.wallet_address);
      }
    } else {
      setLoading(false);
    }
  }, [userId, user?.wallet_address]);

  const fetchUserWallet = async () => {
    try {
      setFetching(true);
      // Use authAPI which automatically includes the Authorization token
      const response = await authAPI.getUser(userId);
      const userData = response.data;
      
      if (userData.wallet_address) {
        setWalletAddress(userData.wallet_address);
        setLoading(false);
        if (onConnect) {
          onConnect(userData.wallet_address);
        }
      } else {
        // If wallet is missing, auto-generate for investors/startups
        // If Privy is enabled, DO NOT generate wallets here (keys would be lost).
        if (PRIVY_ENABLED) {
          setLoading(false);
        } else if (userData.role === 'investor' || userData.role === 'startup' || userData.role === 'founder') {
          await generateAndSaveWallet();
        } else {
          setLoading(false);
        }
      }
    } catch (error) {
      console.error("Failed to fetch user wallet:", error);
      if (error.response?.status === 401) {
        console.error("Unauthorized: Please login again.");
      }
      setLoading(false);
    } finally {
      setFetching(false);
    }
  };

  const generateAndSaveWallet = async () => {
    if (PRIVY_ENABLED) {
      toast.error("Privy is enabled. Please login with Privy to create your wallet.");
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      // Generate wallet using @solana/web3.js
      if (typeof window !== "undefined" && window.solana?.isPhantom) {
        // Try to connect Phantom wallet first
        const response = await window.solana.connect();
        const walletAddress = response.publicKey.toString();
        await saveWalletAddress(walletAddress);
        return;
      }
      
      // Fallback: Generate new keypair
      const keypair = Keypair.generate();
      const walletAddress = keypair.publicKey.toBase58();
      await saveWalletAddress(walletAddress);
      toast.success("Wallet address generated and saved!");
    } catch (error) {
      console.error("Failed to generate wallet:", error);
      toast.error("Failed to generate wallet. Please enter manually.");
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    // Check if Phantom wallet is available
    if (typeof window !== "undefined" && window.solana?.isPhantom) {
      try {
        const response = await window.solana.connect();
        setWalletAddress(response.publicKey.toString());
        await saveWalletAddress(response.publicKey.toString());
        toast.success("Wallet connected!");
        if (onConnect) {
          onConnect(response.publicKey.toString());
        }
      } catch (error) {
        toast.error("Failed to connect wallet");
      }
    } else {
      // Fallback: manual wallet address entry
      if (!walletAddress) {
        toast.error("Please enter a wallet address or install Phantom wallet");
        return;
      }
      await saveWalletAddress(walletAddress);
    }
  };

  const saveWalletAddress = async (address) => {
    try {
      setLoading(true);
      // Use api (axios instance) which automatically includes the Authorization token
      await api.patch(`/api/users/${userId}`, { wallet_address: address });
      toast.success("Wallet address saved");
      setWalletAddress(address);
      if (onConnect) {
        onConnect(address);
      }
    } catch (error) {
      console.error("Failed to save wallet address:", error);
      if (error.response?.status === 401) {
        toast.error("Unauthorized. Please login again.");
      } else {
        toast.error("Failed to save wallet address");
      }
    } finally {
      setLoading(false);
    }
  };

  // When Privy is enabled, just show the wallet address (no connection UI needed)
  if (PRIVY_ENABLED) {
    return (
      <div className="wallet-connect bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <Wallet className="w-6 h-6 mr-2 text-blue-600" />
          <h3 className="text-xl font-bold">Your Wallet</h3>
        </div>

        {loading ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-700 font-medium">Loading wallet address...</p>
          </div>
        ) : walletAddress ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <span className="font-semibold text-green-900">Connected via Privy</span>
            </div>
            <p className="text-sm text-gray-900 break-all font-mono mb-2 bg-white p-2 rounded border border-green-300">
              {walletAddress}
            </p>
            <p className="text-xs text-gray-600 mt-2">
              This embedded wallet was automatically created when you signed in with Privy. You can use it to sign USDC investment transactions.
            </p>
          </div>
        ) : (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-sm text-amber-900 font-semibold mb-2">
              No wallet found
            </p>
            <p className="text-xs text-amber-800">
              Please <strong>sign in with Privy</strong> on the login page to create your embedded wallet automatically.
            </p>
          </div>
        )}
      </div>
    );
  }

  // Legacy flow: When Privy is NOT enabled, show connection options
  return (
    <div className="wallet-connect bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center mb-4">
        <Wallet className="w-6 h-6 mr-2 text-blue-600" />
        <h3 className="text-xl font-bold">Connect Wallet</h3>
      </div>

      {loading ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700 font-medium">Loading wallet address...</p>
        </div>
      ) : walletAddress ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <span className="font-semibold">Wallet Address</span>
          </div>
          <p className="text-sm text-gray-900 break-all font-mono mb-2">{walletAddress}</p>
          <div className="mt-3 space-y-2">
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
              ℹ️ <strong>Note:</strong> This is a valid Solana wallet address. The account will appear on Solana Explorer after it receives its first transaction or funding.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded p-2">
              <p className="text-xs font-semibold text-blue-900 mb-1">💡 Need to fund your wallet?</p>
              <p className="text-xs text-blue-700 mb-2">
                <strong>Devnet (Test):</strong> Get free SOL at{" "}
                <a 
                  href="https://faucet.solana.com/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="underline hover:text-blue-900 font-medium"
                >
                  faucet.solana.com
                </a>
              </p>
              <p className="text-xs text-blue-700">
                Paste your address above and request airdrop. See{" "}
                <a 
                  href="/WALLET_FUNDING_GUIDE.md" 
                  target="_blank"
                  className="underline hover:text-blue-900 font-medium"
                >
                  Wallet Funding Guide
                </a> for details.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <>
          <p className="text-gray-600 mb-4">
            Connect your Solana wallet to invest using USDC stablecoins.
          </p>
          
          {typeof window !== "undefined" && window.solana?.isPhantom ? (
            <button onClick={handleConnect} className="btn-primary w-full" disabled={loading}>
              <Wallet className="w-4 h-4 mr-2" />
              Connect Phantom Wallet
            </button>
          ) : (
            <>
              <input
                type="text"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="Enter Solana wallet address"
                className="w-full px-4 py-2 border rounded-lg mb-4"
              />
              <button onClick={handleConnect} className="btn-primary w-full" disabled={loading}>
                Save Wallet Address
              </button>
              <p className="text-xs text-gray-500 mt-2">
                Or install{" "}
                <a
                  href="https://phantom.app"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Phantom Wallet
                </a>
              </p>
            </>
          )}
        </>
      )}
    </div>
  );
}

