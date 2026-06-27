import { z } from 'zod';

export const aiSettingsSchema = z.object({
  provider_name: z.string().min(1, 'Provider wajib dipilih'),
  api_key: z.string().optional().or(z.literal('')),
  api_host: z.string().url('URL tidak valid').optional().or(z.literal('')),
  model_name: z.string().min(1, 'Nama model wajib diisi'),
  system_prompt: z.string().optional().or(z.literal('')),
  temperature: z.number().min(0).max(2),
  max_tokens: z.number().min(1).max(128000),
  is_active: z.boolean(),
});

export type AiSettingsFormData = z.infer<typeof aiSettingsSchema>;
