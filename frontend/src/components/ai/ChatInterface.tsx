'use client';

import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { AiChatMessage, AiChatResponse } from '@/types/ai';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import ChatMessage from './ChatMessage';

type ContextType = 'general' | 'payroll' | 'employee' | 'tax';

const CONTEXT_OPTIONS: { label: string; value: ContextType }[] = [
  { label: 'Umum', value: 'general' },
  { label: 'Payroll', value: 'payroll' },
  { label: 'Karyawan', value: 'employee' },
  { label: 'Pajak', value: 'tax' },
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<AiChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contextType, setContextType] = useState<ContextType>('general');
  const [isConfigured, setIsConfigured] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check if AI is configured on mount
  useEffect(() => {
    const checkConfig = async () => {
      try {
        await api.get('/api/v1/ai/settings?company_id=1');
        setIsConfigured(true);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setIsConfigured(false);
        } else {
          setIsConfigured(false);
        }
      }
    };
    checkConfig();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading || !isConfigured) return;

    const userMessage: AiChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<AiChatResponse>('/api/v1/ai/chat', {
        company_id: 1,
        message: trimmed,
        context_type: contextType,
      });

      const assistantMessage: AiChatMessage = {
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Terjadi kesalahan. Silakan coba lagi.');
      }
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Top bar — Context selector */}
      <div className="flex items-center gap-2 border-b border-gray-200 p-3">
        {CONTEXT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setContextType(opt.value)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              contextType === opt.value
                ? 'bg-primary-100 text-primary-700 font-medium'
                : 'bg-gray-100 text-slate-600 hover:bg-gray-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Message area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {!isConfigured ? (
          /* Not configured state */
          <div className="flex items-center justify-center h-full">
            <Card className="max-w-sm text-center">
              <div className="text-4xl mb-3">⚠️</div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">
                AI belum dikonfigurasi
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                Konfigurasi AI diperlukan sebelum menggunakan fitur chat.
              </p>
              <a
                href="/settings/ai"
                className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                Buka Pengaturan AI →
              </a>
            </Card>
          </div>
        ) : messages.length === 0 && !isLoading ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-5xl mb-4">🤖</div>
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              Tanya apa saja tentang payroll, pajak, atau karyawan
            </h3>
            <p className="text-sm text-slate-400">
              Pilih konteks di atas untuk respons yang lebih relevan
            </p>
          </div>
        ) : (
          /* Messages */
          <>
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex items-end gap-2 px-2 py-1 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
                  <span className="text-xs font-semibold text-slate-600">AI</span>
                </div>
                <div className="bg-white border border-gray-200 text-slate-700 px-4 py-3 rounded-2xl rounded-bl-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white p-4">
        {error && (
          <p className="text-sm text-red-600 mb-2">{error}</p>
        )}
        <div className="flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ketik pesan..."
            disabled={isLoading || !isConfigured}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
          />
          <Button
            variant="primary"
            size="md"
            onClick={handleSend}
            disabled={isLoading || !isConfigured || !inputValue.trim()}
            loading={isLoading}
            className="!p-2.5"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
