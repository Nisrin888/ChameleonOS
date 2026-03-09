import type { DashboardSummary } from "../lib/api";

interface Props {
  summary: DashboardSummary;
}

export function StatsCards({ summary }: Props) {
  const cards = [
    {
      label: "Total Impressions",
      value: summary.total_impressions.toLocaleString(),
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      label: "Conversions",
      value: summary.total_conversions.toLocaleString(),
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "Overall CVR",
      value: `${(summary.overall_cvr * 100).toFixed(2)}%`,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      label: "Lift vs Control",
      value:
        summary.lift_vs_control > 0
          ? `+${summary.lift_vs_control.toFixed(1)}%`
          : `${summary.lift_vs_control.toFixed(1)}%`,
      color: summary.lift_vs_control > 0 ? "text-emerald-600" : "text-red-600",
      bg: summary.lift_vs_control > 0 ? "bg-emerald-50" : "bg-red-50",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`${card.bg} rounded-xl p-5 border border-gray-100`}
        >
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            {card.label}
          </p>
          <p className={`text-2xl font-bold mt-1 ${card.color}`}>
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}
