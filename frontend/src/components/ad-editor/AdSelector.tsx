import { DetectedAd, formatTime } from './types';

interface AdSelectorProps {
  detectedAds: DetectedAd[];
  selectedAdIndex: number;
  onAdSelect: (index: number) => void;
}

export function AdSelector({ detectedAds, selectedAdIndex, onAdSelect }: AdSelectorProps) {
  return (
    <div className="flex gap-2 px-3 sm:px-4 py-1.5 sm:py-2 border-b border-border overflow-x-auto scroll-smooth touch-pan-x">
      {detectedAds.map((ad, index) => (
        <button
          key={index}
          onClick={() => onAdSelect(index)}
          className={`px-4 py-3 sm:px-3 sm:py-1.5 text-sm sm:text-xs rounded-lg whitespace-nowrap touch-manipulation min-h-[44px] sm:min-h-0 active:scale-95 transition-all ${
            index === selectedAdIndex
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted hover:bg-accent active:bg-accent/80'
          }`}
        >
          {formatTime(ad.start)}
        </button>
      ))}
    </div>
  );
}
