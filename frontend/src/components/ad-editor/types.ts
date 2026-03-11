// Save status for visual feedback
export type SaveStatus = 'idle' | 'saving' | 'success' | 'error';

export interface DetectedAd {
  start: number;
  end: number;
  confidence: number;
  reason: string;
  sponsor?: string;
  pattern_id?: number;
  detection_stage?: string;
  scope?: string;
  network_id?: string;
}

export interface AdCorrection {
  type: 'confirm' | 'reject' | 'adjust';
  originalAd: DetectedAd;
  adjustedStart?: number;
  adjustedEnd?: number;
  notes?: string;
}

export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function formatStageName(stage: string): string {
  switch (stage) {
    case 'fingerprint': return 'Fingerprint';
    case 'text_pattern': return 'Pattern';
    case 'verification': return 'Pass 2';
    case 'language': return 'Language';
    default: return 'Pass 1';
  }
}
