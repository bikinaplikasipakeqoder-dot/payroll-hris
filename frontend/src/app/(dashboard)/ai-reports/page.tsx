'use client';

import { useEffect, useRef, useState } from 'react';
import ReportGenerator from '@/components/ai/ReportGenerator';
import ReportResult, { AiReport } from '@/components/ai/ReportResult';
import { api, ApiError } from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

interface GenerateParams {
  report_type: string;
  period_month: number;
  period_year: number;
}

export default function AiReportsPage() {
  const [reports, setReports] = useState<AiReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<AiReport | null>(null);
  const [isConfigured, setIsConfigured] = useState(true);
  const [lastParams, setLastParams] = useState<GenerateParams | null>(null);

  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkSettings = async () => {
      try {
        await api.get('/api/v1/ai/settings?company_id=1');
        setIsConfigured(true);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setIsConfigured(false);
        }
      }
    };
    checkSettings();
  }, []);

  const handleGenerate = (report: AiReport) => {
    setReports((prev) => [report, ...prev]);
    setSelectedReport(report);
  };

  const handleRegenerate = async () => {
    if (!lastParams) return;

    try {
      const response = await api.post<AiReport>('/api/v1/ai/reports', {
        company_id: 1,
        ...lastParams,
      });
      setReports((prev) => [response, ...prev]);
      setSelectedReport(response);
    } catch {
      // Error handled silently; user can retry
    }
  };

  const handleView = (report: AiReport) => {
    setSelectedReport(report);
    resultRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 text-gray-900">Laporan AI</h1>

      <ReportGenerator
        onGenerate={(report, params) => {
          setLastParams(params);
          handleGenerate(report);
        }}
        isConfigured={isConfigured}
      />

      {selectedReport && (
        <div ref={resultRef} className="mt-6">
          <ReportResult report={selectedReport} onRegenerate={handleRegenerate} />
        </div>
      )}

      {reports.length > 1 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Riwayat Laporan</h2>
          <div className="space-y-3">
            {reports.map((report, idx) => (
              <Card key={idx} className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-800">{report.report_title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {new Date(report.generated_at).toLocaleString('id-ID', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleView(report)}
                >
                  Lihat
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
