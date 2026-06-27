"use client";

import Card from "@/components/ui/Card";

const activities = [
  {
    description: "Payroll Juni 2026 telah disetujui",
    time: "2 jam lalu",
    color: "bg-green-500",
  },
  {
    description: "3 pengajuan lembur baru",
    time: "5 jam lalu",
    color: "bg-amber-500",
  },
  {
    description: "Karyawan baru: Budi Santoso",
    time: "1 hari lalu",
    color: "bg-blue-500",
  },
  {
    description: "Payroll Mei 2026 telah dibayar",
    time: "3 hari lalu",
    color: "bg-green-500",
  },
  {
    description: "Update data BPJS: 5 karyawan",
    time: "5 hari lalu",
    color: "bg-blue-500",
  },
];

export default function RecentActivity() {
  return (
    <Card title="Aktivitas Terbaru">
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={index} className="flex items-start gap-3">
            <div
              className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${activity.color}`}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-700">{activity.description}</p>
              <p className="text-xs text-slate-400">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
