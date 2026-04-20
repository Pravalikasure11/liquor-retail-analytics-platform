import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "../services/api";
import { PageHeader, Card, Badge, Loading } from "../components/ui.jsx";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const fmt = (n) => "$" + Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
const fmtK = (n) => n >= 1000 ? "$" + (n / 1000).toFixed(1) + "k" : "$" + n;

export default function AnalyticsPage() {
  const [view, setView] = useState("monthly");
  const [dailyDays, setDailyDays] = useState(30);

  const { data: daily }   = useQuery({ queryKey: ["daily", dailyDays], queryFn: () => analyticsAPI.daily(dailyDays).then(r => r.data), enabled: view === "daily" });
  const { data: monthly } = useQuery({ queryKey: ["monthly"], queryFn: () => analyticsAPI.monthly().then(r => r.data), enabled: view === "monthly" });
  const { data: yearly }  = useQuery({ queryKey: ["yearly"],  queryFn: () => analyticsAPI.yearly().then(r => r.data), enabled: view === "yearly" });
  const { data: pl }      = useQuery({ queryKey: ["pl"],      queryFn: () => analyticsAPI.plSummary().then(r => r.data), enabled: view === "pl" });
  const { data: topP }    = useQuery({ queryKey: ["top-p"],   queryFn: () => analyticsAPI.topProducts({ limit: 10, period_days: 90 }).then(r => r.data) });
  const { data: botP }    = useQuery({ queryKey: ["bot-p"],   queryFn: () => analyticsAPI.bottomProducts({ limit: 10 }).then(r => r.data) });

  const tabs = [
    { key: "daily",   label: "Daily" },
    { key: "monthly", label: "Monthly" },
    { key: "yearly",  label: "Yearly" },
    { key: "pl",      label: "P&L Statement" },
  ];

  const tabBtn = (k, label) => (
    <button key={k} onClick={() => setView(k)} style={{
      padding: "7px 16px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 13,
      background: view === k ? "#111" : "transparent",
      color: view === k ? "#fff" : "#888", fontWeight: view === k ? 600 : 400,
    }}>{label}</button>
  );

  const chartData = view === "daily" ? daily : view === "monthly" ? monthly : view === "yearly" ? yearly?.map(y => ({ ...y, month: String(y.year) })) : pl;
  const xKey = view === "daily" ? "day" : view === "yearly" ? "year" : "month";
  const xFmt = view === "daily" ? (v => v?.slice(5)) : (v => view === "yearly" ? v : v?.slice(5));

  return (
    <div style={{ flex: 1, overflow: "auto" }}>
      <PageHeader title="Sales Analytics" subtitle="Power BI-style deep analytics" />

      <div style={{ padding: "16px 24px" }}>
        {/* Tab switcher */}
        <div style={{ display: "flex", gap: 4, background: "#f5f5f3", borderRadius: 10, padding: 4, marginBottom: 20, width: "fit-content" }}>
          {tabs.map(t => tabBtn(t.key, t.label))}
        </div>

        {view !== "pl" ? (
          <>
            {view === "daily" && (
              <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                {[7, 14, 30, 60, 90].map(d => (
                  <button key={d} onClick={() => setDailyDays(d)} style={{
                    padding: "4px 12px", borderRadius: 6, border: "1px solid #e0e0e0", cursor: "pointer",
                    background: dailyDays === d ? "#111" : "#fff", color: dailyDays === d ? "#fff" : "#888", fontSize: 12,
                  }}>{d}d</button>
                ))}
              </div>
            )}

            {/* Main chart */}
            <Card title={`${view.charAt(0).toUpperCase() + view.slice(1)} Revenue & Profit`} style={{ marginBottom: 16 }}>
              <div style={{ padding: "0 16px 16px" }}>
                {!chartData ? <Loading /> : (
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="revG" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#378ADD" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#378ADD" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="profG" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#639922" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#639922" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey={xKey} tick={{ fontSize: 10 }} tickLine={false} tickFormatter={xFmt} interval={view === "daily" ? Math.floor((chartData?.length || 1) / 6) : 0} />
                      <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={fmtK} />
                      <Tooltip formatter={(v, n) => [fmt(v), n]} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#378ADD" strokeWidth={2} fill="url(#revG)" dot={false} />
                      <Area type="monotone" dataKey="profit" name="Profit" stroke="#639922" strokeWidth={2} fill="url(#profG)" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Card>

            {/* Units sold */}
            <Card title="Units Sold" style={{ marginBottom: 16 }}>
              <div style={{ padding: "0 16px 16px" }}>
                {!chartData ? <Loading /> : (
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey={xKey} tick={{ fontSize: 10 }} tickLine={false} tickFormatter={xFmt} interval={view === "daily" ? Math.floor((chartData?.length || 1) / 6) : 0} />
                      <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                      <Tooltip />
                      <Bar dataKey="units" name="Units Sold" fill="#BA7517" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Card>
          </>
        ) : (
          /* P&L Statement */
          <Card title="Profit & Loss Statement">
            {!pl ? <Loading /> : (
              <div style={{ padding: "0 18px 18px" }}>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={pl} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 10 }} tickLine={false} tickFormatter={v => v?.slice(5)} />
                    <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={fmtK} />
                    <Tooltip formatter={(v) => [fmt(v)]} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="revenue" name="Revenue" fill="#378ADD" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="gross_profit" name="Gross Profit" fill="#639922" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="expenses" name="Expenses" fill="#E24B4A" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="net_profit" name="Net Profit" fill="#d4af37" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>

                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 16 }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                      {["Month","Revenue","COGS","Gross Profit","Expenses","Net Profit","Net Margin"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 11, color: "#888", fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pl.map(row => {
                      const netMargin = row.revenue > 0 ? Math.round(row.net_profit / row.revenue * 100) : 0;
                      return (
                        <tr key={row.month} style={{ borderBottom: "1px solid #f8f8f8" }}>
                          <td style={{ padding: "10px 12px", fontWeight: 500 }}>{row.month}</td>
                          <td style={{ padding: "10px 12px" }}>{fmt(row.revenue)}</td>
                          <td style={{ padding: "10px 12px", color: "#E24B4A" }}>{fmt(row.cogs)}</td>
                          <td style={{ padding: "10px 12px", color: "#639922" }}>{fmt(row.gross_profit)}</td>
                          <td style={{ padding: "10px 12px", color: "#E24B4A" }}>{fmt(row.expenses)}</td>
                          <td style={{ padding: "10px 12px", fontWeight: 700, color: row.net_profit >= 0 ? "#639922" : "#E24B4A" }}>{fmt(row.net_profit)}</td>
                          <td style={{ padding: "10px 12px" }}>
                            <Badge color={netMargin > 20 ? "green" : netMargin > 10 ? "amber" : "red"}>{netMargin}%</Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {/* Best & Worst sellers */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          <Card title="Best Sellers (90 days)">
            <div style={{ padding: "4px 0 8px" }}>
              {(topP || []).map((p, i) => {
                const max = topP?.[0]?.profit || 1;
                const pct = Math.round(p.profit / max * 100);
                return (
                  <div key={p.product_id} style={{ padding: "8px 18px", borderBottom: i < topP.length - 1 ? "1px solid #f8f8f8" : "none" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 13 }}><span style={{ color: "#aaa", fontSize: 11, marginRight: 5 }}>#{i+1}</span>{p.name}</span>
                      <span style={{ color: "#639922", fontWeight: 700, fontSize: 13 }}>{fmt(p.profit)}</span>
                    </div>
                    <div style={{ height: 4, background: "#f0f0f0", borderRadius: 99 }}>
                      <div style={{ width: `${pct}%`, height: "100%", background: "#639922", borderRadius: 99 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card title="Slowest Movers (90 days)">
            <div style={{ padding: "4px 0 8px" }}>
              {(botP || []).map((p, i) => (
                <div key={p.product_id} style={{ padding: "8px 18px", borderBottom: i < botP.length - 1 ? "1px solid #f8f8f8" : "none", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{p.name}</div>
                    <div style={{ fontSize: 11, color: "#aaa" }}>{p.category}</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ color: "#E24B4A", fontWeight: 700 }}>{p.units} units</div>
                    <div style={{ fontSize: 11, color: "#aaa" }}>{fmt(p.revenue)}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
