import CollapsibleSection from '../../components/CollapsibleSection';

interface Podcasting20SectionProps {
  vttTranscriptsEnabled: boolean;
  chaptersEnabled: boolean;
  onVttTranscriptsEnabledChange: (enabled: boolean) => void;
  onChaptersEnabledChange: (enabled: boolean) => void;
}

function Podcasting20Section({
  vttTranscriptsEnabled,
  chaptersEnabled,
  onVttTranscriptsEnabledChange,
  onChaptersEnabledChange,
}: Podcasting20SectionProps) {
  return (
    <CollapsibleSection title="Podcasting 2.0">
      <div className="space-y-4">
        <div>
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                vttTranscriptsEnabled ? 'bg-primary' : 'bg-secondary'
              }`}
              onClick={() => onVttTranscriptsEnabledChange(!vttTranscriptsEnabled)}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  vttTranscriptsEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </div>
            <span className="text-sm font-medium text-foreground">Generate VTT Transcripts</span>
          </label>
          <p className="mt-2 text-sm text-muted-foreground ml-14">
            Create WebVTT transcripts with adjusted timestamps for podcast apps
          </p>
        </div>

        <div>
          <label className="flex items-center gap-3 cursor-pointer">
            <div
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                chaptersEnabled ? 'bg-primary' : 'bg-secondary'
              }`}
              onClick={() => onChaptersEnabledChange(!chaptersEnabled)}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  chaptersEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </div>
            <span className="text-sm font-medium text-foreground">Generate Chapters</span>
          </label>
          <p className="mt-2 text-sm text-muted-foreground ml-14">
            Create JSON chapters from ad boundaries and description timestamps
          </p>
        </div>
      </div>
    </CollapsibleSection>
  );
}

export default Podcasting20Section;
