"use client";

import Card from "@/components/ui/Card";

interface DepartmentItem {
  department: string;
  count: number;
}

interface EmployeeChartProps {
  data: DepartmentItem[];
}

const PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#F97316", "#84CC16"];

export default function EmployeeChart({ data }: EmployeeChartProps) {
  const total = data.reduce((sum, d) => sum + d.count, 0);

  let accumulated = 0;
  const gradientSegments = data.map((item, index) => {
    const color = PALETTE[index % PALETTE.length];
    const start = accumulated;
    const end = accumulated + (item.count / total) * 360;
    accumulated = end;
    return `${color} ${start}deg ${end}deg`;
  });
  const gradient = `conic-gradient(${gradientSegments.join(", ")})`;

  return (
    <Card title="Karyawan per Departemen">
      <div className="flex flex-col items-center">
        {total === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">
            Belum ada data karyawan per departemen.
          </p>
        ) : (
          <>
            <div className="relative w-44 h-44 mb-6">
              <div
                className="w-full h-full rounded-full"
                style={{ background: gradient }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-slate-800">{total}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-2 w-full">
              {data.map((item, index) => (
                <div key={item.department} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: PALETTE[index % PALETTE.length] }}
                  />
                  <span className="text-sm text-slate-600 truncate">
                    {item.department}
                  </span>
                  <span className="text-sm font-medium text-slate-800 ml-auto">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
