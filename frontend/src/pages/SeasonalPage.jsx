import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "../services/api";
import { PageHeader, Loading } from "../components/ui.jsx";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

const fmt = (n) => "$" + Number(n||0).toLocaleString("en-US",{maximumFractionDigits:0});

const ICONS = {
  christmas:"🎄",new_year:"🎆",new_year_eve:"🥂",st_patricks:"🍀",
  super_bowl:"🏈",july_4th:"🎇",thanksgiving:"🦃",halloween:"🎃",
  memorial_day:"🇺🇸",labor_day:"⚒️",cinco_de_mayo:"🌮",easter:"🐣",
};

const MONTH_NAMES = ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

export default function SeasonalPage() {
  const [selectedYear, setSelectedYear] = useState(2026);
  const [selectedSeason, setSelectedSeason] = useState(null);

  const { data: overview, isLoading } = useQuery({
    queryKey: ["seasons-overview", selectedYear],
    queryFn: () => analyticsAPI.seasonsOverview(selectedYear).then(r => r.data),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["seasonal-detail", selectedSeason, selectedYear],
    queryFn: () => analyticsAPI.seasonal(selectedSeason, selectedYear).then(r => r.data),
    enabled: !!selectedSeason,
  });

  const PctBadge = ({ v }) => {
    if (v === null || v === undefined) return <span style={{color:"#ccc",fontSize:12}}>No prior data</span>;
    const color = v > 0 ? "#639922" : v < 0 ? "#E24B4A" : "#888";
    const Icon = v > 0 ? TrendingUp : v < 0 ? TrendingDown : Minus;
    return (
      <span style={{color,fontWeight:700,fontSize:12,display:"flex",alignItems:"center",gap:3}}>
        <Icon size={12}/> {v > 0 ? "+" : ""}{v}% vs prior year
      </span>
    );
  };

  // Build YoY chart data from detail
  const chartData = detail?.years ? Object.values(detail.years).map(y => ({
    year: String(y.year), revenue: y.revenue, profit: y.profit
  })) : [];

  return (
    <div style={{flex:1,overflow:"auto"}}>
      <PageHeader title="Seasonal Analytics" subtitle="Holiday and event performance — year over year"/>

      <div style={{padding:"16px 24px"}}>
        {/* Year selector */}
        <div style={{display:"flex",gap:8,marginBottom:20}}>
          {[2026,2025,2024].map(y=>(
            <button key={y} onClick={()=>{setSelectedYear(y);setSelectedSeason(null);}}
              style={{padding:"6px 16px",borderRadius:8,border:"1px solid #ddd",cursor:"pointer",fontWeight:600,fontSize:13,
                background:selectedYear===y?"#111":"#fff",color:selectedYear===y?"#fff":"#666"}}>
              {y}
            </button>
          ))}
        </div>

        {isLoading ? <Loading/> : (
          <>
            {/* Season grid */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:12,marginBottom:24}}>
              {(overview||[]).map(s=>(
                <div key={s.key} onClick={()=>setSelectedSeason(s.key===selectedSeason?null:s.key)}
                  style={{background:"#fff",border:`2px solid ${selectedSeason===s.key?"#d4af37":"#ebebeb"}`,
                    borderRadius:12,padding:"14px 16px",cursor:"pointer",transition:"all 0.15s",
                    boxShadow:selectedSeason===s.key?"0 4px 16px rgba(212,175,55,0.2)":"none"}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                    <div>
                      <span style={{fontSize:20}}>{ICONS[s.key]||"📅"}</span>
                      <div style={{fontSize:13,fontWeight:700,color:"#111",marginTop:4}}>{s.label}</div>
                      <div style={{fontSize:11,color:"#aaa"}}>{MONTH_NAMES[s.month]} {s.day_start}–{s.day_end}</div>
                    </div>
                    {s.revenue > 0 && (
                      <span style={{background:"#f0fdf4",color:"#3B6D11",padding:"2px 8px",borderRadius:99,fontSize:11,fontWeight:600}}>
                        {fmt(s.revenue)}
                      </span>
                    )}
                  </div>
                  {s.revenue > 0 ? (
                    <PctBadge v={s.yoy_pct}/>
                  ) : (
                    <span style={{fontSize:11,color:"#ccc"}}>Not yet / no data</span>
                  )}
                </div>
              ))}
            </div>

            {/* Detail panel */}
            {selectedSeason && (
              <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"20px 24px"}}>
                {detailLoading ? <Loading/> : detail && (
                  <>
                    <div style={{fontSize:16,fontWeight:700,marginBottom:4}}>
                      {ICONS[selectedSeason]||"📅"} {detail.season} — Year-over-Year
                    </div>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:20}}>
                      {/* YoY Chart */}
                      <div>
                        <div style={{fontSize:12,color:"#888",marginBottom:10,fontWeight:600}}>REVENUE BY YEAR</div>
                        <ResponsiveContainer width="100%" height={200}>
                          <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5"/>
                            <XAxis dataKey="year" tick={{fontSize:12}}/>
                            <YAxis tick={{fontSize:11}} tickFormatter={v=>"$"+Math.round(v/1000)+"k"}/>
                            <Tooltip formatter={(v)=>["$"+Number(v).toLocaleString()]}/>
                            <Bar dataKey="revenue" fill="#d4af37" radius={[6,6,0,0]} name="Revenue"/>
                            <Bar dataKey="profit" fill="#639922" radius={[6,6,0,0]} name="Profit"/>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      {/* Stock recommendations */}
                      <div>
                        <div style={{fontSize:12,color:"#888",marginBottom:10,fontWeight:600}}>WHAT TO STOCK UP ON</div>
                        <div style={{display:"flex",flexDirection:"column",gap:8}}>
                          {(detail.recommended_stock||[]).map((r,i)=>(
                            <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",
                              padding:"8px 12px",background:"#fafafa",borderRadius:8,fontSize:13}}>
                              <span>{r.item}</span>
                              <span style={{padding:"2px 8px",borderRadius:99,fontSize:11,fontWeight:600,
                                background:r.priority==="High"?"#fef3c7":r.priority==="Medium"?"#e6f1fb":"#f0f0f0",
                                color:r.priority==="High"?"#92400e":r.priority==="Medium"?"#185FA5":"#666"}}>
                                {r.priority}
                              </span>
                            </div>
                          ))}
                          {(!detail.recommended_stock||detail.recommended_stock.length===0)&&(
                            <div style={{color:"#aaa",fontSize:12}}>No specific recommendations</div>
                          )}
                        </div>
                      </div>
                    </div>
                    {/* Year breakdown table */}
                    <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:12}}>
                      {Object.values(detail.years||{}).map(y=>(
                        <div key={y.year} style={{background:"#fafafa",borderRadius:8,padding:"12px 14px"}}>
                          <div style={{fontSize:12,color:"#888",marginBottom:4,fontWeight:600}}>{y.year}</div>
                          <div style={{fontSize:20,fontWeight:700,color:"#111"}}>{fmt(y.revenue)}</div>
                          <div style={{fontSize:12,color:"#639922"}}>Profit: {fmt(y.profit)}</div>
                          <div style={{fontSize:11,color:"#aaa"}}>{y.transactions} transactions</div>
                        </div>
                      ))}
                    </div>
                    {/* YoY summary */}
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginTop:12}}>
                      {detail.yoy_2025_vs_2024?.revenue_pct !== undefined && (
                        <div style={{background:"#f0fdf4",borderRadius:8,padding:"10px 14px",fontSize:13}}>
                          <div style={{color:"#888",fontSize:11,marginBottom:2}}>2025 vs 2024</div>
                          <PctBadge v={detail.yoy_2025_vs_2024.revenue_pct}/>
                        </div>
                      )}
                      {detail.yoy_2026_vs_2025?.revenue_pct !== undefined && (
                        <div style={{background:"#fef9e7",borderRadius:8,padding:"10px 14px",fontSize:13}}>
                          <div style={{color:"#888",fontSize:11,marginBottom:2}}>2026 vs 2025</div>
                          <PctBadge v={detail.yoy_2026_vs_2025.revenue_pct}/>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
