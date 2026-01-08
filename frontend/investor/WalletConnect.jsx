/**
 * Wallet Connect Component
 * Connects Solana wallet for USDC transactions
 */
import { useState, useEffect } from "react";
import { Wallet, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function WalletConnect({ userId, onConnect }) {
  const [walletAddress, setWalletAddress] = useState("");
  const [loading, setLoading] = useState(false);

  // Load existing wallet address from user on mount
  useEffect(() => {
    if (userId) {
      fetchUserWallet();
    }
  }, [userId]);

  const fetchUserWallet = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/users/${userId}`);
      if (response.ok) {
        const user = await response.json();
        if (user.wallet_address) {
          setWalletAddress(user.wallet_address);
          if (onConnect) {
            onConnect(user.wallet_address);
          }
        }
      }
    } catch (error) {
      console.error("Failed to fetch user wallet:", error);
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.100.93:8000';
      const response = await fetch(`${apiUrl}/api/users/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: address }),
      });
      if (!response.ok) {
        throw new Error("Failed to save wallet address");
      }
      toast.success("Wallet address saved");
    } catch (error) {
      toast.error("Failed to save wallet address");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wallet-connect bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center mb-4">
        <Wallet className="w-6 h-6 mr-2 text-blue-600" />
        <h3 className="text-xl font-bold">Connect Wallet</h3>
      </div>

      {walletAddress ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <span className="font-semibold">Wallet Connected</span>
          </div>
          <p className="text-sm text-gray-600 break-all">{walletAddress}</p>
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

