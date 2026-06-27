"use client";

import Card from "@/components/ui/Card";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: "blue" | "green" | "amber" | "red";
  trend?: string;
}

const colorMap = {
  blue: "bg-blue-100 text-blue-600",
  green: "bg-green-100 text-green-600",
  amber: "bg-amber-100 text-amber-600",
  red: "bg-red-100 text-red-600",
};

export default function StatCard({ title, value, icon, color, trend }: StatCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${colorMap[color]}`}
        >
          {icon}
        </div>
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-800">{value}</p>
        </div>
      </div>
      {trend && (
        <p
          className={`text-xs mt-2 ${
            trend.startsWith("+") || trend.startsWith("↑")
              ? "text-green-600"
              : "text-red-600"
          }`}
        >
          {trend}
        </p>
      )}
    </Card>
  );
}
