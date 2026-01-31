/**
 * BackgroundImage Component
 * Reusable component for hero and section backgrounds with overlays
 */
import Image from 'next/image';

export default function BackgroundImage({
  src,
  alt = 'Background image',
  overlay = 'default',
  className = '',
  children,
  priority = false,
}) {
  const overlayClasses = {
    default: 'bg-gradient-to-br from-slate-900/90 via-slate-800/85 to-amber-500/40',
    dark: 'bg-slate-900/85',
    light: 'bg-white/80',
    trust: 'bg-gradient-to-br from-sky-900/40 to-sky-800/40',
    career: 'bg-gradient-to-br from-sky-900/40 to-violet-900/40',
    investment: 'bg-gradient-to-br from-amber-900/40 to-sky-900/40',
    auth: 'bg-gradient-to-br from-slate-900/90 via-slate-800/85 to-slate-900/90',
  };

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Background Image with Blur */}
      <div className="absolute inset-0">
        <Image
          src={src}
          alt={alt}
          fill
          priority={priority}
          className="object-cover blur-sm"
          quality={85}
        />
      </div>

      {/* Darker Overlay for better text readability */}
      <div className={`absolute inset-0 ${overlayClasses[overlay] || overlayClasses.default}`} />

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
