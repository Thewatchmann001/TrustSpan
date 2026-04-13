import Image from 'next/image';
import Link from 'next/link';
import { Shield } from 'lucide-react';
import { useState } from 'react';

export default function Logo({ size = 'default', showText = true, className = '', variant = 'default' }) {
  const [hasLogoImage, setHasLogoImage] = useState(true);
  
  const sizes = {
    small: { logo: 'w-8 h-8', text: 'text-lg', subtext: 'text-[10px]' },
    default: { logo: 'w-12 h-12', text: 'text-xl', subtext: 'text-xs' },
    large: { logo: 'w-16 h-16', text: 'text-2xl md:text-3xl', subtext: 'text-sm' },
  };

  const sizeConfig = sizes[size];
  
  // Text color classes based on variant
  const textClasses = variant === 'light' 
    ? {
        main: 'text-white',
        sub: 'text-blue-100'
      }
    : {
        main: 'bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 bg-clip-text text-transparent group-hover:from-blue-700 group-hover:via-blue-800 group-hover:to-blue-900',
        sub: 'text-blue-600'
      };

  return (
    <Link 
      href="/" 
      className={`flex items-center gap-3 group ${className}`} 
      style={{ textDecoration: 'none' }}
    >
      {/* Logo Image/Icon */}
      <div className={`relative ${sizeConfig.logo} flex-shrink-0`}>
        {hasLogoImage ? (
          <Image
            src="/trust.png"
            alt="TrustSpan Logo"
            width={size === 'small' ? 32 : size === 'default' ? 48 : 64}
            height={size === 'small' ? 32 : size === 'default' ? 48 : 64}
            className="object-contain"
            onError={() => setHasLogoImage(false)}
            priority
          />
        ) : (
          // Fallback to icon if image doesn't exist
          <div className="relative w-full h-full">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 rounded-xl transform rotate-3 group-hover:rotate-6 transition-transform duration-300 shadow-lg"></div>
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 rounded-xl transform -rotate-3 group-hover:-rotate-6 transition-transform duration-300"></div>
            <div className="relative w-full h-full bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl flex items-center justify-center shadow-xl">
              <Shield className="w-1/2 h-1/2 text-white" strokeWidth={2.5} />
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-xl pointer-events-none"></div>
          </div>
        )}
      </div>
      
      {/* TrustSpan Text - Always Visible */}
      {showText && (
        <div className="flex flex-col justify-center">
          <span className={`${sizeConfig.text} font-extrabold ${textClasses.main} transition-all duration-300 leading-tight tracking-tight whitespace-nowrap drop-shadow-lg`}>
            TrustSpan
          </span>
          <span className={`${sizeConfig.subtext} ${textClasses.sub} font-semibold -mt-0.5 leading-tight whitespace-nowrap`}>
            Sierra Leone
          </span>
        </div>
      )}
    </Link>
  );
}
