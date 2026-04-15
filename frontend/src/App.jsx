import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  Flame,
  TrendingUp,
  Activity,
  Truck,
  Gauge,
  Zap,
  RefreshCw,
  BarChart3,
  CloudRain,
  Timer,
  MapPinned,
  Building2,
  AlertTriangle,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const API_KEY =
  import.meta.env.VITE_API_KEY || "supersecret123";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "x-api-key": API_KEY,
  },
  timeout: 8000,
});

// ------------------ FALLBACK DATA ------------------
const fallbackLatest = [
  {
    platform: "Swiggy",
    region: "Connaught Place",
    city: "Delhi",
    base_fee: 35,
    demand_supply_ratio: 0.7,
    peak_multiplier: 1.12,
    weather_multiplier: 1.04,
    traffic_multiplier: 1.07,
    busy_multiplier: 1.2,
    anomaly_multiplier: 1.0,
    platform_multiplier: 1.05,
    final_multiplier: 1.5,
    final_fee: 54,
    calculated_at: new Date().toISOString(),
  },
  {
    platform: "Zomato",
    region: "Sector 18",
    city: "Noida",
    base_fee: 32,
    demand_supply_ratio: 1.8,
    peak_multiplier: 1.12,
    weather_multiplier: 1.0,
    traffic_multiplier: 1.1,
    busy_multiplier: 1.1,
    anomaly_multiplier: 1.0,
    platform_multiplier: 1.05,
    final_multiplier: 1.3,
    final_fee: 46,
    calculated_at: new Date().toISOString(),
  },
  {
    platform: "Blinkit",
    region: "HSR Layout",
    city: "Bengaluru",
    base_fee: 28,
    demand_supply_ratio: 2.9,
    peak_multiplier: 1.18,
    weather_multiplier: 1.03,
    traffic_multiplier: 1.15,
    busy_multiplier: 1.3,
    anomaly_multiplier: 1.1,
    platform_multiplier: 0.98,
    final_multiplier: 1.8,
    final_fee: 63,
    calculated_at: new Date().toISOString(),
  },
  {
    platform: "Swiggy",
    region: "Andheri West",
    city: "Mumbai",
    base_fee: 35,
    demand_supply_ratio: 3.2,
    peak_multiplier: 1.2,
    weather_multiplier: 1.1,
    traffic_multiplier: 1.2,
    busy_multiplier: 1.2,
    anomaly_multiplier: 1.1,
    platform_multiplier: 1.05,
    final_multiplier: 2.5,
    final_fee: 88,
    calculated_at: new Date().toISOString(),
  },
];

const fallbackHistory = Array.from({ length: 30 }).map((_, i) => ({
  tick: i + 1,
  final_fee: Math.round((45 + Math.sin(i / 4) * 8 + i * 0.3) * 10) / 10,
  final_multiplier:
    Math.round((1.1 + Math.sin(i / 6) * 0.15 + i * 0.01) * 100) / 100,
  calculated_at: new Date(Date.now() - (30 - i) * 600000).toISOString(),
}));

const fallbackHeatmap = [
  0, 1, 1, 1, 1, 2, 3, 8, 7, 6, 7, 9, 10, 9, 8, 7, 7, 8, 10, 13, 14, 13, 11, 8,
].map((v, i) => ({
  hour: `${i}h`,
  value: v,
}));

// ------------------ HELPERS ------------------
function getMultiplierColor(value) {
  if (value >= 2.3) return "bg-red-500/90 text-white";
  if (value >= 1.7) return "bg-amber-500/90 text-black";
  if (value >= 1.2) return "bg-lime-300/90 text-black";
  return "bg-sky-300/90 text-black";
}

function getRelativeTime(isoString) {
  if (!isoString) return "just now";
  const diff = Math.max(
    0,
    Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  );

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function getPlatformAccent(platform) {
  if (platform === "Swiggy") {
    return {
      badge: "bg-orange-500/15 text-orange-300 border-orange-500/30",
      dot: "bg-orange-400",
      solid: "#f97316",
    };
  }
  if (platform === "Zomato") {
    return {
      badge: "bg-red-500/15 text-red-300 border-red-500/30",
      dot: "bg-red-400",
      solid: "#ef4444",
    };
  }
  if (platform === "Blinkit") {
    return {
      badge: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
      dot: "bg-yellow-400",
      solid: "#eab308",
    };
  }
  return {
    badge: "bg-zinc-500/15 text-zinc-300 border-zinc-500/30",
    dot: "bg-zinc-400",
    solid: "#71717a",
  };
}

function MetricCard({ title, value, sub, icon: Icon, accent = "text-amber-400" }) {
  return (
    <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-zinc-400 text-sm font-medium">{title}</p>
            <h3 className="text-4xl font-extrabold text-white mt-2 tracking-tight">
              {value}
            </h3>
            <p className="text-zinc-400 text-sm mt-1">{sub}</p>
          </div>
          <div className={`p-3 rounded-2xl bg-zinc-800/80 ${accent}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function App() {
  const [platform, setPlatform] = useState("All");
  const [region, setRegion] = useState("All");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const [latest, setLatest] = useState(fallbackLatest);
  const [history, setHistory] = useState(fallbackHistory);
  const [summary, setSummary] = useState(null);
  const [heatmapData, setHeatmapData] = useState(fallbackHeatmap);
  const [topSurges, setTopSurges] = useState([]);

  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("mock");
  const [errorMsg, setErrorMsg] = useState("");

  const filteredByPlatform = useMemo(() => {
    if (platform === "All") return latest;
    return latest.filter((r) => r.platform === platform);
  }, [latest, platform]);

  const regionOptions = useMemo(() => {
    const unique = [...new Set(filteredByPlatform.map((r) => r.region))].filter(Boolean);
    return ["All", ...unique];
  }, [filteredByPlatform]);

  const filteredLatest = useMemo(() => {
    let rows = filteredByPlatform;
    if (region !== "All") {
      rows = rows.filter((r) => r.region === region);
    }
    return rows;
  }, [filteredByPlatform, region]);

  const hero = useMemo(() => {
    if (filteredLatest.length > 0) {
      return [...filteredLatest].sort(
        (a, b) => Number(b.final_multiplier) - Number(a.final_multiplier)
      )[0];
    }
    if (filteredByPlatform.length > 0) {
      return [...filteredByPlatform].sort(
        (a, b) => Number(b.final_multiplier) - Number(a.final_multiplier)
      )[0];
    }
    return fallbackLatest[0];
  }, [filteredLatest, filteredByPlatform]);

  const kpis = useMemo(() => {
    const sourceRows = filteredLatest.length > 0 ? filteredLatest : filteredByPlatform;
    const fees = sourceRows.map((x) => Number(x.final_fee || 0));
    const ratios = sourceRows.map((x) => Number(x.demand_supply_ratio || 0));
    const mults = sourceRows.map((x) => Number(x.final_multiplier || 1));

    return {
      currentFare: hero?.final_fee ?? 54,
      surge: hero?.final_multiplier ?? 1.5,
      activeOrders:
        summary?.est_active_orders ??
        Math.round((hero?.demand_supply_ratio ?? 0.7) * 300 + 12),
      dsRatio: hero?.demand_supply_ratio ?? 0.7,
      avgFee:
        typeof summary?.avg_fee === "number"
          ? summary.avg_fee.toFixed(1)
          : fees.length
          ? (fees.reduce((a, b) => a + b, 0) / fees.length).toFixed(1)
          : "0",
      maxMult:
        typeof summary?.max_multiplier === "number"
          ? summary.max_multiplier.toFixed(1)
          : mults.length
          ? Math.max(...mults).toFixed(1)
          : "1.0",
      avgRatio:
        typeof summary?.avg_ds_ratio === "number"
          ? summary.avg_ds_ratio.toFixed(2)
          : ratios.length
          ? (ratios.reduce((a, b) => a + b, 0) / ratios.length).toFixed(2)
          : "0",
    };
  }, [filteredLatest, filteredByPlatform, hero, summary]);

  const anomalyRow = useMemo(() => {
    const rows = filteredLatest.length > 0 ? filteredLatest : filteredByPlatform;
    if (!rows.length) return null;

    const top = [...rows].sort(
      (a, b) => Number(b.final_multiplier) - Number(a.final_multiplier)
    )[0];

    return Number(top.final_multiplier) >= 2.3 ? top : null;
  }, [filteredLatest, filteredByPlatform]);

  const freshnessText = useMemo(() => {
    return getRelativeTime(hero?.calculated_at);
  }, [hero]);

  const topLeaderboard = useMemo(() => {
    const rows = topSurges.length > 0 ? topSurges : filteredLatest.length ? filteredLatest : filteredByPlatform;
    return [...rows]
      .sort((a, b) => Number(b.final_multiplier) - Number(a.final_multiplier))
      .slice(0, 3);
  }, [topSurges, filteredLatest, filteredByPlatform]);

  const factorCards = [
    {
      label: "Demand factor",
      value: `+${((hero?.demand_supply_ratio ?? 0.7) * 0.18).toFixed(2)}x`,
    },
    {
      label: "Supply factor",
      value: `+${(((hero?.busy_multiplier ?? 1.2) - 1) * 1).toFixed(2)}x`,
    },
    {
      label: "Weather factor",
      value: `+${(((hero?.weather_multiplier ?? 1.04) - 1) * 1).toFixed(2)}x`,
    },
    {
      label: "Peak factor",
      value: `+${(((hero?.peak_multiplier ?? 1.12) - 1) * 1).toFixed(2)}x`,
    },
    {
      label: "Traffic factor",
      value: `+${(((hero?.traffic_multiplier ?? 1.07) - 1) * 1).toFixed(2)}x`,
    },
    {
      label: "Anomaly factor",
      value: `+${(((hero?.anomaly_multiplier ?? 1.0) - 1) * 1).toFixed(2)}x`,
    },
  ];

  const liveFeedRows = useMemo(() => {
    const rows = topSurges.length > 0 ? topSurges : filteredLatest;
    let filtered = rows;

    if (platform !== "All") {
      filtered = filtered.filter((r) => r.platform === platform);
    }
    if (region !== "All") {
      filtered = filtered.filter((r) => r.region === region);
    }

    return filtered.slice(0, 5);
  }, [topSurges, filteredLatest, platform, region]);

  const platformComparison = useMemo(() => {
    const sourceRows = region === "All" ? latest : latest.filter((r) => r.region === region);

    const grouped = ["Swiggy", "Zomato", "Blinkit"].map((p) => {
      const rows = sourceRows.filter((r) => r.platform === p);
      const avg =
        rows.length > 0
          ? rows.reduce((sum, r) => sum + Number(r.final_multiplier || 1), 0) / rows.length
          : 0;

      return {
        platform: p,
        value: Number(avg.toFixed(2)),
        color: getPlatformAccent(p).solid,
      };
    });

    return grouped;
  }, [latest, region]);

  const fetchData = async () => {
    setLoading(true);
    setErrorMsg("");

    try {
      await axios.get(`${API_BASE_URL}/health`);

      const latestUrl =
        platform === "All" ? `/latest-prices` : `/latest-prices/${platform}`;

      const latestRes = await api.get(latestUrl);
      const latestRows = latestRes.data?.data || [];

      if (latestRows.length > 0) {
        setLatest(latestRows);
      }

      const historySource = latestRows.length > 0 ? latestRows : fallbackLatest;
      const historyRow =
        region !== "All"
          ? historySource.find((r) => r.region === region) || historySource[0]
          : historySource[0];

      const regionEncoded = encodeURIComponent(historyRow.region || "Connaught Place");
      const histPlatform = encodeURIComponent(historyRow.platform || "Swiggy");

      const [historyRes, summaryRes, heatmapRes, topSurgesRes] = await Promise.all([
        api.get(`/history/${histPlatform}/${regionEncoded}?limit=30`),
        api.get("/dashboard/summary"),
        api.get("/dashboard/heatmap"),
        api.get("/dashboard/top-surges?limit=5"),
      ]);

      const historyRows = historyRes.data?.data || [];
      const summaryData = summaryRes.data?.data || null;
      const heatmapRows = heatmapRes.data?.data || [];
      const surgeRows = topSurgesRes.data?.data || [];

      if (historyRows.length > 0) {
        const mapped = historyRows
          .map((x, i) => ({
            tick: i + 1,
            final_fee: x.final_fee,
            final_multiplier: x.final_multiplier,
            calculated_at: x.calculated_at,
          }))
          .reverse();

        setHistory(mapped);
      } else {
        setHistory(fallbackHistory);
      }

      if (summaryData) setSummary(summaryData);
      if (heatmapRows.length > 0) setHeatmapData(heatmapRows);
      else setHeatmapData(fallbackHeatmap);

      if (surgeRows.length > 0) setTopSurges(surgeRows);
      else setTopSurges([]);

      setApiStatus("live");
    } catch (error) {
      console.error("Dashboard API fallback:", error);
      setApiStatus("mock");
      setErrorMsg("API unavailable or unauthorized. Showing mock demo data.");
      setHistory(fallbackHistory);
      setHeatmapData(fallbackHeatmap);
      setTopSurges([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (region !== "All" && !regionOptions.includes(region)) {
      setRegion("All");
    }
  }, [regionOptions, region]);

  useEffect(() => {
    fetchData();
  }, [platform, region]);

  useEffect(() => {
    if (!autoRefresh) return;

    const id = setInterval(() => {
      fetchData();
    }, 10000);

    return () => clearInterval(id);
  }, [autoRefresh, platform, region]);

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-3xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center shadow-lg">
                <Flame className="w-7 h-7 text-amber-400" />
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <h1 className="text-2xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
                    Dynamic Pricing Control Room
                  </h1>

                  <Badge
                    className={`rounded-full px-3 py-1 border font-semibold tracking-wide ${
                      apiStatus === "live"
                        ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                        : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                    }`}
                  >
                    {apiStatus === "live" ? "LIVE API" : "MOCK MODE"}
                  </Badge>
                </div>

                <p className="text-zinc-400">
                  Swiggy • Zomato • Blinkit • Real-time Surge Intelligence
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded-2xl px-4 py-2">
                <span className="text-sm text-zinc-400">Auto Refresh</span>
                <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
              </div>

              <Select value={platform} onValueChange={setPlatform}>
                <SelectTrigger className="w-[150px] bg-zinc-950 border-zinc-800 rounded-2xl text-white">
                  <SelectValue placeholder="Platform" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                  <SelectItem value="All">All Platforms</SelectItem>
                  <SelectItem value="Swiggy">Swiggy</SelectItem>
                  <SelectItem value="Zomato">Zomato</SelectItem>
                  <SelectItem value="Blinkit">Blinkit</SelectItem>
                </SelectContent>
              </Select>

              <Select value={region} onValueChange={setRegion}>
                <SelectTrigger className="w-[170px] bg-zinc-950 border-zinc-800 rounded-2xl text-white">
                  <SelectValue placeholder="Region" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                  {regionOptions.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r === "All" ? "All Regions" : r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                onClick={fetchData}
                className="rounded-2xl bg-amber-500 hover:bg-amber-400 text-black font-semibold"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Live freshness row */}
          <div className="flex flex-wrap items-center gap-3">
            <Badge className="rounded-full px-3 py-1 bg-zinc-900 border border-zinc-700 text-zinc-300">
              Updated {freshnessText}
            </Badge>

            <Badge
              className={`rounded-full px-3 py-1 border ${
                getPlatformAccent(hero?.platform).badge
              }`}
            >
              {hero?.platform || "Unknown"}
            </Badge>

            <Badge className="rounded-full px-3 py-1 bg-zinc-900 border border-zinc-700 text-zinc-300">
              {hero?.region || "Unknown Region"}
            </Badge>

            <Badge className="rounded-full px-3 py-1 bg-zinc-900 border border-zinc-700 text-zinc-300">
              {hero?.city || "Unknown City"}
            </Badge>
          </div>
        </div>

        {/* Error banner */}
        {errorMsg && (
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-amber-300">
            {errorMsg}
          </div>
        )}

        {/* Anomaly Alert */}
        {anomalyRow && (
          <div className="rounded-3xl border border-red-500/20 bg-red-500/10 px-5 py-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-300 mt-0.5" />
                <div>
                  <div className="text-red-300 font-semibold text-sm uppercase tracking-wide">
                    Surge Anomaly Detected
                  </div>
                  <div className="text-white mt-1">
                    {anomalyRow.platform} is spiking in{" "}
                    <span className="font-semibold">{anomalyRow.region}</span>,{" "}
                    {anomalyRow.city} at{" "}
                    <span className="font-semibold">
                      {Number(anomalyRow.final_multiplier).toFixed(1)}x
                    </span>{" "}
                    (₹{Math.round(Number(anomalyRow.final_fee))})
                  </div>
                </div>
              </div>

              <Badge className="w-fit rounded-full px-4 py-1 bg-red-500/20 text-red-200 border border-red-500/30">
                Investigate pricing spike
              </Badge>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <MetricCard
            title="Current fare"
            value={`₹${Math.round(kpis.currentFare)}`}
            sub={`Base ₹${Math.round(hero?.base_fee || 35)}`}
            icon={TrendingUp}
          />
          <MetricCard
            title="Surge multiplier"
            value={`${Number(kpis.surge).toFixed(1)}x`}
            sub="Active surge"
            icon={Zap}
            accent="text-orange-400"
          />
          <MetricCard
            title="Active orders"
            value={kpis.activeOrders}
            sub="Estimated live demand"
            icon={Activity}
            accent="text-emerald-400"
          />
          <MetricCard
            title="D/S ratio"
            value={Number(kpis.dsRatio).toFixed(1)}
            sub="Demand / Supply"
            icon={Truck}
            accent="text-sky-400"
          />
        </div>

        {/* Signals + Surge Breakdown */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100 flex items-center gap-2">
                <Gauge className="w-5 h-5 text-amber-400" />
                Pricing Signals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {[
                {
                  label: "Demand (orders/min)",
                  value: Math.round((hero?.demand_supply_ratio || 0.7) * 32),
                  max: 40,
                },
                {
                  label: "Drivers online",
                  value: Math.max(
                    10,
                    40 - Math.round((hero?.demand_supply_ratio || 0.7) * 8)
                  ),
                  max: 40,
                },
                {
                  label: "Traffic index",
                  value: Math.round(((hero?.traffic_multiplier || 1.07) - 1) * 100),
                  max: 40,
                },
                {
                  label: "Rain intensity",
                  value: Math.round(((hero?.weather_multiplier || 1.04) - 1) * 100),
                  max: 40,
                },
                {
                  label: "Peak hour weight",
                  value: Math.round(((hero?.peak_multiplier || 1.12) - 1) * 100),
                  max: 40,
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="grid grid-cols-[170px_1fr_40px] gap-4 items-center"
                >
                  <span className="text-zinc-300 text-sm md:text-base">
                    {item.label}
                  </span>
                  <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-zinc-500 via-amber-400 to-yellow-300"
                      style={{
                        width: `${Math.min(100, (item.value / item.max) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-right text-zinc-100 font-semibold">
                    {item.value}
                  </span>
                </div>
              ))}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4">
                <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3">
                  <div className="text-zinc-400 text-xs">Active Platform</div>
                  <div className="mt-1 flex items-center gap-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        getPlatformAccent(hero?.platform).dot
                      }`}
                    />
                    <span className="text-white font-semibold">{hero?.platform}</span>
                  </div>
                </div>

                <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3">
                  <div className="text-zinc-400 text-xs">Live Zone</div>
                  <div className="mt-1 text-white font-semibold">{hero?.region}</div>
                </div>

                <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3">
                  <div className="text-zinc-400 text-xs">Signal State</div>
                  <div className="mt-1">
                    <Badge className="rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      {Number(hero?.final_multiplier || 1) >= 2 ? "High Surge" : "Stable"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardContent className="p-6">
              <div className="text-center mb-6">
                <div className="text-6xl font-extrabold text-white drop-shadow-sm">
                  {Number(hero?.final_multiplier || 1.5).toFixed(1)}x
                </div>
                <div className="text-zinc-400 mt-2">Surge multiplier</div>

                <div className="mt-5 h-3 bg-zinc-800 rounded-full overflow-hidden max-w-md mx-auto">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                    style={{
                      width: `${Math.min(
                        100,
                        ((hero?.final_multiplier || 1.5) / 3.0) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {factorCards.map((f) => (
                  <div
                    key={f.label}
                    className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-4 shadow-lg"
                  >
                    <div className="text-zinc-400 text-sm">{f.label}</div>
                    <div className="text-2xl font-bold mt-1 text-white">{f.value}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Heatmap + Region Pricing */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100 flex items-center gap-2">
                <Timer className="w-5 h-5 text-amber-400" />
                24H Pricing Activity Heatmap
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData}>
                    <CartesianGrid stroke="#27272a" vertical={false} />
                    <XAxis dataKey="hour" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" />
                    <Tooltip
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid #3f3f46",
                        borderRadius: 16,
                        color: "#ffffff",
                      }}
                    />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#f59e0b" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100 flex items-center gap-2">
                <MapPinned className="w-5 h-5 text-amber-400" />
                Region Pricing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-zinc-400 border-b border-zinc-800">
                      <th className="text-left py-3">Zone</th>
                      <th className="text-left py-3">D/S</th>
                      <th className="text-left py-3">Multiplier</th>
                      <th className="text-left py-3">Fare</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(filteredLatest.length ? filteredLatest : filteredByPlatform)
                      .slice(0, 6)
                      .map((row, idx) => (
                        <tr
                          key={`${row.region}-${idx}`}
                          className="border-b border-zinc-800/60"
                        >
                          <td className="py-3 font-semibold text-white">{row.region}</td>
                          <td className="py-3 text-zinc-300">
                            {Number(row.demand_supply_ratio).toFixed(1)}
                          </td>
                          <td className="py-3">
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-bold ${getMultiplierColor(
                                Number(row.final_multiplier)
                              )}`}
                            >
                              {Number(row.final_multiplier).toFixed(1)}x
                            </span>
                          </td>
                          <td className="py-3 font-bold text-white">
                            ₹{Math.round(Number(row.final_fee))}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Rolling Multiplier */}
        <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-zinc-100 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-amber-400" />
              Rolling Multiplier — Last 30 Ticks
            </CardTitle>
            <Badge className="bg-orange-100 text-orange-700 rounded-full px-4 py-1 font-semibold">
              {Number(hero?.final_multiplier || 1) >= 2 ? "Surging" : "Stable"}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid stroke="#27272a" vertical={false} />
                  <XAxis dataKey="tick" stroke="#a1a1aa" />
                  <YAxis stroke="#a1a1aa" domain={[0.8, "dataMax + 0.5"]} />
                  <Tooltip
                    contentStyle={{
                      background: "#18181b",
                      border: "1px solid #3f3f46",
                      borderRadius: 16,
                      color: "#ffffff",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="final_multiplier"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Surge Leaderboard + Platform Comparison */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100">Top Surge Leaderboard</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {topLeaderboard.map((row, idx) => (
                  <div
                    key={`${row.platform}-${row.region}-${idx}`}
                    className="rounded-3xl bg-zinc-900/80 border border-zinc-700/80 p-5 shadow-lg"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <Badge className="rounded-full px-3 py-1 bg-zinc-800 text-zinc-200 border border-zinc-700">
                        #{idx + 1}
                      </Badge>

                      <Badge
                        className={`${getMultiplierColor(
                          Number(row.final_multiplier)
                        )} rounded-full px-3 py-1`}
                      >
                        {Number(row.final_multiplier).toFixed(1)}x
                      </Badge>
                    </div>

                    <div className="space-y-1">
                      <div className="text-lg font-bold text-white">{row.platform}</div>
                      <div className="text-zinc-300">{row.region}</div>
                      <div className="text-zinc-500 text-sm">{row.city}</div>
                    </div>

                    <div className="mt-5 flex items-end justify-between">
                      <div>
                        <div className="text-zinc-400 text-xs">Current Fare</div>
                        <div className="text-3xl font-extrabold text-white">
                          ₹{Math.round(Number(row.final_fee))}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-zinc-400 text-xs">D/S Ratio</div>
                        <div className="text-white font-semibold">
                          {Number(row.demand_supply_ratio).toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-amber-400" />
                Platform Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={platformComparison}>
                    <CartesianGrid stroke="#27272a" vertical={false} />
                    <XAxis dataKey="platform" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" domain={[0, "dataMax + 0.8"]} />
                    <Tooltip
                      contentStyle={{
                        background: "#18181b",
                        border: "1px solid #3f3f46",
                        borderRadius: 16,
                        color: "#ffffff",
                      }}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {platformComparison.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-3 gap-3 mt-4">
                {platformComparison.map((p) => (
                  <div
                    key={p.platform}
                    className="rounded-2xl bg-zinc-900/80 border border-zinc-700 p-3"
                  >
                    <div className="text-zinc-400 text-xs">{p.platform}</div>
                    <div className="text-xl font-bold text-white mt-1">
                      {p.value > 0 ? `${p.value}x` : "--"}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Feed + System Pulse */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100">Live Surge Feed</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {liveFeedRows.length > 0 ? (
                liveFeedRows.map((row, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-2xl bg-zinc-900/80 border border-zinc-700 px-4 py-2.5 shadow-md"
                  >
                    <div>
                      <div className="font-semibold text-white">
                        {row.platform} • {row.region}
                      </div>
                      <div className="text-sm text-zinc-400">
                        {row.city} • Updated {new Date(row.calculated_at).toLocaleTimeString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge
                        className={`${getMultiplierColor(
                          Number(row.final_multiplier)
                        )} rounded-full px-3 py-1`}
                      >
                        {Number(row.final_multiplier).toFixed(1)}x
                      </Badge>
                      <div className="text-xl font-bold text-white">
                        ₹{Math.round(Number(row.final_fee))}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 text-zinc-400">
                  No live surge rows available for current filter.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-zinc-950/90 border-zinc-800 rounded-3xl shadow-2xl">
            <CardHeader>
              <CardTitle className="text-zinc-100">System Pulse</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">API Status</div>
                <div
                  className={`text-xl font-bold mt-1 ${
                    apiStatus === "live" ? "text-emerald-400" : "text-amber-400"
                  }`}
                >
                  {apiStatus === "live" ? "Connected" : "Fallback / Mock"}
                </div>
              </div>

              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">Average Fee</div>
                <div className="text-2xl font-bold mt-1 text-white">₹{kpis.avgFee}</div>
              </div>

              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">Max Multiplier</div>
                <div className="text-2xl font-bold mt-1 text-white">{kpis.maxMult}x</div>
              </div>

              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">Avg D/S Ratio</div>
                <div className="text-2xl font-bold mt-1 text-white">{kpis.avgRatio}</div>
              </div>

              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">Coverage</div>
                <div className="text-lg font-semibold text-white mt-1">
                  {summary?.region_count ?? 0} regions • {summary?.platform_count ?? 0} platforms
                </div>
              </div>

              <div className="rounded-2xl bg-zinc-900/90 border border-zinc-700/80 p-3.5 shadow-lg">
                <div className="text-zinc-400 text-sm">Weather Signal</div>
                <div className="flex items-center gap-2 mt-1">
                  <CloudRain className="w-5 h-5 text-sky-400" />
                  <span className="text-lg font-semibold text-white">
                    +{(((hero?.weather_multiplier || 1.04) - 1) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}