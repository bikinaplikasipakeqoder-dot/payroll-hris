"use client";

import Card from "@/components/ui/Card";

const data = [
  { dept: "Engineering", count: 45, color: "#2563EB" },
  { dept: "Marketing", count: 20, color: "#10B981" },
  { dept: "Finance", count: 15, color: "#F59E0B" },
  { dept: "HR", count: 10, color: "#EF4444" },
  { dept: "Operations", count: 25, color: "#8B5CF6" },
];

export default function EmployeeChart() {
  const total = data.reduce((sum, d) => sum + d.count, 0);

  // Build conic-gradient segments
  let accumulated = 0;
  const gradientSegments = data.map((item) => {
    const start = accumulated;
    const end = accumulated + (item.count / total) * 360;
    accumulated = end;
    return `${item.color} ${start}deg ${end}deg`;
  });
  const gradient = `conic-gradient(${gradientSegments.join(", ")})`;

  return (
    <Card title="Karyawan per Departemen">
      <div className="flex flex-col items-center">
        {/* Donut Chart */}
        <div className="relative w-44 h-44 mb-6">
          <div
            className="w-full h-full rounded-full"
            style={{ background: gradient }}
          />
          {/* Center hole */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-slate-800">{total}</span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 w-full">
          {data.map((item) => (
            <div key={item.dept} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-slate-600 truncate">
                {item.dept}
              </span>
              <span className="text-sm font-medium text-slate-800 ml-auto">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
