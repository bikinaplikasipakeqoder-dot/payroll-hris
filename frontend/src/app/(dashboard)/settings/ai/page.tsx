'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, ApiError } from '@/lib/api';
import { AiSetting } from '@/types/ai';
import { AiSettingsFormData } from '@/components/ai/AiSettingsSchema';
import AiSettingsForm from '@/components/ai/AiSettingsForm';

export default function AiSettingsPage() {
  const [settings, setSettings] = useState<AiSetting | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setNotFound(false);
    try {
      const data = await api.get<AiSetting>('/api/v1/ai/settings?company_id=1');
      setSettings(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
        setSettings(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSuccess = () => {
    setSavedMessage(true);
    fetchSettings();
    setTimeout(() => setSavedMessage(false), 3000);
  };

  const buildDefaultValues = (): Partial<AiSettingsFormData> | undefined => {
    if (!settings) return undefined;
    return {
      provider_name: settings.provider_name,
      api_key: '',
      api_host: settings.api_host || '',
      model_name: settings.model_name,
      system_prompt: settings.system_prompt || '',
      temperature: settings.temperature ?? 0.7,
      max_tokens: settings.max_tokens ?? 2048,
      timeout_seconds: settings.timeout_seconds ?? 9,
      is_active: settings.is_active,
    };
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Pengaturan AI</h1>
        <p className="text-sm text-slate-500 mt-1">
          Konfigurasi provider AI untuk fitur chat dan laporan
        </p>
      </div>

      {savedMessage && (
        <div className="mb-4 px-4 py-2 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
          Tersimpan!
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Memuat pengaturan...</p>
      ) : (
        <AiSettingsForm
          key={settings?.id ?? 'new'}
          defaultValues={buildDefaultValues()}
          existingId={notFound ? undefined : settings?.id}
          apiKeyMasked={settings?.api_key_masked}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
}
