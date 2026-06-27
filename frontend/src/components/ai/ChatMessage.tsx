'use client';

import { AiChatMessage } from '@/types/ai';

interface ChatMessageProps {
  message: AiChatMessage;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-end gap-2 px-2 py-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
          <span className="text-xs font-semibold text-slate-600">AI</span>
        </div>
      )}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Message bubble */}
        <div
          className={`px-4 py-3 max-w-[70%] whitespace-pre-wrap break-words ${
            isUser
              ? 'bg-primary-600 text-white rounded-2xl rounded-br-sm'
              : 'bg-white border border-gray-200 text-slate-700 rounded-2xl rounded-bl-sm'
          }`}
        >
          {message.content}
        </div>

        {/* Timestamp */}
        {message.timestamp && (
          <span className="text-xs text-slate-400 mt-1 px-1">
            {message.timestamp}
          </span>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-700 flex items-center justify-center">
          <span className="text-xs font-semibold text-white">U</span>
        </div>
      )}
    </div>
  );
}
