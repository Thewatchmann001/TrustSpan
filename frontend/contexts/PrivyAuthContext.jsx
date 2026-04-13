/**
 * Privy Authentication Context
 * Provides Privy authentication with automatic Solana wallet creation
 * Falls back to mock implementation if Privy is not configured
 */
import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { usePrivy } from "@privy-io/react-auth";

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";

const PRIVY_ENABLED = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_PRIVY_APP_ID && 
  process.env.NEXT_PUBLIC_PRIVY_APP_ID !== 'your-privy-app-id' &&
  process.env.NEXT_PUBLIC_PRIVY_APP_ID.trim() !== '';

const PrivyAuthContext = createContext();

export const usePrivyAuth = () => {
  const context = useContext(PrivyAuthContext);
  if (!context) {
    throw new Error('usePrivyAuth must be used within PrivyAuthProvider');
  }
  return context;
};

export const PrivyAuthProvider = ({ children }) => {
  // Fallback implementation when Privy is not configured
  const fallbackAuth = {
    ready: true,
    authenticated: false,
    user: null,
    login: async () => {
      console.warn('Privy not configured. Please set NEXT_PUBLIC_PRIVY_APP_ID in .env.local');
      return Promise.resolve();
    },
    logout: () => {
      console.warn('Privy not configured');
    },
    linkEmail: () => Promise.resolve(),
    linkWallet: () => Promise.resolve(),
    getAccessToken: () => Promise.resolve(null),
  };

  // IMPORTANT: usePrivy() must be called inside a component that's wrapped by PrivyProvider.
  // We'll catch the missing-provider error and fall back.
  let privyHook;
  let hookError = null;
  
  try {
    privyHook = usePrivy();
  } catch (error) {
    hookError = error;
    // If error is about missing PrivyProvider, use fallback
    if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
      console.error('❌ PrivyProvider not found when calling usePrivy():', error.message);
      console.error('This means PrivyAuthProvider is not inside PrivyProvider. Check _app.jsx structure.');
      privyHook = fallbackAuth;
    } else {
      console.error('❌ Error initializing Privy hook:', error);
      privyHook = fallbackAuth;
    }
  }
  
  // Use ref to maintain privyHook reference and preserve context
  const privyHookRef = useRef(privyHook);
  useEffect(() => {
    privyHookRef.current = privyHook;
  }, [privyHook]);
  
  // Don't destructure login - we need to call it directly from privyHook to preserve context
  const ready = privyHook?.ready ?? false;
  const authenticated = privyHook?.authenticated ?? false;
  const user = privyHook?.user ?? null;
  const logout = privyHook?.logout ?? fallbackAuth.logout;
  const linkEmail = privyHook?.linkEmail ?? fallbackAuth.linkEmail;
  const linkWallet = privyHook?.linkWallet ?? fallbackAuth.linkWallet;
  const getAccessToken = privyHook?.getAccessToken ?? fallbackAuth.getAccessToken;

  // Debug: Log ready state changes (only once, not repeatedly)
  useEffect(() => {
    if (typeof window !== 'undefined' && PRIVY_ENABLED && privyHook && privyHook !== fallbackAuth) {
      // Only log when ready state actually changes, not on every render
      if (ready) {
        // Privy is ready - no need to poll or warn
        return;
      }
      // If not ready, Privy is still initializing - this is normal and will resolve automatically
      // Don't poll or show warnings - Privy will become ready on its own
    }
  }, [ready, PRIVY_ENABLED, privyHook]);

  const [solanaAddress, setSolanaAddress] = useState(null);
  const [userRole, setUserRole] = useState(null);

  // Get Solana wallet address from Privy
  useEffect(() => {
    if (authenticated && user) {
      // Privy automatically creates wallets for users
      // Find a Solana wallet address from linkedAccounts (robust across Privy versions)
      const wallets = user?.linkedAccounts?.filter((account) => account.type === "wallet") || [];
      const solWallet =
        wallets.find((w) => w.chainType === "solana") ||
        wallets.find((w) => String(w.walletClientType || "").toLowerCase().includes("solana")) ||
        wallets[0];

      setSolanaAddress(solWallet?.address || null);

      // Get user role from Privy metadata or from a pre-login selection stored in localStorage.
      // This lets the user choose "investor/startup/job seeker" before Privy login,
      // while keeping backend role assignment consistent in `/api/users/privy/sync`.
      let role = user?.metadata?.role;
      if (!role && typeof window !== "undefined") {
        role = window.localStorage.getItem(PENDING_ROLE_STORAGE_KEY) || null;
        if (role) {
          console.log('📌 PrivyAuthContext: Found pending role in localStorage:', role);
        }
      }
      role = role || 'investor';
      console.log('👤 PrivyAuthContext: Setting userRole to:', role);
      setUserRole(role);
    } else {
      setSolanaAddress(null);
      setUserRole(null);
    }
  }, [authenticated, user]);

  // Ensure Solana wallet is linked
  const ensureSolanaWallet = async () => {
    if (!authenticated) {
      await wrappedLogin();
      return;
    }

    if (!solanaAddress) {
      // Link Solana wallet via Privy
      try {
        await linkWallet('solana');
      } catch (error) {
        console.error('Failed to link Solana wallet:', error);
      }
    }
  };

  // Wrap login to provide better error handling
  // IMPORTANT: Call login directly from privyHookRef to preserve React context binding
  const wrappedLogin = async (...args) => {
    const currentHook = privyHookRef.current;
    
    console.log('🔐 wrappedLogin called');
    console.log('🔐 currentHook === fallbackAuth:', currentHook === fallbackAuth);
    console.log('🔐 ready state:', ready);
    console.log('🔐 currentHook exists:', !!currentHook);
    console.log('🔐 currentHook.login type:', typeof currentHook?.login);
    console.log('🔐 currentHook.ready:', currentHook?.ready);
    
    if (currentHook === fallbackAuth || !currentHook) {
      console.error('❌ Cannot login: Using fallback Privy (PrivyProvider not found)');
      const error = new Error('Privy is not properly configured. PrivyProvider may not be wrapping the app correctly. Check _app.jsx to ensure PrivyProvider wraps PrivyAuthProvider.');
      error.name = 'PrivyNotConfigured';
      throw error;
    }
    
    // Check if we have the real login function from privyHook
    const loginFn = currentHook.login;
    if (!loginFn || typeof loginFn !== 'function') {
      console.error('❌ Cannot login: Login function not available from privyHook');
      console.error('currentHook contents:', Object.keys(currentHook || {}));
      const error = new Error('Privy login function is not available. Privy may still be initializing. Try waiting a few seconds.');
      error.name = 'PrivyNotReady';
      throw error;
    }
    
    // CRITICAL: Wait for ready state - Privy's login() will fail if not ready
    const currentReady = currentHook.ready ?? ready;
    if (!currentReady) {
      console.warn('⚠️ Privy not ready yet. Waiting for initialization...');
      console.warn('  Current ready state:', currentReady);
      console.warn('  currentHook.ready:', currentHook?.ready);
      
      // Wait up to 10 seconds for Privy to become ready
      let attempts = 0;
      const maxAttempts = 20; // 20 * 500ms = 10 seconds
      
      while (!currentHook.ready && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 500));
        attempts++;
        
        // Re-check ready from the hook
        if (currentHook.ready) {
          console.log('✅ Privy became ready after', attempts * 500, 'ms!');
          break;
        }
        
        // Log progress every 2 seconds
        if (attempts % 4 === 0) {
          console.log(`⏳ Still waiting for Privy... (${attempts * 500}ms elapsed)`);
        }
      }
      
      // Final check - if still not ready, throw helpful error
      if (!currentHook.ready) {
        console.error('❌ Privy did not become ready after 10 seconds');
        console.error('This usually means:');
        console.error('  1. Privy scripts are not loading (check Network tab for auth.privy.io)');
        console.error('  2. PrivyProvider is not properly configured');
        console.error('  3. App ID might be invalid or domain not whitelisted');
        console.error('  4. Browser extensions might be blocking Privy scripts');
        
        const error = new Error('Privy is not ready. Please wait a few seconds and try again. If the problem persists, check the browser console for Privy initialization errors.');
        error.name = 'PrivyNotReady';
        error.ready = false;
        error.waited = attempts * 500;
        throw error;
      }
    }
    
    // Verify login function is still available after waiting
    if (!currentHook.login || typeof currentHook.login !== 'function') {
      console.error('❌ Login function disappeared after waiting');
      const error = new Error('Privy login function is not available. This might indicate a context issue.');
      error.name = 'PrivyLoginUnavailable';
      throw error;
    }
    
    try {
      console.log('✅ Privy is ready! Calling login function...');
      console.log('  Ready state:', currentHook.ready);
      console.log('  Login function type:', typeof currentHook.login);
      
      // Call login directly from currentHook to preserve React context
      // Use .apply() to ensure proper context binding
      return await loginFn.apply(currentHook, args);
    } catch (error) {
      console.error('❌ Privy login error:', error);
      console.error('Error details:', {
        message: error.message,
        name: error.name,
        ready: currentHook?.ready,
        hasLogin: typeof currentHook?.login === 'function',
        currentHookType: currentHook === fallbackAuth ? 'fallback' : 'real',
      });
      
      // If error is about PrivyProvider, provide more context
      if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
        console.error('🔍 Debugging PrivyProvider context:');
        console.error('  - Check that PrivyProvider wraps PrivyAuthProvider in _app.jsx');
        console.error('  - Verify NEXT_PUBLIC_PRIVY_APP_ID is set correctly');
        console.error('  - Check browser console for Privy initialization errors');
        console.error('  - Check Network tab for requests to auth.privy.io');
      }
      
      // If error is about PrivyProvider, provide helpful message
      if (error.message?.includes('PrivyProvider') || error.message?.includes('wrap your application')) {
        const helpfulError = new Error('Privy login failed: PrivyProvider context not found. This usually means Privy is not fully initialized. The ready state is: ' + currentReady + '. Try waiting a few seconds and refreshing the page.');
        helpfulError.name = 'PrivyProviderNotFound';
        helpfulError.originalError = error;
        throw helpfulError;
      }
      
      throw error;
    }
  };

  const value = {
    ready,
    authenticated,
    user,
    login: wrappedLogin,
    logout,
    linkEmail,
    solanaAddress,
    userRole,
    ensureSolanaWallet,
    getAccessToken,
    isInvestor: userRole === 'investor',
    isStartup: userRole === 'startup' || userRole === 'founder',
    // Debug info
    _isFallback: privyHook === fallbackAuth,
    _hookError: hookError?.message,
  };

  return (
    <PrivyAuthContext.Provider value={value}>
      {children}
    </PrivyAuthContext.Provider>
  );
};

