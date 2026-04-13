import "../styles/globals.css";
import { AuthProvider } from "../contexts/AuthContext";
import { JobsProvider } from "../contexts/JobsContext";
import { Toaster } from "react-hot-toast";
import Layout from "../components/Layout";
import Head from "next/head";
import { useEffect, useState, useMemo } from "react";
import PrivyWrapper from "../components/PrivyWrapper";
import { PrivyAuthProvider } from "../contexts/PrivyAuthContext";
import ErrorBoundary from "../components/ErrorBoundary";
import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react";
import { WalletAdapterNetwork } from "@solana/wallet-adapter-base";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import { PhantomWalletAdapter, SolflareWalletAdapter } from "@solana/wallet-adapter-wallets";
import "@solana/wallet-adapter-react-ui/styles.css";

const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID;
const PRIVY_ENABLED =
  typeof PRIVY_APP_ID === "string" &&
  PRIVY_APP_ID.trim() !== "" &&
  PRIVY_APP_ID !== "your-privy-app-id";

function MyApp({ Component, pageProps }) {
  // Fix hydration by only rendering on client
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Register Service Worker for PWA (only in production)
  useEffect(() => {
    // Skip service worker in development to avoid Fast Refresh issues
    if (process.env.NODE_ENV === "development") {
      // Unregister any existing service workers in development
      if (typeof window !== "undefined" && "serviceWorker" in navigator) {
        navigator.serviceWorker.getRegistrations().then((registrations) => {
          registrations.forEach((registration) => {
            registration.unregister();
            console.log("🔧 Service Worker unregistered for development");
          });
        });
      }
      return;
    }

    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      // Register service worker
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("✅ Service Worker registered:", registration.scope);

          // Check for updates
          registration.addEventListener("updatefound", () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener("statechange", () => {
                if (
                  newWorker.state === "installed" &&
                  navigator.serviceWorker.controller
                ) {
                  console.log("🔄 New service worker available");
                  // Optionally show update notification to user
                }
              });
            }
          });
        })
        .catch((error) => {
          console.log("❌ Service Worker registration failed:", error);
        });

      // Handle service worker updates
      let refreshing = false;
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    }

  }, []);

  // Debug: Log Privy configuration (dev-safe)
  useEffect(() => {
    if (typeof window === "undefined") return;
    console.log("🔍 Privy Configuration Check:");
    console.log("  PRIVY_ENABLED:", PRIVY_ENABLED);
    console.log(
      "  PRIVY_APP_ID:",
      PRIVY_APP_ID ? `${PRIVY_APP_ID.substring(0, 10)}...` : "NOT SET"
    );
  }, []);

  // Wallet Adapter setup (for transaction signing - Option 1: Use Wallet Adapter)
  // Privy is only used for authentication, Wallet Adapter handles signing
  // IMPORTANT: All hooks must be called before any conditional returns
  const network = WalletAdapterNetwork.Devnet;
  const endpoint = useMemo(() => {
    return process.env.NEXT_PUBLIC_SOLANA_RPC_URL || "https://api.devnet.solana.com";
  }, []);
  
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter(),
    ],
    []
  );

  // Show loading while client mounts (prevents hydration mismatch)
  if (!mounted) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f4f8' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="animate-spin" style={{ width: 40, height: 40, border: '3px solid #ddd', borderTop: '3px solid #0A66C2', borderRadius: '50%', margin: '0 auto' }}></div>
          <p style={{ marginTop: 16, color: '#666' }}>Loading TrustSpan...</p>
        </div>
      </div>
    );
  }

  const coreApp = (
    <ErrorBoundary>
      <PrivyWrapper>
        <PrivyAuthProvider>
          <ConnectionProvider endpoint={endpoint}>
            <WalletProvider wallets={wallets} autoConnect>
              <WalletModalProvider>
                <AuthProvider>
                  <JobsProvider>
                    <Layout>
                      <Component {...pageProps} />
                    </Layout>
                    <Toaster position="top-right" />
                  </JobsProvider>
                </AuthProvider>
              </WalletModalProvider>
            </WalletProvider>
          </ConnectionProvider>
        </PrivyAuthProvider>
      </PrivyWrapper>
    </ErrorBoundary>
  );

  return (
    <>
      <Head>
        <title>TrustSpan - Professional Career & Investment Platform</title>
        <meta
          name="description"
          content="AI-Powered CV Builder & Global Job Matching Platform"
        />
        <link rel="manifest" href="/manifest.json" />

        {/* LinkedIn-style Theme Colors */}
        <meta name="theme-color" content="#0A66C2" />
        <meta name="msapplication-TileColor" content="#0A66C2" />
        <meta name="msapplication-navbutton-color" content="#0A66C2" />

        {/* PWA Meta Tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="TrustSpan" />

        {/* iOS Safari */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-touch-fullscreen" content="yes" />

        {/* Viewport */}
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
        />

        {/* Open Graph / Social Media */}
        <meta property="og:type" content="website" />
        <meta
          property="og:title"
          content="TrustSpan - Professional Career & Investment Platform"
        />
        <meta
          property="og:description"
          content="AI-Powered CV Builder & Global Job Matching Platform"
        />
        <meta property="og:site_name" content="TrustSpan" />

        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="TrustSpan" />
        <meta
          name="twitter:description"
          content="AI-Powered CV Builder & Global Job Matching Platform"
        />

        {/* Favicon */}
        <link rel="icon" type="image/png" href="/trust.png" />
        <link rel="apple-touch-icon" href="/trust.png" />
      </Head>
      {coreApp}
    </>
  );
}

export default MyApp;
