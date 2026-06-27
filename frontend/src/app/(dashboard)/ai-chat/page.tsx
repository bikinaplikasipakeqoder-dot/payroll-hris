'use client';

import ChatInterface from '@/components/ai/ChatInterface';

export default function AiChatPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">AI Chat</h1>
      <div className="h-[calc(100vh-10rem)]">
        <ChatInterface />
      </div>
    </div>
  );
}
