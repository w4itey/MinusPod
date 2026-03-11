import CollapsibleSection from '../../components/CollapsibleSection';

interface AdDetectionSectionProps {
  minCutConfidence: number;
  autoProcessEnabled: boolean;
  onMinCutConfidenceChange: (value: number) => void;
  onAutoProcessEnabledChange: (enabled: boolean) => void;
}

function AdDetectionSection({
  minCutConfidence,
  autoProcessEnabled,
  onMinCutConfidenceChange,
  onAutoProcessEnabledChange,
}: AdDetectionSectionProps) {
  return (
    <CollapsibleSection title="Ad Detection">
      <div className="space-y-6">
        <div>
          <label htmlFor="minCutConfidence" className="block text-sm font-medium text-foreground mb-2">
            Minimum Confidence Threshold: {Math.round(minCutConfidence * 100)}%
          </label>
          <input
            type="range"
            id="minCutConfidence"
            min="0.50"
            max="0.95"
            step="0.05"
            value={minCutConfidence}
            onChange={(e) => onMinCutConfidenceChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>More Aggressive (50%)</span>
            <span>More Conservative (95%)</span>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            Controls how confident the system must be before removing an ad.
            Lower values remove more potential ads but may include false positives.
          </p>
        </div>

        <div className="pt-3 border-t border-border">
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                autoProcessEnabled ? 'bg-primary' : 'bg-secondary'
              }`}
              onClick={() => onAutoProcessEnabledChange(!autoProcessEnabled)}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autoProcessEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </div>
            <span className="text-sm font-medium text-foreground">Auto-Process New Episodes</span>
          </label>
          <p className="mt-2 text-sm text-muted-foreground ml-14">
            Automatically download and process new episodes when feeds are refreshed. Individual podcasts can override this setting.
          </p>
        </div>
      </div>
    </CollapsibleSection>
  );
}

export default AdDetectionSection;
