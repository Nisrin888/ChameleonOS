import type { PerformanceRow } from "../lib/api";

interface Props {
  rows: PerformanceRow[];
}

const vibeBadgeColor: Record<string, string> = {
  casual: "bg-amber-100 text-amber-800",
  bold: "bg-red-100 text-red-800",
  minimalist: "bg-green-100 text-green-800",
  professional: "bg-blue-100 text-blue-800",
  luxe: "bg-purple-100 text-purple-800",
  wellness: "bg-teal-100 text-teal-800",
  athletic: "bg-orange-100 text-orange-800",
  edgy: "bg-gray-200 text-gray-800",
  default: "bg-gray-100 text-gray-600",
};

export function SourceTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
        No data yet. Visit the demo store with different UTM parameters to generate traffic.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <th className="px-4 py-3 text-left font-medium text-gray-500">Source</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Vibe</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Variation</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">Impressions</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">Conversions</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">CVR</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={`${row.variation_id}-${row.traffic_source}-${i}`}
                className="border-b border-gray-50 hover:bg-gray-50/50 transition"
              >
                <td className="px-4 py-3 font-medium">{row.traffic_source}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${vibeBadgeColor[row.vibe] || vibeBadgeColor.default}`}
                  >
                    {row.vibe}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {row.variation_name}
                  {row.is_control && (
                    <span className="ml-2 text-xs text-gray-400">(control)</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {row.impressions.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {row.conversions.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-medium tabular-nums">
                  {(row.cvr * 100).toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
