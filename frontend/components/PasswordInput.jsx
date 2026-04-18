import { useState, useEffect } from 'react';
import { Eye, EyeOff, Lock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { validatePasswordStrength, calculatePasswordStrength } from '../utils/validation';

export default function PasswordInput({ 
  value, 
  onChange, 
  placeholder = "Enter your password",
  className = "",
  showIcon = true,
  required = true,
  showStrengthMeter = true,
  ...props 
}) {
  const [showPassword, setShowPassword] = useState(false);
  const [strength, setStrength] = useState({ strength: 'Weak', score: 0 });
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    if (value && showStrengthMeter) {
      const validation = validatePasswordStrength(value);
      const strengthData = calculatePasswordStrength(value);
      setStrength(strengthData);
      setSuggestions(validation.suggestions);
    } else {
      setStrength({ strength: 'Weak', score: 0 });
      setSuggestions([]);
    }
  }, [value, showStrengthMeter]);

  const getStrengthColor = () => {
    if (strength.strength === 'Strong') return 'bg-green-500';
    if (strength.strength === 'Medium') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStrengthTextColor = () => {
    if (strength.strength === 'Strong') return 'text-green-600';
    if (strength.strength === 'Medium') return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="w-full">
      <div className="relative">
        {showIcon && (
          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-blue-400 w-5 h-5 z-10" />
        )}
        <input
          type={showPassword ? "text" : "password"}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`input-field ${showIcon ? 'pl-10 pr-12' : 'pr-12'} ${className}`}
          {...props}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-blue-400 hover:text-blue-600 transition-colors duration-200 focus:outline-none"
          aria-label={showPassword ? "Hide password" : "Show password"}
        >
          {showPassword ? (
            <EyeOff className="w-5 h-5" />
          ) : (
            <Eye className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Password Strength Meter */}
      {showStrengthMeter && value && (
        <div className="mt-3 space-y-2">
          {/* Strength Bar */}
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${getStrengthColor()}`}
                style={{ width: `${strength.score}%` }}
              />
            </div>
            <span className={`text-xs font-semibold ${getStrengthTextColor()}`}>
              {strength.strength}
            </span>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="text-xs space-y-1">
              {suggestions.map((suggestion, idx) => (
                <div key={idx} className="flex items-center gap-2 text-red-600">
                  <AlertCircle className="w-3 h-3" />
                  <span>{suggestion}</span>
                </div>
              ))}
            </div>
          )}

          {/* Success Message */}
          {suggestions.length === 0 && value && (
            <div className="flex items-center gap-2 text-green-600 text-xs">
              <CheckCircle2 className="w-4 h-4" />
              <span>Password meets all requirements</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

