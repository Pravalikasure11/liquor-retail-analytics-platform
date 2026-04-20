import { useQuery } from "@tanstack/react-query";
import { analyticsAPI, dealsAPI } from "../services/api";
import { KPICard, Card, Loading, Badge, PageHeader } from "../components/ui.jsx";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import {
  DollarSign, TrendingUp, Package, AlertTriangle,
  ShoppingCart, Tag, Beer, Cigarette, Wine
} from "lucide-react";

const CAT_COLORS = {
  "Hard Liquor":"#d4af37","Beer":"#378ADD","Tobacco":"#888780",
  "Vapes":"#534AB7","Cool Drinks":"#0F6E56","Snacks":"#BA7517","Wine":"#D4537E"
};
const fmt  = (n) => "$" + Number(n||0).toLocaleString("en-US",{maximumFractionDigits:0});
const fmtK = (n) => n>=1000 ? "$"+(n/1000).toFixed(1)+"k" : "$"+Math.round(n||0);

export default function DashboardPage() {
  const { data: kpis, isLoading } = useQuery({
    queryKey:["dashboard"], queryFn:()=>analyticsAPI.dashboard().then(r=>r.data), refetchInterval:30000
  });
  const { data: dailyData } = useQuery({
    queryKey:["daily",30], queryFn:()=>analyticsAPI.daily(30).then(r=>r.data)
  });
  const { data: topProds } = useQuery({
    queryKey:["top-products"], queryFn:()=>analyticsAPI.topProducts({limit:10,period_days:30}).then(r=>r.data)
  });
  const { data: deals } = useQuery({
    queryKey:["deals-unread"], queryFn:()=>dealsAPI.unreadCount().then(r=>r.data)
  });
  const { data: historical } = useQuery({
    queryKey:["historical"], queryFn:()=>analyticsAPI.historicalSummary().then(r=>r.data)
  });

  if (isLoading) return <Loading />;

  const catData = (kpis?.category_breakdown || []).filter(c=>c.revenue>0);
  const yearlyHist = kpis?.yearly_historical || [];

  // Monthly historical for YoY chart
  const monthly2025 = (historical||[]).filter(h=>h.period_type==="month"&&h.year===2025);
  const monthly2026 = (historical||[]).filter(h=>h.period_type==="month"&&h.year===2026);
  const months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const yoyData = Array.from({length:12},(_,i)=>{
    const m=i+1;
    const y25=monthly2025.find(h=>h.month===m);
    const y26=monthly2026.find(h=>h.month===m);
    return {month:months[m],"2025":Math.round(y25?.revenue||0),"2026":Math.round(y26?.revenue||0)};
  }).filter(d=>d["2025"]>0||d["2026"]>0);

  return (
    <div style={{flex:1,overflow:"auto"}}>
      <PageHeader title="Zach's Liquor Store" subtitle={`Dashboard · ${new Date().toLocaleDateString("en-US",{weekday:"long",month:"long",day:"numeric"})}`}
        actions={deals?.count>0&&(
          <div style={{background:"#fef3c7",border:"1px solid #fde68a",borderRadius:8,padding:"6px 12px",fontSize:12,color:"#92400e",display:"flex",alignItems:"center",gap:6}}>
            <Tag size={13}/> {deals.count} new supplier deals
          </div>
        )}
      />
      <div style={{padding:"20px 24px"}}>

        {/* KPI Row */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14,marginBottom:20}}>
          <KPICard label="Today's Revenue" value={fmt(kpis?.today_revenue)} icon={DollarSign} color="#d4af37"
            sub={`Month to date: ${fmt(kpis?.month_revenue)}`}/>
          <KPICard label="Month Gross Profit" value={fmt(kpis?.month_profit)} icon={TrendingUp} color="#639922"
            sub={`Margin: ${kpis?.profit_margin_pct}%`}/>
          <KPICard label="Month Net (after expenses)" value={fmt(kpis?.month_net)} icon={ShoppingCart}
            color={kpis?.month_net>=0?"#378ADD":"#E24B4A"}
            sub={`Expenses: ${fmt(kpis?.month_expenses)}`}/>
          <KPICard label="Stock Alerts" value={(kpis?.low_stock_count||0)+(kpis?.out_of_stock_count||0)}
            icon={AlertTriangle} color="#E24B4A"
            sub={`${kpis?.out_of_stock_count} out · ${kpis?.low_stock_count} low`}/>
        </div>

        {/* Secondary KPIs */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14,marginBottom:20}}>
          <KPICard label="Total Products" value={kpis?.total_products} icon={Package} color="#534AB7" sub="active in inventory"/>
          <KPICard label="Inventory (cost)" value={fmtK(kpis?.inventory_cost_value)} icon={Package} color="#0F6E56" sub="current stock value"/>
          <KPICard label="Inventory (retail)" value={fmtK(kpis?.inventory_retail_value)} icon={Package} color="#BA7517" sub="at sell price"/>
          <KPICard label="Total Sales (all time)" value={Number(kpis?.total_sales_count||0).toLocaleString()} icon={ShoppingCart} color="#185FA5" sub={`${fmt(kpis?.total_revenue)} revenue`}/>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"2fr 1fr",gap:16,marginBottom:16}}>
          {/* Revenue chart */}
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"18px 20px"}}>
            <div style={{fontSize:13,fontWeight:600,marginBottom:14}}>Daily Revenue — Last 30 Days</div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={dailyData||[]} margin={{top:0,right:0,left:-20,bottom:0}}>
                <defs><linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d4af37" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#d4af37" stopOpacity={0}/>
                </linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5"/>
                <XAxis dataKey="date" tick={{fontSize:10}} tickFormatter={d=>d?.slice(5)}/>
                <YAxis tick={{fontSize:10}} tickFormatter={v=>"$"+Math.round(v/1000)+"k"}/>
                <Tooltip formatter={(v)=>["$"+Number(v).toLocaleString(),"Revenue"]}/>
                <Area type="monotone" dataKey="revenue" stroke="#d4af37" fill="url(#rev)" strokeWidth={2}/>
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category pie */}
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"18px 20px"}}>
            <div style={{fontSize:13,fontWeight:600,marginBottom:8}}>Sales Mix This Month</div>
            {catData.length>0 ? (
              <>
                <ResponsiveContainer width="100%" height={120}>
                  <PieChart>
                    <Pie data={catData} dataKey="revenue" cx="50%" cy="50%" outerRadius={55} innerRadius={30}>
                      {catData.map((entry,i)=>(
                        <Cell key={i} fill={CAT_COLORS[entry.category]||"#aaa"}/>
                      ))}
                    </Pie>
                    <Tooltip formatter={(v)=>["$"+Number(v).toLocaleString(),"Revenue"]}/>
                  </PieChart>
                </ResponsiveContainer>
                <div style={{display:"flex",flexDirection:"column",gap:4,marginTop:4}}>
                  {catData.slice(0,5).map(c=>(
                    <div key={c.category} style={{display:"flex",justifyContent:"space-between",fontSize:11}}>
                      <span style={{display:"flex",alignItems:"center",gap:5}}>
                        <span style={{width:8,height:8,borderRadius:"50%",background:CAT_COLORS[c.category]||"#aaa",display:"inline-block"}}/>
                        {c.category}
                      </span>
                      <span style={{color:"#888"}}>{fmt(c.revenue)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : <div style={{color:"#aaa",fontSize:12,paddingTop:20,textAlign:"center"}}>No sales data yet</div>}
          </div>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
          {/* YoY comparison */}
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"18px 20px"}}>
            <div style={{fontSize:13,fontWeight:600,marginBottom:14}}>2025 vs 2026 — Month by Month</div>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={yoyData} margin={{top:0,right:0,left:-20,bottom:0}}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5"/>
                <XAxis dataKey="month" tick={{fontSize:10}}/>
                <YAxis tick={{fontSize:10}} tickFormatter={v=>"$"+Math.round(v/1000)+"k"}/>
                <Tooltip formatter={(v,n)=>["$"+Number(v).toLocaleString(),n]}/>
                <Legend wrapperStyle={{fontSize:11}}/>
                <Bar dataKey="2025" fill="#e0e0e0" radius={[4,4,0,0]}/>
                <Bar dataKey="2026" fill="#d4af37" radius={[4,4,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top products */}
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"18px 20px"}}>
            <div style={{fontSize:13,fontWeight:600,marginBottom:12}}>Top 10 Products — Last 30 Days</div>
            <div style={{display:"flex",flexDirection:"column",gap:6,maxHeight:180,overflowY:"auto"}}>
              {(topProds||[]).map((p,i)=>(
                <div key={p.id} style={{display:"flex",alignItems:"center",gap:8,fontSize:12}}>
                  <span style={{width:18,height:18,borderRadius:"50%",background:i<3?"#d4af37":"#f0f0f0",
                    color:i<3?"#111":"#666",display:"flex",alignItems:"center",justifyContent:"center",
                    fontSize:10,fontWeight:700,flexShrink:0}}>{i+1}</span>
                  <span style={{flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{p.name}</span>
                  <span style={{color:"#888",flexShrink:0}}>{p.units} units</span>
                  <span style={{fontWeight:600,color:"#639922",flexShrink:0}}>{fmt(p.revenue)}</span>
                </div>
              ))}
              {(!topProds||topProds.length===0)&&<div style={{color:"#aaa",fontSize:12,padding:"20px 0",textAlign:"center"}}>No sales data yet — record a sale to see top products</div>}
            </div>
          </div>
        </div>

        {/* Historical yearly */}
        {yearlyHist.length>0&&(
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"18px 20px"}}>
            <div style={{fontSize:13,fontWeight:600,marginBottom:14}}>Annual Revenue — Store History (from Aenasys POS)</div>
            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(160px,1fr))",gap:12}}>
              {yearlyHist.map(y=>(
                <div key={y.year} style={{background:"#fafafa",borderRadius:8,padding:"12px 14px",border:"1px solid #f0f0f0"}}>
                  <div style={{fontSize:12,color:"#888",marginBottom:4}}>{y.year}</div>
                  <div style={{fontSize:20,fontWeight:700,color:"#111"}}>{fmtK(y.revenue)}</div>
                </div>
              ))}
              <div style={{background:"#fef9e7",borderRadius:8,padding:"12px 14px",border:"1px solid #fde68a"}}>
                <div style={{fontSize:12,color:"#92400e",marginBottom:4}}>2026 YTD (Jan–Apr)</div>
                <div style={{fontSize:20,fontWeight:700,color:"#92400e"}}>{fmtK(637214)}</div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
