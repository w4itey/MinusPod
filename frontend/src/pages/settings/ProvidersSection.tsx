import { useEffect, useState } from 'react';
import CollapsibleSection from '../../components/CollapsibleSection';
import {
  ProviderName,
  ProviderStatus,
  ProvidersResponse,
  listProviders,
  updateProvider,
  clearProvider,
  testProvider,
} from '../../api/providers';

interface ProviderMeta {
  name: ProviderName;
  label: string;
  placeholder: string;
  hasBaseUrl: boolean;
  hasModel: boolean;
}

const PROVIDER_META: ProviderMeta[] = [
  { name: 'anthropic',  label: 'Anthropic',           placeholder: 'sk-ant-...',      hasBaseUrl: false, hasModel: false },
  { name: 'openai',     label: 'OpenAI-Compatible',   placeholder: 'sk-...',          hasBaseUrl: true,  hasModel: false },
  { name: 'openrouter', label: 'OpenRouter',          placeholder: 'sk-or-...',       hasBaseUrl: false, hasModel: false },
  { name: 'whisper',    label: 'Whisper (remote)',    placeholder: 'sk-...',          hasBaseUrl: true,  hasModel: true  },
];

function StatusBadge({ status }: { status: ProviderStatus }) {
  if (status.source === 'db') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-600 dark:text-green-400">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
        Configured
      </span>
    );
  }
  if (status.source === 'env') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
        Using env fallback
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
      <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60" />
      Not set
    </span>
  );
}

function borderClass(status: ProviderStatus) {
  if (status.source === 'db') return 'border-l-2 border-green-500/60';
  if (status.source === 'env') return 'border-l-2 border-amber-500/60';
  return 'border-l-2 border-border';
}

interface ProviderRowProps {
  meta: ProviderMeta;
  status: ProviderStatus;
  disabled: boolean;
  onSaved: (next: ProviderStatus) => void;
}

function ProviderRow({ meta, status, disabled, onSaved }: ProviderRowProps) {
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState(status.baseUrl || '');
  const [model, setModel] = useState(status.model || '');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setBaseUrl(status.baseUrl || '');
    setModel(status.model || '');
  }, [status.baseUrl, status.model]);

  async function handleSave() {
    setError(null);
    setSaving(true);
    try {
      const payload: { apiKey?: string; baseUrl?: string; model?: string } = {};
      if (apiKey) payload.apiKey = apiKey;
      if (meta.hasBaseUrl) payload.baseUrl = baseUrl;
      if (meta.hasModel) payload.model = model;
      const next = await updateProvider(meta.name, payload);
      setApiKey('');
      onSaved(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleClear() {
    if (!window.confirm(`Remove stored ${meta.label} key? The env-var fallback (if any) will be used.`)) return;
    setError(null);
    try {
      const next = await clearProvider(meta.name);
      setApiKey('');
      onSaved(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Clear failed');
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await testProvider(meta.name);
      setTestResult({ ok: r.ok, msg: r.ok ? 'OK' : (r.error || 'failed') });
    } catch (e) {
      setTestResult({ ok: false, msg: e instanceof Error ? e.message : 'failed' });
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className={`pl-3 py-3 ${borderClass(status)}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-foreground">{meta.label}</span>
        <StatusBadge status={status} />
      </div>

      <label htmlFor={`${meta.name}-key`} className="block text-sm font-medium text-foreground mb-2">API key</label>
      <input
        id={`${meta.name}-key`}
        type="password"
        autoComplete="off"
        disabled={disabled}
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        placeholder={status.configured ? '(configured - enter new value to change)' : meta.placeholder}
        className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono text-sm"
      />

      {meta.hasBaseUrl && (
        <>
          <label htmlFor={`${meta.name}-base`} className="block text-sm font-medium text-foreground mb-2 mt-3">Base URL</label>
          <input
            id={`${meta.name}-base`}
            type="text"
            disabled={disabled}
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://..."
            className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono text-sm"
          />
        </>
      )}

      {meta.hasModel && (
        <>
          <label htmlFor={`${meta.name}-model`} className="block text-sm font-medium text-foreground mb-2 mt-3">Model</label>
          <input
            id={`${meta.name}-model`}
            type="text"
            disabled={disabled}
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="whisper-1"
            className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono text-sm"
          />
        </>
      )}

      <div className="flex items-center gap-2 mt-3">
        <button
          type="button"
          disabled={disabled || saving}
          onClick={handleSave}
          className="px-3 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
        <button
          type="button"
          disabled={testing}
          onClick={handleTest}
          className="px-3 py-1.5 rounded-md border border-border text-sm font-medium hover:bg-secondary disabled:opacity-50"
        >
          {testing ? 'Testing...' : 'Test'}
        </button>
        {status.source === 'db' && (
          <button
            type="button"
            onClick={handleClear}
            className="px-3 py-1.5 rounded-md border border-border text-sm font-medium text-destructive hover:bg-secondary"
          >
            Clear
          </button>
        )}
        {testResult && (
          <span className={`text-sm ${testResult.ok ? 'text-green-600 dark:text-green-400' : 'text-destructive'}`}>
            {testResult.msg}
          </span>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
    </div>
  );
}

export default function ProvidersSection() {
  const [data, setData] = useState<ProvidersResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    listProviders().then(setData).catch((e) => setLoadError(e instanceof Error ? e.message : 'Load failed'));
  }, []);

  function updateEntry(name: ProviderName, next: ProviderStatus) {
    setData((d) => (d ? { ...d, [name]: next } : d));
  }

  return (
    <CollapsibleSection
      title="Providers & API Keys"
      subtitle="Encrypted at rest. GET endpoints never return key values."
      storageKey="settings-providers-open"
    >
      {loadError && <p className="text-sm text-destructive mb-3">{loadError}</p>}

      {data && !data.cryptoReady && (
        <div className="mb-4 p-3 rounded-lg border border-amber-500/40 bg-amber-500/10 text-sm text-amber-700 dark:text-amber-300">
          Provider key storage is locked. Set <code className="font-mono">MINUSPOD_MASTER_PASSPHRASE</code> in the
          container environment and set an admin password to enable. Existing env-var keys continue to work.
        </div>
      )}

      <p className="text-sm text-muted-foreground mb-4">
        Keys are encrypted with AES-256-GCM using a process-level key derived from{' '}
        <code className="font-mono">MINUSPOD_MASTER_PASSPHRASE</code>. Changing your admin password does not affect stored keys.
      </p>

      {data && (
        <div className="space-y-2">
          {PROVIDER_META.map((meta) => (
            <ProviderRow
              key={meta.name}
              meta={meta}
              status={data[meta.name]}
              disabled={!data.cryptoReady}
              onSaved={(next) => updateEntry(meta.name, next)}
            />
          ))}
        </div>
      )}
    </CollapsibleSection>
  );
}
