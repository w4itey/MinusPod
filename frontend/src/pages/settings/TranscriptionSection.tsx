import type { WhisperModel } from '../../api/types';
import CollapsibleSection from '../../components/CollapsibleSection';

interface TranscriptionSectionProps {
  whisperModel: string;
  whisperModels: WhisperModel[] | undefined;
  onWhisperModelChange: (model: string) => void;
}

function TranscriptionSection({
  whisperModel,
  whisperModels,
  onWhisperModelChange,
}: TranscriptionSectionProps) {
  return (
    <CollapsibleSection title="Transcription">
      <div>
        <label htmlFor="whisperModel" className="block text-sm font-medium text-foreground mb-2">
          Whisper Model
        </label>
        <select
          id="whisperModel"
          value={whisperModel}
          onChange={(e) => onWhisperModelChange(e.target.value)}
          className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {whisperModels?.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name} - {model.vram} VRAM, {model.quality}
            </option>
          ))}
        </select>
        <p className="mt-1 text-sm text-muted-foreground">
          Larger models produce better transcriptions but require more GPU memory
        </p>
        {whisperModels && (
          <div className="mt-3 text-xs text-muted-foreground">
            <span className="font-medium">Current:</span> {whisperModels.find(m => m.id === whisperModel)?.speed || ''}
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
}

export default TranscriptionSection;
