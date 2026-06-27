'use client';

import { useState } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

export interface AiReport {
  report_title: string;
  report_content: string;
  generated_at: string;
  model_used: string;
}

interface ReportResultProps {
  report: AiReport;
  onRegenerate: () => void;
}

function renderContent(content: string) {
  const lines = content.split('\n');

  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc list-inside space-y-1 text-slate-700">
          {listItems.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((line, idx) => {
    if (line.startsWith('- ') || line.startsWith('• ')) {
      listItems.push(line.slice(2));
    } else {
      flushList();

      if (line.startsWith('## ')) {
        elements.push(
          <h3 key={idx} className="text-lg font-semibold text-slate-800 mt-4 mb-2">
            {line.slice(3)}
          </h3>
        );
      } else if (line.startsWith('**') && line.endsWith('**')) {
        elements.push(
          <p key={idx} className="font-bold text-slate-800">
            {line.slice(2, -2)}
          </p>
        );
      } else if (line.trim() === '') {
        elements.push(<div key={idx} className="h-2" />);
      } else {
        elements.push(
          <p key={idx} className="text-slate-700 leading-relaxed">
            {line}
          </p>
        );
      }
    }
  });

  flushList();
  return elements;
}

export default function ReportResult({ report, onRegenerate }: ReportResultProps) {
  const [copied, setCopied] = useState(false);

  const formattedDate = new Date(report.generated_at).toLocaleString('id-ID', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const handleCopy = async () => {
    await navigator.clipboard.writeText(report.report_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="p-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-xl font-bold text-slate-800">{report.report_title}</h2>
        <span className="text-xs text-slate-500 whitespace-nowrap rounded-full bg-slate-100 px-2.5 py-1">
          Model: {report.model_used}
        </span>
      </div>

      {/* Content */}
      <div className="mt-4 space-y-1">
        {renderContent(report.report_content)}
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t flex justify-between items-center">
        <span className="text-xs text-slate-400">
          Dibuat pada {formattedDate} menggunakan {report.model_used}
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? 'Tersalin!' : 'Salin'}
          </Button>
          <Button variant="secondary" size="sm" onClick={onRegenerate}>
            Generate Ulang
          </Button>
        </div>
      </div>
    </Card>
  );
}
