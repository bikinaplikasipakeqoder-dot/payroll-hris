'use client';

import { useRef, KeyboardEvent } from 'react';

interface TemplateEditorProps {
  value: string;
  onChange: (val: string) => void;
  label: string;
  height?: string;
}

export default function TemplateEditor({
  value,
  onChange,
  label,
  height = '500px',
}: TemplateEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue = value.substring(0, start) + '\t' + value.substring(end);
      onChange(newValue);

      // Restore cursor position after React re-renders
      requestAnimationFrame(() => {
        textarea.selectionStart = start + 1;
        textarea.selectionEnd = start + 1;
      });
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full font-mono text-sm bg-gray-900 text-green-400 border border-gray-700 rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
        style={{ minHeight: height }}
        spellCheck={false}
      />
    </div>
  );
}
