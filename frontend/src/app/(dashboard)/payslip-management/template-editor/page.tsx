'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Code, Eye, RefreshCw } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import TemplateEditor from '@/components/payslip/TemplateEditor';

const DEFAULT_TEMPLATE = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Slip Gaji - {{ employee.full_name }}</title>
</head>
<body>
  <div class="payslip">
    <div class="header">
      <h1>{{ company.name }}</h1>
      <h2>SLIP GAJI</h2>
      <p>Periode: {{ payslip.period }}</p>
    </div>
    <div class="employee-info">
      <table>
        <tr><td>Nama</td><td>: {{ employee.full_name }}</td></tr>
        <tr><td>Kode</td><td>: {{ employee.employee_code }}</td></tr>
        <tr><td>Departemen</td><td>: {{ employee.department }}</td></tr>
        <tr><td>Jabatan</td><td>: {{ employee.position }}</td></tr>
      </table>
    </div>
    <div class="salary-details">
      <h3>Pendapatan</h3>
      <table>
        <tr><td>Gaji Pokok</td><td>{{ payslip.basic_salary }}</td></tr>
        <tr><td>Tunjangan</td><td>{{ payslip.allowances }}</td></tr>
        <tr><td>Lembur</td><td>{{ payslip.overtime }}</td></tr>
        <tr class="total"><td>Total Pendapatan</td><td>{{ payslip.gross_salary }}</td></tr>
      </table>
      <h3>Potongan</h3>
      <table>
        <tr><td>PPh 21</td><td>{{ payslip.tax }}</td></tr>
        <tr><td>BPJS Kesehatan</td><td>{{ payslip.bpjs_kes }}</td></tr>
        <tr><td>BPJS Ketenagakerjaan</td><td>{{ payslip.bpjs_tk }}</td></tr>
        <tr class="total"><td>Total Potongan</td><td>{{ payslip.total_deductions }}</td></tr>
      </table>
    </div>
    <div class="net-salary">
      <h3>Gaji Bersih: {{ payslip.net_salary }}</h3>
    </div>
  </div>
</body>
</html>`;

const DEFAULT_CSS = `.payslip {
  font-family: 'Inter', sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
}
.header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 2px solid #2563EB;
  padding-bottom: 20px;
}
.header h1 { color: #1e293b; margin: 0; }
.header h2 { color: #2563EB; margin: 10px 0; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
td { padding: 8px 12px; }
.total td { font-weight: bold; border-top: 1px solid #e2e8f0; }
.net-salary { margin-top: 30px; text-align: center; }
.net-salary h3 { color: #2563EB; font-size: 1.5em; }`;

const TEMPLATE_VARIABLES = [
  { variable: '{{ company.name }}', description: 'Nama Perusahaan' },
  { variable: '{{ employee.full_name }}', description: 'Nama Karyawan' },
  { variable: '{{ employee.employee_code }}', description: 'Kode Karyawan' },
  { variable: '{{ employee.department }}', description: 'Departemen' },
  { variable: '{{ employee.position }}', description: 'Jabatan' },
  { variable: '{{ payslip.period }}', description: 'Periode Gaji' },
  { variable: '{{ payslip.basic_salary }}', description: 'Gaji Pokok' },
  { variable: '{{ payslip.allowances }}', description: 'Total Tunjangan' },
  { variable: '{{ payslip.overtime }}', description: 'Lembur' },
  { variable: '{{ payslip.gross_salary }}', description: 'Gaji Kotor' },
  { variable: '{{ payslip.tax }}', description: 'PPh 21' },
  { variable: '{{ payslip.bpjs_kes }}', description: 'BPJS Kesehatan' },
  { variable: '{{ payslip.bpjs_tk }}', description: 'BPJS Ketenagakerjaan' },
  { variable: '{{ payslip.total_deductions }}', description: 'Total Potongan' },
  { variable: '{{ payslip.net_salary }}', description: 'Gaji Bersih' },
];

export default function TemplateEditorPage() {
  const router = useRouter();
  const [htmlTemplate, setHtmlTemplate] = useState(DEFAULT_TEMPLATE);
  const [cssTemplate, setCssTemplate] = useState(DEFAULT_CSS);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showVariables, setShowVariables] = useState(true);

  const handlePreview = async () => {
    setPreviewing(true);
    setError(null);
    try {
      const response = await api.post<{ html: string }>(
        '/api/v1/payslip/templates/preview',
        { html_template: htmlTemplate, css_template: cssTemplate }
      );
      setPreviewHtml(response.html);
    } catch (err) {
      // Fallback: render locally by combining HTML + CSS
      const combined = htmlTemplate.replace(
        '</head>',
        `<style>${cssTemplate}</style></head>`
      );
      setPreviewHtml(combined);
    } finally {
      setPreviewing(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.post('/api/v1/payslip/templates', {
        html_template: htmlTemplate,
        css_template: cssTemplate,
      });
      setSuccess('Template berhasil disimpan');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Gagal menyimpan template');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setHtmlTemplate(DEFAULT_TEMPLATE);
    setCssTemplate(DEFAULT_CSS);
    setPreviewHtml(null);
    setSuccess('Template di-reset ke default');
    setTimeout(() => setSuccess(null), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/payslip-management')}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Editor Template Payslip
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Kustomisasi tampilan slip gaji PDF
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleReset}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset ke Default
          </Button>
          <Button variant="secondary" onClick={handlePreview} loading={previewing}>
            <Eye className="w-4 h-4 mr-2" />
            Preview
          </Button>
          <Button onClick={handleSave} loading={saving}>
            <Code className="w-4 h-4 mr-2" />
            Simpan Template
          </Button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3">
          <p className="text-sm text-green-700">{success}</p>
        </div>
      )}

      {/* Two-pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Pane - Editor */}
        <div className="space-y-4">
          <TemplateEditor
            label="HTML Template"
            value={htmlTemplate}
            onChange={setHtmlTemplate}
            height="400px"
          />
          <TemplateEditor
            label="CSS (Opsional)"
            value={cssTemplate}
            onChange={setCssTemplate}
            height="200px"
          />
        </div>

        {/* Right Pane - Preview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              Preview
            </label>
            <Button size="sm" variant="secondary" onClick={handlePreview} loading={previewing}>
              Refresh Preview
            </Button>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden" style={{ minHeight: '500px' }}>
            {previewHtml ? (
              <iframe
                srcDoc={previewHtml}
                className="w-full h-full border-0"
                style={{ minHeight: '620px' }}
                title="Payslip Preview"
                sandbox="allow-same-origin"
              />
            ) : (
              <div className="flex items-center justify-center h-full min-h-[500px] text-gray-400">
                <div className="text-center">
                  <Eye className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Klik &quot;Preview&quot; untuk melihat hasil template</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Variable Reference */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Variabel Template
          </h3>
          <button
            className="text-sm text-primary-600 hover:text-primary-700"
            onClick={() => setShowVariables(!showVariables)}
          >
            {showVariables ? 'Sembunyikan' : 'Tampilkan'}
          </button>
        </div>
        {showVariables && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Variabel
                  </th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">
                    Deskripsi
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {TEMPLATE_VARIABLES.map((v) => (
                  <tr key={v.variable}>
                    <td className="px-4 py-2">
                      <code className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs font-mono">
                        {v.variable}
                      </code>
                    </td>
                    <td className="px-4 py-2 text-gray-600">{v.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
