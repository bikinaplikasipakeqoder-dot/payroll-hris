"use client";

import Card from "@/components/ui/Card";

interface TrendItem {
  period: string;
  month: string;
  amount: number;
}

interface PayrollSummaryChartProps {
  data: TrendItem[];
}

function formatAmount(amount: number): string {
  return `Rp ${Math.round(amount / 1000000)}jt`;
}

export default function PayrollSummaryChart({ data }: PayrollSummaryChartProps) {
  const maxAmount = data.length > 0 ? Math.max(...data.map((d) => d.amount)) : 1;

  return (
    <Card title="Tren Payroll Bulanan">
      <div className="space-y-3">
        {data.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">
            Belum ada data payroll.
          </p>
        ) : (
          data.map((item) => {
            const widthPercent = maxAmount > 0 ? (item.amount / maxAmount) * 100 : 0;
            return (
              <div key={item.period} className="flex items-center gap-3">
                <span className="text-sm text-slate-600 w-8 shrink-0">
                  {item.month}
                </span>
                <div className="flex-1 h-7 bg-slate-100 rounded-md overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-md transition-all"
                    style={{ width: `${widthPercent}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-slate-700 w-20 text-right shrink-0">
                  {formatAmount(item.amount)}
                </span>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
