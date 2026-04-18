/**
 * OAuth Callback Page
 * Handles OAuth redirects from Google, LinkedIn, Facebook
 * Extracts token from URL and stores it, then redirects user
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../contexts/AuthContext';
import { Loader } from 'lucide-react';

export default function AuthCallback() {
  const router = useRouter();
  const { setToken, setUser } = useAuth();

  useEffect(() => {
    const { token, user_id, role, error } = router.query;

    if (error) {
      // OAuth error - redirect to login with error message
      router.push(`/login?error=${error}`);
      return;
    }

    if (token && user_id && role) {
      // Store token and user info
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify({ id: parseInt(user_id), role }));
      }

      // Update auth context
      setToken(token);
      setUser({ id: parseInt(user_id), role });

      // Redirect based on role
      if (role === 'founder' || role === 'startup') {
        router.push('/cv-builder');
      } else if (role === 'investor') {
        router.push('/cv-builder');
      } else {
        router.push('/cv-builder');
      }
    } else {
      // Missing parameters - redirect to login
      router.push('/login?error=missing_token');
    }
  }, [router.query, router, setToken, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loader className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">Completing sign in...</p>
      </div>
    </div>
  );
}
