/**
 * PrivyWrapper - Ensures PrivyProvider is always present when PrivyAuthProvider renders
 * This prevents timing issues where usePrivy() is called before PrivyProvider mounts
 */
import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { toSolanaWalletConnectors } from "@privy-io/react-auth/solana";
import RTCO_CONFIG from "../config/RTCO_CONFIG";

// IMPORTANT:
// Privy enforces an "Allowed origins" list. Using a hardcoded App ID/Client ID will often fail
// with "Origin not allowed" if that Privy app doesn't whitelist the current origin.
//
// So we only enable Privy when env vars are explicitly configured.
// Set these in `frontend/.env.local`:
// - NEXT_PUBLIC_PRIVY_APP_ID
// - NEXT_PUBLIC_PRIVY_CLIENT_ID
const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID;
const PRIVY_CLIENT_ID = process.env.NEXT_PUBLIC_PRIVY_CLIENT_ID;

const PRIVY_ENABLED =
  typeof PRIVY_APP_ID === "string" &&
  PRIVY_APP_ID.trim() !== "" &&
  PRIVY_APP_ID !== "your-privy-app-id" &&
  typeof PRIVY_CLIENT_ID === "string" &&
  PRIVY_CLIENT_ID.trim() !== "";

// Dynamically import PrivyProvider
const PrivyProvider = PRIVY_ENABLED
  ? dynamic(
      () => import("@privy-io/react-auth").then((mod) => mod.PrivyProvider),
      { ssr: false },
    )
  : null;

export default function PrivyWrapper({ children }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!PRIVY_ENABLED) {
      console.warn(
        "⚠️ Privy disabled. Set NEXT_PUBLIC_PRIVY_APP_ID and NEXT_PUBLIC_PRIVY_CLIENT_ID in frontend/.env.local",
      );
      return;
    }
    console.log("🔐 Privy enabled for origin:", window.location.origin);
    console.log("🔗 Solana RPC configured from RTCO_CONFIG");
  }, []);

  // On server or before mount, render children without PrivyProvider
  // PrivyAuthProvider will use fallback mode
  if (!PRIVY_ENABLED || !PrivyProvider || !mounted) {
    return <>{children}</>;
  }

  // Solana RPC endpoints - Privy will create the RPC client internally
  const SOLANA_DEVNET_RPC =
    "https://rpc.ankr.com/solana_devnet/35560d5ba7fa406f5658b06fc1117d59cb197bb6a99e644f8aecd26c0c21bbc1";
  const SOLANA_MAINNET_RPC = "https://api.mainnet-beta.solana.com";

  // Merge RTCO_CONFIG with Solana connectors - pass RPC URLs, not Connection objects
  // Privy internally creates the RPC client compatible with its version
  const finalConfig = {
    ...RTCO_CONFIG.appConfig,
    externalWallets: {
      solana: {
        connectors: toSolanaWalletConnectors(),
      },
    },
    solana: {
      ...RTCO_CONFIG.appConfig.solana,
      rpcs: {
        "solana:devnet": SOLANA_DEVNET_RPC,
        "solana:mainnet": SOLANA_MAINNET_RPC,
      },
    },
  };

  // Once mounted on client, render with PrivyProvider
  // Pass config (which includes solana.rpcs for embedded wallet signing)
  return (
    <PrivyProvider
      appId={PRIVY_APP_ID}
      clientId={PRIVY_CLIENT_ID}
      config={finalConfig}
      onSuccess={RTCO_CONFIG.onSuccess}
    >
      {children}
    </PrivyProvider>
  );
}
