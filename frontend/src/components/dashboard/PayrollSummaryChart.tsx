"use client";

import Card from "@/components/ui/Card";

const data = [
  { month: "Jan", amount: 450000000 },
  { month: "Feb", amount: 480000000 },
  { month: "Mar", amount: 465000000 },
  { month: "Apr", amount: 520000000 },
  { month: "Mei", amount: 510000000 },
  { month: "Jun", amount: 535000000 },
];

function formatAmount(amount: number): string {
  return `Rp ${Math.round(amount / 1000000)}jt`;
}

export default function PayrollSummaryChart() {
  const maxAmount = Math.max(...data.map((d) => d.amount));

  return (
    <Card title="Tren Payroll Bulanan">
      <div className="space-y-3">
        {data.map((item) => {
          const widthPercent = (item.amount / maxAmount) * 100;
          return (
            <div key={item.month} className="flex items-center gap-3">
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
        })}
      </div>
    </Card>
  );
}
