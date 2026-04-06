import { useState, useEffect } from 'react';

interface CopyButtonProps {
  text: string;
  label?: string;
  copiedLabel?: string;
  className?: string;
  copiedClassName?: string;
  labelClassName?: string;
}

function CopyButton({
  text,
  label = 'Copy URL',
  copiedLabel = 'Copied!',
  className = '',
  copiedClassName = 'text-green-500',
  labelClassName = 'text-xs',
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(timer);
  }, [copied]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const input = document.createElement('input');
      input.value = text;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
    }
    setCopied(true);
  };

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 rounded transition-colors ${
        copied
          ? copiedClassName
          : 'text-muted-foreground hover:text-foreground hover:bg-accent'
      } ${className}`}
      title={label}
    >
      {copied ? (
        <svg className="w-4 h-4 animate-scale-in" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      )}
      <span className={labelClassName}>{copied ? copiedLabel : label}</span>
    </button>
  );
}

export default CopyButton;
