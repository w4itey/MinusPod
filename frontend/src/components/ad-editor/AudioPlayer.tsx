import React from 'react';
import { Play, Pause } from 'lucide-react';
import { formatTime } from './types';

interface AudioPlayerProps {
  audioUrl: string;
  audioRef: React.Ref<HTMLAudioElement>;
  isPlaying: boolean;
  currentTime: number;
  audioDuration: number;
  onPlayPause: () => void;
  onProgressClick: (e: React.MouseEvent<HTMLDivElement>) => void;
}

export function AudioPlayer({
  audioUrl,
  audioRef,
  isPlaying,
  currentTime,
  audioDuration,
  onPlayPause,
  onProgressClick,
}: AudioPlayerProps) {
  return (
    <div className="px-4 py-3 border-b border-border">
      <audio ref={audioRef} src={audioUrl} className="hidden" />
      <div className="flex items-center gap-3">
        <button
          onClick={onPlayPause}
          className="p-2 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80 touch-manipulation"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
        </button>
        <span className="text-sm font-mono w-12">{formatTime(currentTime)}</span>
        <div
          className="flex-1 h-2 bg-muted rounded-full overflow-hidden cursor-pointer hover:h-3 transition-all"
          onClick={onProgressClick}
        >
          <div
            className="h-full bg-primary pointer-events-none"
            style={{ width: `${(currentTime / (audioDuration || 1)) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
