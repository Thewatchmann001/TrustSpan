/**
 * RTCO Configuration for Privy v3.12.0 with Solana Devnet via Ankr
 * Real-Time Configuration Object for authentication and wallet management
 *
 * CRITICAL: Uses config.solana.rpcs format (not chains prop)
 * This is required for Privy's embedded wallet UIs to work with Solana
 */
import { Connection } from "@solana/web3.js";

// Ankr RPC endpoints for Solana
const SOLANA_DEVNET_RPC =
  "https://rpc.ankr.com/solana_devnet/35560d5ba7fa406f5658b06fc1117d59cb197bb6a99e644f8aecd26c0c21bbc1";
const SOLANA_MAINNET_RPC = "https://api.mainnet-beta.solana.com";

// Privy configuration - Solana v3.12.0 format
// Privy's useSolanaRpcClient expects RPC URL strings, not Connection instances
const RTCO_CONFIG = {
  // Main config for PrivyProvider
  appConfig: {
    loginMethods: ["email", "google", "twitter", "github"],
    appearance: {
      theme: "dark",
      accentColor: "#3b82f6",
    },
    embeddedWallets: {
      createOnLogin: "users-without-wallets",
      requireUserPasswordOnCreate: false,
      noPromptOnSignature: false,
    },
    externalWallets: {
      solana: {
        // Solana connectors will be added dynamically in PrivyWrapper
      },
    },
    // Disable wallet login first since we're using Wallet Adapter for signing
    // Privy is only used for authentication (email/google), not wallet connections
    showWalletLoginFirst: false,
    // CRITICAL: RPC configuration for embedded wallet UIs
    // Privy v3.12.0 expects RPC URL strings for useSolanaRpcClient
    // The rpcs format is used by PrivyProvider, but useSolanaRpcClient needs URL strings
    solana: {
      network: "devnet",
      rpc: SOLANA_DEVNET_RPC,
      rpcs: {
        "solana:devnet": {
          rpc: SOLANA_DEVNET_RPC,
          rpcSubscriptions: SOLANA_DEVNET_RPC.replace("https://", "wss://"),
        },
        "solana:mainnet": {
          rpc: SOLANA_MAINNET_RPC,
          rpcSubscriptions: SOLANA_MAINNET_RPC.replace("https://", "wss://"),
        },
      },
    },
    // Top-level rpcUrls for broader compatibility
    rpcUrls: {
      "solana:devnet": SOLANA_DEVNET_RPC,
      "solana:mainnet": SOLANA_MAINNET_RPC,
    },
  },

  // Success callback
  onSuccess: (user) => {
    console.log("✅ Privy authenticated - User ID:", user?.id);
  },
};

// Log config on initialization
if (typeof window !== "undefined") {
  console.log("📋 RTCO Config initialized with Solana RPC endpoints");
  console.log("🌐 Devnet RPC:", SOLANA_DEVNET_RPC);
}

export default RTCO_CONFIG;
