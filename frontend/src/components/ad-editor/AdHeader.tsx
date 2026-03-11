import { DetectedAd, formatStageName } from './types';

interface AdHeaderProps {
  selectedAdIndex: number;
  totalAds: number;
  selectedAd: DetectedAd;
  onClose?: () => void;
}

export function AdHeader({ selectedAdIndex, totalAds, selectedAd, onClose }: AdHeaderProps) {
  return (
    <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 border-b border-border">
      <div className="flex items-center gap-2 flex-wrap">
        <h3 className="text-sm font-medium">
          Ad {selectedAdIndex + 1} of {totalAds}
        </h3>
        {selectedAd.sponsor && (
          <span className="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded">
            {selectedAd.sponsor}
          </span>
        )}
        {selectedAd.scope && (
          <span className={`px-2 py-0.5 text-xs rounded ${
            selectedAd.scope === 'global'
              ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
              : selectedAd.scope === 'network'
              ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400'
              : 'bg-green-500/20 text-green-600 dark:text-green-400'
          }`}>
            {selectedAd.scope === 'global' ? 'Global' :
             selectedAd.scope === 'network' ? `Network: ${selectedAd.network_id || '?'}` :
             'Podcast'}
          </span>
        )}
        {selectedAd.detection_stage && (
          <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded">
            {formatStageName(selectedAd.detection_stage)}
          </span>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
