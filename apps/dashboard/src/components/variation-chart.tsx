import type { PerformanceRow } from "../lib/api";

interface Props {
  rows: PerformanceRow[];
}

export function VariationChart({ rows }: Props) {
  if (rows.length === 0) return null;

  // Aggregate by variation name
  const variationMap = new Map<
    string,
    { name: string; impressions: number; conversions: number; is_control: boolean }
  >();

  for (const row of rows) {
    const key = row.variation_name;
    const existing = variationMap.get(key);
    if (existing) {
      existing.impressions += row.impressions;
      existing.conversions += row.conversions;
    } else {
      variationMap.set(key, {
        name: row.variation_name,
        impressions: row.impressions,
        conversions: row.conversions,
        is_control: row.is_control,
      });
    }
  }

  const variations = Array.from(variationMap.values());
  const maxCvr = Math.max(
    ...variations.map((v) =>
      v.impressions > 0 ? v.conversions / v.impressions : 0
    ),
    0.01
  );

  const barColors = [
    "bg-indigo-500",
    "bg-amber-500",
    "bg-emerald-500",
    "bg-rose-500",
    "bg-purple-500",
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
        Conversion Rate by Variation
      </h3>
      <div className="space-y-4">
        {variations.map((v, i) => {
          const cvr = v.impressions > 0 ? v.conversions / v.impressions : 0;
          const widthPct = Math.max((cvr / maxCvr) * 100, 2);

          return (
            <div key={v.name}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-medium text-gray-700 truncate max-w-xs">
                  {v.name}
                  {v.is_control && (
                    <span className="ml-1 text-xs text-gray-400">(control)</span>
                  )}
                </span>
                <span className="font-bold tabular-nums">
                  {(cvr * 100).toFixed(2)}%
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${v.is_control ? "bg-gray-400" : barColors[i % barColors.length]} transition-all duration-500`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
