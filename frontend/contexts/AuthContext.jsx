import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';
import { useRouter } from 'next/router';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Helper to safely get Privy auth
const usePrivyAuthSafe = () => {
  try {
    const { usePrivyAuth } = require('./PrivyAuthContext');
    return usePrivyAuth();
  } catch (e) {
    return null;
  }
};

const PENDING_ROLE_STORAGE_KEY = "trustspan_pending_role";
const ROLE_MISMATCH_MESSAGE_KEY = "trustspan_role_mismatch_message";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncFailed, setSyncFailed] = useState(false); // Guard to prevent infinite retries
  const [authError, setAuthError] = useState(null); // Store backend error messages for UI display
  const router = useRouter();

  // Get Privy auth state (safely)
  const privyAuth = usePrivyAuthSafe();

  // Sync Privy user with backend
  useEffect(() => {
    const syncPrivyUser = async () => {
      // GUARD 1: Don't retry if sync already failed (e.g., 403 role mismatch) - FATAL ERROR
      if (syncFailed) {
        console.log('⏸️ Sync previously failed (fatal error), skipping retry');
        setLoading(false);
        return;
      }

      // GUARD 2: Don't sync if there's an auth error
      if (authError) {
        console.log('⏸️ Auth error exists, skipping sync');
        setLoading(false);
        return;
      }

      // GUARD 3: Don't sync if user already exists (already synced)
      if (user) {
        setLoading(false);
        return;
      }

      if (privyAuth && privyAuth.authenticated && privyAuth.user && !user) {
        try {
          console.log('🔄 Starting Privy user sync...');
          // Get Privy user data
          const privyUser = privyAuth.user;
          let email = privyUser.email?.address || privyUser.linkedAccounts?.find(acc => acc.type === 'email')?.address;
          
          if (!email) {
            console.warn('⚠️ No email found in Privy user, using privy ID as fallback');
            email = privyUser.id.replace(/[^a-zA-Z0-9]/g, '') + '@privy.user';
          }

          // Get Solana wallet from Privy
          const solanaWallet = privyAuth.solanaAddress || 
            privyUser.linkedAccounts?.find(acc => acc.type === 'wallet' && acc.walletClientType === 'solana');

          // Get role from localStorage (set before Privy login) or default
          // Note: Backend will enforce role matching - existing user's role is authoritative
          let role = 'student'; // Default
          if (typeof window !== 'undefined') {
            const pendingRole = localStorage.getItem(PENDING_ROLE_STORAGE_KEY);
            if (pendingRole) {
              role = pendingRole;
              console.log('📌 Using pending role from localStorage:', role);
            }
          }
          // Fallback to privyAuth.userRole if available
          if (!role && privyAuth.userRole) {
            role = privyAuth.userRole;
          }

          // Sync with backend
          const syncData = {
            privy_id: privyUser.id,
            email: email,
            full_name: privyUser.name || email.split('@')[0],
            wallet_address: solanaWallet?.address || solanaWallet || null,
            role: role,
          };

          console.log('📤 Syncing with backend:', { email, role, wallet: syncData.wallet_address });
          const response = await authAPI.syncPrivy(syncData);
          const backendUser = response.data;

          console.log('✅ Backend sync successful:', { 
            id: backendUser.id, 
            role: backendUser.role,
            hasToken: !!backendUser.access_token 
          });

          // Store token and user (unified account: capabilities + active_role)
          if (backendUser.access_token) {
            if (typeof window !== 'undefined') {
              localStorage.setItem('token', backendUser.access_token);
              localStorage.setItem('user', JSON.stringify(backendUser));
              localStorage.removeItem(PENDING_ROLE_STORAGE_KEY);
            }
            setToken(backendUser.access_token);
            setUser(backendUser);
            console.log('✅ Token and user stored (active_role:', backendUser.active_role, ', capabilities:', backendUser.capabilities?.allowed_roles, ')');
          } else {
            console.error('❌ No access_token in backend response');
          }
        } catch (error) {
          console.error('❌ Failed to sync Privy user:', error);
          const errorDetail = error.response?.data?.detail || error.response?.data?.message || error.message;
          
          // Handle role mismatch error (403 from backend) - FATAL, AUTO-LOGOUT
          if (error.response?.status === 403) {
            const errorMessage = errorDetail || 'You are registered with a different role. Please select the correct role.';
            console.error('❌ Role enforcement: User tried to authenticate with wrong role');
            console.error('Error message:', errorMessage);
            
            // Extract correct role from error message if available
            // Backend format: "This email is registered as {role}. Please select '{role}' from the role dropdown..."
            let correctRole = null;
            let roleDisplayName = null;
            
            // Try to extract role from the improved backend message
            const roleMatch1 = errorMessage.match(/registered as (\w+)/i);
            const roleMatch2 = errorMessage.match(/select ['"]([^'"]+)['"]/i);
            
            if (roleMatch1) {
              correctRole = roleMatch1[1].toLowerCase();
              // Map backend role names to frontend role names
              if (correctRole === 'founder' || correctRole === 'startup') {
                correctRole = 'startup';
                roleDisplayName = 'Startup';
              } else if (correctRole === 'student' || correctRole === 'job seeker') {
                correctRole = 'student';
                roleDisplayName = 'Job Seeker';
              } else if (correctRole === 'investor') {
                roleDisplayName = 'Investor';
              }
            } else if (roleMatch2) {
              roleDisplayName = roleMatch2[1];
              // Map display name back to role value
              if (roleDisplayName.toLowerCase().includes('startup') || roleDisplayName.toLowerCase().includes('founder')) {
                correctRole = 'startup';
              } else if (roleDisplayName.toLowerCase().includes('job') || roleDisplayName.toLowerCase().includes('student')) {
                correctRole = 'student';
              } else if (roleDisplayName.toLowerCase().includes('investor')) {
                correctRole = 'investor';
              }
            }
            
            // Store error message for UI display (with correct role if extracted)
            const displayMessage = roleDisplayName
              ? `You are registered as ${roleDisplayName}. Please select "${roleDisplayName}" from the role dropdown and try again.`
              : errorMessage;
            setAuthError(displayMessage);
            
            // Store toast message in sessionStorage for display after redirect
            // Create a clear, actionable message with the correct role
            if (typeof window !== 'undefined') {
              let toastMessage;
              if (roleDisplayName) {
                // Create a clear message with the registered role and action
                toastMessage = {
                  message: `This email is registered as ${roleDisplayName}. Please select "${roleDisplayName}" from the role dropdown below.`,
                  registeredRole: roleDisplayName,
                  correctRole: correctRole,
                  type: 'role_mismatch'
                };
              } else {
                // Fallback if we couldn't extract the role
                toastMessage = {
                  message: errorMessage || 'Role mismatch detected. Please select the correct role from the dropdown.',
                  type: 'role_mismatch'
                };
              }
              sessionStorage.setItem(ROLE_MISMATCH_MESSAGE_KEY, JSON.stringify(toastMessage));
              console.log('💾 Stored role mismatch message for toast:', toastMessage);
            }
            
            // AUTO-LOGOUT: Immediately logout from Privy to reset auth state
            console.log('🔄 Auto-logging out from Privy due to role mismatch...');
            if (privyAuth && privyAuth.logout) {
              try {
                await privyAuth.logout();
                console.log('✅ Privy logout completed');
              } catch (logoutErr) {
                console.error('⚠️ Privy logout error (non-fatal):', logoutErr);
                // Continue even if Privy logout fails
              }
            }
            
            // Clear ALL auth state immediately
            if (typeof window !== 'undefined') {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              localStorage.removeItem(PENDING_ROLE_STORAGE_KEY);
              console.log('🧹 Cleared all auth state from localStorage');
            }
            setToken(null);
            setUser(null);
            
            // Set syncFailed to prevent infinite retries - FATAL ERROR STATE
            setSyncFailed(true);
            setLoading(false);
            
            // Redirect to login page to show error and allow role selection
            // Use setTimeout to ensure state updates complete first
            setTimeout(() => {
              if (router.pathname !== '/login' && router.pathname !== '/register') {
                console.log('🔄 Redirecting to login page due to role mismatch');
                router.push('/login');
              }
            }, 100);
            
            return;
          }
          
          console.error('Error details:', error.response?.data || error.message);
        }
      }
      setLoading(false);
    };

    syncPrivyUser();
  }, [privyAuth?.authenticated, privyAuth?.user, privyAuth?.solanaAddress, user, syncFailed, authError]);

  // Reset syncFailed and authError when Privy auth state changes (new login attempt)
  // Reset when user is fully logged out (no Privy auth, no token, no user)
  useEffect(() => {
    const isFullyLoggedOut = !privyAuth?.authenticated && !token && !user;
    if (isFullyLoggedOut) {
      // User is completely logged out - clear all error flags to allow fresh login
      if (syncFailed || authError) {
        console.log('🧹 Clearing auth error flags - user is fully logged out');
        setSyncFailed(false);
        setAuthError(null);
      }
    }
  }, [privyAuth?.authenticated, token, user, syncFailed, authError]);

  useEffect(() => {
    if (typeof window !== 'undefined' && !privyAuth?.authenticated) {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      if (storedToken && storedUser) {
        setToken(storedToken);
        try {
          const parsed = JSON.parse(storedUser);
          setUser(parsed);
        } catch {
          setUser(null);
        }
      }
    }
    if (!privyAuth?.authenticated) {
      setLoading(false);
    }
  }, [privyAuth?.authenticated]);

  // Fetch capabilities when user exists but has no capabilities (e.g. after refresh with old stored user)
  useEffect(() => {
    if (!token || !user?.id) return;
    if (user.capabilities?.allowed_roles?.length) return;
    authAPI.getCapabilities()
      .then((res) => {
        const caps = res.data;
        const updated = { ...user, capabilities: caps, active_role: user.active_role || user.role };
        setUser(updated);
        if (typeof window !== 'undefined') {
          localStorage.setItem('user', JSON.stringify(updated));
        }
      })
      .catch(() => {});
  }, [token, user?.id]);

  // Helper function to extract error message from API response
  const extractErrorMessage = (error) => {
    const detail = error.response?.data?.detail;
    if (!detail) return error.message || 'An error occurred';
    
    // Handle Pydantic validation errors (array of objects)
    if (Array.isArray(detail)) {
      return detail.map(err => err.msg || JSON.stringify(err)).join(', ');
    }
    
    // Handle object with message property
    if (typeof detail === 'object' && detail !== null) {
      return detail.msg || detail.message || JSON.stringify(detail);
    }
    
    // Handle string
    return String(detail);
  };

  const login = async (email, password, role = null) => {
    try {
      const loginData = { email, password };
      if (role) loginData.role = role;
      const response = await authAPI.login(loginData);
      const data = response.data;
      const { access_token, user_id, role: userRole, active_role, capabilities } = data;

      if (typeof window !== 'undefined') {
        localStorage.setItem('token', access_token);
        const userPayload = { id: user_id, role: userRole, active_role: active_role || userRole, capabilities: capabilities || {} };
        localStorage.setItem('user', JSON.stringify(userPayload));
      }

      setToken(access_token);
      setUser({ id: user_id, role: userRole, active_role: active_role || userRole, capabilities: capabilities || {} });

      const userData = await authAPI.getUser(user_id);
      const fullUser = { ...userData.data, active_role: active_role || userRole, capabilities: capabilities || {} };
      setUser(fullUser);
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(fullUser));
      }
      return { success: true, user: fullUser };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error) };
    }
  };

  const register = async (userData) => {
    try {
      console.log('📝 Registering user...', userData.email);
      const response = await authAPI.register(userData);
      console.log('✅ Registration successful, attempting auto-login...');
      
      // Auto-login after registration (with timeout handling)
      try {
        const loginResult = await login(userData.email, userData.password);
        return loginResult;
      } catch (loginError) {
        console.error('⚠️ Auto-login failed, but registration succeeded:', loginError);
        // Return success even if auto-login fails - user can login manually
        return {
          success: true,
          user: response.data,
          message: 'Registration successful. Please login.'
        };
      }
    } catch (error) {
      console.error('❌ Registration error:', error);
      
      // Handle network errors
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return {
          success: false,
          error: 'Request timed out. Please check your connection and try again.'
        };
      }
      
      if (!error.response) {
        return {
          success: false,
          error: 'Cannot connect to server. Please make sure the backend is running.'
        };
      }
      
      // Handle Pydantic validation errors
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Registration failed';
      
      if (Array.isArray(errorDetail)) {
        // Format validation errors into a readable message
        errorMessage = errorDetail.map(err => {
          const field = err.loc ? err.loc.join('.') : 'field';
          return `${field}: ${err.msg}`;
        }).join(', ');
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (errorDetail?.message) {
        errorMessage = errorDetail.message;
      }
      
      return { 
        success: false, 
        error: extractErrorMessage(error)
      };
    }
  };

  const logout = async () => {
    console.log('🚪 Logging out - clearing all auth state...');
    
    // Reset ALL auth state - complete reset
    setSyncFailed(false);
    setAuthError(null);
    
    // Clear app state immediately (synchronous)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem(PENDING_ROLE_STORAGE_KEY);
      sessionStorage.removeItem(ROLE_MISMATCH_MESSAGE_KEY);
      console.log('🧹 Cleared all localStorage and sessionStorage');
    }
    setToken(null);
    setUser(null);
    
    // Logout from Privy - await to ensure it completes
    if (privyAuth && privyAuth.logout) {
      try {
        await privyAuth.logout();
        console.log('✅ Privy logout completed');
      } catch (err) {
        console.error('Privy logout error:', err);
        // Continue with logout even if Privy fails
      }
    }
    
    // Redirect immediately
    router.push('/');
  };

  const switchRole = async (role) => {
    if (!token || !user) return { success: false, error: 'Not authenticated' };
    try {
      const res = await authAPI.switchRole(role);
      const data = res.data;
      const newToken = data.access_token;
      const activeRole = data.active_role || role;
      const capabilities = data.capabilities || user.capabilities || {};
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', newToken);
        localStorage.setItem('user', JSON.stringify({ ...user, active_role: activeRole, capabilities }));
      }
      setToken(newToken);
      setUser({ ...user, active_role: activeRole, capabilities });
      return { success: true, active_role: activeRole };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error) };
    }
  };

  const refetchCapabilities = async () => {
    if (!token) return;
    try {
      const res = await authAPI.getCapabilities();
      const caps = res.data;
      const updated = { ...user, capabilities: caps };
      setUser(updated);
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(updated));
      }
    } catch (_) {}
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    switchRole,
    refetchCapabilities,
    isAuthenticated: !!token,
    capabilities: user?.capabilities || null,
    activeRole: user?.active_role || user?.role || null,
    authError,
    syncFailed,
    clearAuthError: () => setAuthError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

