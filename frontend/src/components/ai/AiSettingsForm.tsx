'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { aiSettingsSchema, AiSettingsFormData } from './AiSettingsSchema';
import { AiTestConnectionResponse } from '@/types/ai';
import { api, ApiError } from '@/lib/api';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

interface AiSettingsFormProps {
  defaultValues?: Partial<AiSettingsFormData>;
  existingId?: number;
  apiKeyMasked?: string | null;
  onSuccess: () => void;
}

const PROVIDER_OPTIONS = ['OpenAI', 'Anthropic', 'Google AI', 'Custom'] as const;

const PROVIDER_HOSTS: Record<string, string> = {
  OpenAI: 'https://api.openai.com/v1',
  Anthropic: 'https://api.anthropic.com/v1',
  'Google AI': 'https://generativelanguage.googleapis.com/v1',
  Custom: '',
};

export default function AiSettingsForm({
  defaultValues,
  existingId,
  apiKeyMasked,
  onSuccess,
}: AiSettingsFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AiSettingsFormData>({
    resolver: zodResolver(aiSettingsSchema),
    defaultValues: {
      provider_name: '',
      api_key: '',
      api_host: '',
      model_name: '',
      system_prompt: '',
      temperature: 0.7,
      max_tokens: 2048,
      timeout_seconds: 9,
      is_active: true,
      ...defaultValues,
    },
  });

  const temperature = watch('temperature');
  const providerName = watch('provider_name');

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value;
    setValue('provider_name', provider);
    const host = PROVIDER_HOSTS[provider];
    if (host !== undefined) {
      setValue('api_host', host);
    }
  };

  const onSubmit = async (data: AiSettingsFormData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = { ...data };

      // If editing and api_key is empty, don't overwrite
      if (existingId && !data.api_key) {
        delete payload.api_key;
      }

      if (existingId) {
        await api.patch(`/api/v1/ai/settings/${existingId}`, payload);
      } else {
        await api.post('/api/v1/ai/settings', { ...payload, company_id: 1 });
      }
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Terjadi kesalahan saat menyimpan.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await api.post<AiTestConnectionResponse>('/api/v1/ai/test-connection', {
        company_id: 1,
      });
      if (result.status === 'ok') {
        setTestResult({ ok: true, message: `Terhubung (${result.latency_ms}ms)` });
      } else {
        setTestResult({ ok: false, message: result.message });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setTestResult({ ok: false, message: err.message });
      } else {
        setTestResult({ ok: false, message: 'Gagal menghubungi server.' });
      }
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-0">
        {/* Section 1: Provider Configuration */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Konfigurasi Provider
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider *
              </label>
              <select
                value={providerName}
                onChange={handleProviderChange}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Pilih provider</option>
                {PROVIDER_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              {errors.provider_name && (
                <p className="mt-1 text-sm text-red-600">{errors.provider_name.message}</p>
              )}
            </div>

            <Input
              label="Nama Model *"
              {...register('model_name')}
              error={errors.model_name?.message}
              placeholder="gpt-4o-mini"
            />
          </div>

          <Input
            label="Base URL"
            {...register('api_host')}
            error={errors.api_host?.message}
            placeholder="https://api.openai.com/v1"
          />
        </div>

        {/* Section 2: Authentication */}
        <div className="border-t border-gray-100 pt-6 mt-6 space-y-4">
          <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Autentikasi
          </h4>

          <div>
            <Input
              label="API Key"
              type="password"
              {...register('api_key')}
              error={errors.api_key?.message}
              placeholder="sk-..."
            />
            {existingId && apiKeyMasked && (
              <p className="mt-1 text-xs text-slate-500">
                Key tersimpan: {apiKeyMasked}. Kosongkan untuk tidak mengubah.
              </p>
            )}
          </div>
        </div>

        {/* Section 3: Model Parameters */}
        <div className="border-t border-gray-100 pt-6 mt-6 space-y-4">
          <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Parameter Model
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {temperature}
              </label>
              <input
                type="range"
                min={0}
                max={2}
                step={0.1}
                {...register('temperature', { valueAsNumber: true })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>0 (Deterministik)</span>
                <span>2 (Kreatif)</span>
              </div>
            </div>

            <Input
              label="Max Tokens"
              type="number"
              {...register('max_tokens', { valueAsNumber: true })}
              error={errors.max_tokens?.message}
              placeholder="2048"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Timeout (detik)"
              type="number"
              {...register('timeout_seconds', { valueAsNumber: true })}
              error={errors.timeout_seconds?.message}
              placeholder="9"
            />
            <div className="flex items-end">
              <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg border border-amber-100">
                Maksimal 9 detik untuk plan Vercel gratis agar tidak diputus server.
              </p>
            </div>
          </div>
        </div>

        {/* Section 4: System Prompt */}
        <div className="border-t border-gray-100 pt-6 mt-6 space-y-4">
          <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            System Prompt
          </h4>

          <div className="w-full">
            <textarea
              {...register('system_prompt')}
              rows={4}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Instruksi khusus untuk AI assistant..."
            />
            {errors.system_prompt && (
              <p className="mt-1 text-sm text-red-600">{errors.system_prompt.message}</p>
            )}
          </div>
        </div>

        {/* Section 5: Actions */}
        <div className="border-t border-gray-100 pt-6 mt-6 space-y-4">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_active"
              {...register('is_active')}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
              Aktifkan AI
            </label>
          </div>

          <div className="flex items-center gap-3">
            <Button type="submit" variant="primary" loading={isSubmitting}>
              Simpan
            </Button>
            <Button
              type="button"
              variant="secondary"
              loading={isTesting}
              onClick={handleTestConnection}
            >
              Test Koneksi
            </Button>
          </div>

          {testResult && (
            <p className={`text-sm ${testResult.ok ? 'text-green-600' : 'text-red-600'}`}>
              {testResult.ok ? '✓' : '✗'} {testResult.message}
            </p>
          )}

          {submitError && (
            <p className="text-sm text-red-600">{submitError}</p>
          )}
        </div>
      </form>
    </Card>
  );
}
