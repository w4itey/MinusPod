import type { ProcessingEpisode } from '../../api/settings';
import CollapsibleSection from '../../components/CollapsibleSection';

interface ProcessingQueueSectionProps {
  processingEpisodes: ProcessingEpisode[] | undefined;
  onCancel: (params: { slug: string; episodeId: string }) => void;
  cancelIsPending: boolean;
}

function ProcessingQueueSection({
  processingEpisodes,
  onCancel,
  cancelIsPending,
}: ProcessingQueueSectionProps) {
  return (
    <CollapsibleSection title="Processing Queue">
      {processingEpisodes && processingEpisodes.length > 0 ? (
        <div className="space-y-2">
          {processingEpisodes.map((episode) => (
            <div
              key={`${episode.slug}-${episode.episodeId}`}
              className="bg-secondary/50 rounded-lg p-4 flex justify-between items-center"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{episode.title}</p>
                <p className="text-sm text-muted-foreground">{episode.podcast}</p>
              </div>
              <button
                onClick={() => onCancel({ slug: episode.slug, episodeId: episode.episodeId })}
                disabled={cancelIsPending}
                className="px-3 py-1 text-sm rounded bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 transition-colors ml-4 flex-shrink-0"
              >
                {cancelIsPending ? 'Canceling...' : 'Cancel'}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No episodes currently processing</p>
      )}
    </CollapsibleSection>
  );
}

export default ProcessingQueueSection;
