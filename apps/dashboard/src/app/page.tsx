"use client";

import { useEffect, useState } from "react";
import { fetchDashboardData, fetchInsights, type DashboardData, type InsightsData } from "../lib/api";
import { StatsCards } from "../components/stats-cards";
import { SourceTable } from "../components/source-table";
import { VariationChart } from "../components/variation-chart";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchDashboardData();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function loadInsights() {
    try {
      setInsightsLoading(true);
      const result = await fetchInsights();
      setInsights(result);
    } catch {
      // Insights are optional — don't block dashboard
    } finally {
      setInsightsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Performance Overview</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data
              ? `Last updated: ${new Date(data.last_updated).toLocaleString()}`
              : "Loading..."}
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          <p className="font-medium">Could not load dashboard data</p>
          <p className="mt-1">{error}</p>
          <p className="mt-2 text-red-500">
            Make sure the API is running at{" "}
            <code className="bg-red-100 px-1 rounded">localhost:8000</code> and
            the database is seeded.
          </p>
        </div>
      )}

      {/* Stats Cards */}
      {data && <StatsCards summary={data.summary} />}

      {/* Content Grid */}
      {data && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold mb-3">
              Traffic Sources
            </h2>
            <SourceTable rows={data.rows} />
          </div>
          <div>
            <h2 className="text-lg font-semibold mb-3">
              Variation Performance
            </h2>
            <VariationChart rows={data.rows} />
          </div>
        </div>
      )}

      {/* Profit Pulse — AI Insights */}
      {data && data.rows.length > 0 && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 text-lg">
                &hearts;
              </div>
              <div>
                <h2 className="text-lg font-semibold text-indigo-900">Profit Pulse</h2>
                <p className="text-xs text-indigo-500">AI-generated performance insights</p>
              </div>
            </div>
            <button
              onClick={loadInsights}
              disabled={insightsLoading}
              className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {insightsLoading ? "Analyzing..." : insights ? "Refresh Insights" : "Generate Insights"}
            </button>
          </div>
          {insights ? (
            <div className="prose prose-sm max-w-none text-indigo-900">
              <div className="whitespace-pre-wrap bg-white/60 rounded-lg p-4 border border-indigo-100 text-sm leading-relaxed">
                {insights.insights}
              </div>
              {insights.error && (
                <p className="text-xs text-amber-600 mt-2">
                  Note: Using fallback analysis (AI unavailable: {insights.error})
                </p>
              )}
              <p className="text-xs text-indigo-400 mt-2">
                Generated at {new Date(insights.generated_at).toLocaleString()}
              </p>
            </div>
          ) : (
            <p className="text-sm text-indigo-600/70">
              Click &quot;Generate Insights&quot; to get an AI-powered analysis of your traffic performance, top variations, and optimization recommendations.
            </p>
          )}
        </div>
      )}

      {/* Empty state */}
      {data && data.rows.length === 0 && !error && (
        <div className="text-center py-16">
          <p className="text-4xl mb-4">📊</p>
          <h2 className="text-lg font-semibold text-gray-700">No data yet</h2>
          <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
            Visit the demo store at{" "}
            <a
              href="http://localhost:3000?utm_source=tiktok"
              className="text-indigo-600 underline"
            >
              localhost:3000
            </a>{" "}
            with different UTM parameters to generate traffic data.
          </p>
        </div>
      )}
    </div>
  );
}
