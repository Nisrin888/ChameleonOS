const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PUBLIC_KEY = "pk_demo_001";

export interface DashboardSummary {
  total_impressions: number;
  total_conversions: number;
  overall_cvr: number;
  control_cvr: number;
  lift_vs_control: number;
}

export interface PerformanceRow {
  traffic_source: string;
  vibe: string;
  variation_name: string;
  variation_id: string;
  impressions: number;
  conversions: number;
  cvr: number;
  is_control: boolean;
}

export interface DashboardData {
  summary: DashboardSummary;
  rows: PerformanceRow[];
  last_updated: string;
}

export async function fetchDashboardData(): Promise<DashboardData> {
  const res = await fetch(
    `${API_URL}/v1/dashboard/performance?public_key=${PUBLIC_KEY}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export interface InsightsData {
  insights: string;
  anomalies: string[];
  error?: string;
  generated_at: string;
}

export async function fetchInsights(): Promise<InsightsData> {
  const res = await fetch(
    `${API_URL}/v1/dashboard/insights?public_key=${PUBLIC_KEY}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
