import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dealsAPI, productsAPI } from "../services/api";
import { PageHeader, Modal, Field, Btn, Badge, Loading, inputStyle, selectStyle } from "../components/ui.jsx";
import { RefreshCw, CheckCheck, Tag, Plus, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";

const CATEGORIES = ["Beer","Hard Liquor","Wine","Tobacco","Vapes","Cool Drinks","Snacks"];

const emptyDeal = {
  title:"", description:"", discount_pct:"", original_price:"", deal_price:"",
  product_name:"", category:"", valid_until:"", source:"manual",
};

export default function DealsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyDeal);
  const [filter, setFilter] = useState("all"); // all, unread, read

  const { data: deals, isLoading } = useQuery({
    queryKey: ["deals"],
    queryFn: () => dealsAPI.list().then(r => r.data),
    refetchInterval: 120000,
  });

  const readMut = useMutation({
    mutationFn: (id) => dealsAPI.markRead(id),
    onSuccess: () => { qc.invalidateQueries(["deals"]); qc.invalidateQueries(["deals-unread"]); },
  });

  const checkMut = useMutation({
    mutationFn: () => dealsAPI.checkNow(),
    onSuccess: () => { toast.success("Supplier check complete!"); qc.invalidateQueries(["deals"]); },
    onError: () => toast.error("Check failed"),
  });

  const sf = (k,v) => setForm(f=>({...f,[k]:v}));
  const unread = (deals||[]).filter(d=>!d.is_read).length;

  const filtered = (deals||[]).filter(d => {
    if (filter==="unread") return !d.is_read;
    if (filter==="read") return d.is_read;
    return true;
  });

  // Supplier deal summary stats
  const totalDeals = (deals||[]).length;
  const activeDeals = (deals||[]).filter(d=>d.is_read===false).length;
  const catBreakdown = {};
  (deals||[]).forEach(d=>{ if(d.category) catBreakdown[d.category]=(catBreakdown[d.category]||0)+1; });

  return (
    <div style={{flex:1,overflow:"auto"}}>
      <PageHeader title="Supplier Deals" subtitle={`${unread} unread · ${totalDeals} total`}
        actions={<>
          <Btn onClick={()=>checkMut.mutate()} disabled={checkMut.isPending}>
            <RefreshCw size={14}/> {checkMut.isPending?"Checking...":"Check Now"}
          </Btn>
          <Btn variant="ghost" onClick={()=>{(deals||[]).filter(d=>!d.is_read).forEach(d=>readMut.mutate(d.id));}}>
            <CheckCheck size={14}/> Mark all read
          </Btn>
          <Btn variant="gold" onClick={()=>{setForm(emptyDeal);setOpen(true);}}>
            <Plus size={14}/> Add Deal
          </Btn>
        </>}
      />

      <div style={{padding:"16px 24px"}}>
        {/* Stats */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:20}}>
          {[
            {label:"Unread Deals",value:unread,color:"#d4af37"},
            {label:"Total Deals",value:totalDeals,color:"#378ADD"},
            {label:"Hard Liquor",value:catBreakdown["Hard Liquor"]||0,color:"#d4af37"},
            {label:"Beer",value:catBreakdown["Beer"]||0,color:"#378ADD"},
          ].map(s=>(
            <div key={s.label} style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,
              padding:"14px 16px",borderTop:`3px solid ${s.color}`}}>
              <div style={{fontSize:11,color:"#888",marginBottom:4,textTransform:"uppercase",letterSpacing:"0.04em"}}>{s.label}</div>
              <div style={{fontSize:24,fontWeight:700,color:"#111"}}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* Filter tabs */}
        <div style={{display:"flex",gap:8,marginBottom:14}}>
          {["all","unread","read"].map(f=>(
            <button key={f} onClick={()=>setFilter(f)}
              style={{padding:"6px 16px",borderRadius:8,border:"1px solid #ddd",cursor:"pointer",
                fontSize:13,fontWeight:600,textTransform:"capitalize",
                background:filter===f?"#111":"#fff",color:filter===f?"#fff":"#666"}}>
              {f} {f==="unread"&&unread>0?`(${unread})`:""}
            </button>
          ))}
        </div>

        {isLoading ? <Loading/> : (
          <>
            {filtered.length === 0 ? (
              <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,padding:"60px 24px",
                textAlign:"center",color:"#aaa"}}>
                <Tag size={32} style={{marginBottom:12,opacity:0.3}}/>
                <div style={{fontSize:14,marginBottom:8}}>
                  {filter==="unread" ? "No unread deals" : "No deals yet"}
                </div>
                <div style={{fontSize:12,marginBottom:16}}>
                  Add your suppliers in the Suppliers page, then click "Check Now" to fetch deals.
                  Or add a deal manually.
                </div>
                <Btn variant="gold" onClick={()=>{setForm(emptyDeal);setOpen(true);}}>
                  <Plus size={14}/> Add Manual Deal
                </Btn>
              </div>
            ) : (
              <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(320px,1fr))",gap:14}}>
                {filtered.map(d=>(
                  <div key={d.id} style={{background:"#fff",
                    border:`1px solid ${d.is_read?"#ebebeb":"#d4af37"}`,
                    borderLeft:`4px solid ${d.is_read?"#ebebeb":"#d4af37"}`,
                    borderRadius:12,padding:"16px 18px"}}>
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                      <div style={{flex:1}}>
                        <div style={{fontSize:13,fontWeight:700,color:"#111",marginBottom:3}}>{d.title}</div>
                        {d.category&&<span style={{fontSize:11,color:"#888",background:"#f5f5f5",
                          padding:"2px 8px",borderRadius:99}}>{d.category}</span>}
                      </div>
                      {!d.is_read&&<span style={{width:8,height:8,borderRadius:"50%",background:"#d4af37",
                        flexShrink:0,marginTop:4}}/>}
                    </div>
                    {d.description&&<div style={{fontSize:12,color:"#666",marginBottom:10,lineHeight:1.5}}>{d.description}</div>}
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:8}}>
                      <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                        {d.discount_pct&&<span style={{background:"#fef3c7",color:"#92400e",padding:"3px 10px",
                          borderRadius:99,fontSize:12,fontWeight:700}}>{d.discount_pct}% OFF</span>}
                        {d.deal_price&&<span style={{background:"#f0fdf4",color:"#3B6D11",padding:"3px 10px",
                          borderRadius:99,fontSize:12,fontWeight:700}}>${d.deal_price}</span>}
                        <span style={{fontSize:11,color:"#bbb"}}>{d.source||"manual"}</span>
                      </div>
                      {!d.is_read&&(
                        <Btn size="sm" onClick={()=>readMut.mutate(d.id)}>Mark read</Btn>
                      )}
                    </div>
                    {d.valid_until&&(
                      <div style={{fontSize:11,color:"#aaa",marginTop:8}}>
                        Expires: {new Date(d.valid_until).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Breakthru & RNDC portal links */}
        <div style={{marginTop:24,background:"#fafafa",borderRadius:12,padding:"16px 20px",border:"1px solid #f0f0f0"}}>
          <div style={{fontSize:13,fontWeight:600,marginBottom:12,color:"#888"}}>SUPPLIER PORTALS</div>
          <div style={{display:"flex",gap:12,flexWrap:"wrap"}}>
            {[
              {name:"Breakthru Beverage",url:"https://www.breakthrubeverage.com",color:"#378ADD"},
              {name:"RNDC Maryland",url:"https://www.rndc-usa.com",color:"#d4af37"},
              {name:"McLane Company",url:"https://www.mclaneco.com",color:"#639922"},
            ].map(s=>(
              <a key={s.name} href={s.url} target="_blank" rel="noopener noreferrer"
                style={{display:"flex",alignItems:"center",gap:6,padding:"8px 14px",borderRadius:8,
                  background:"#fff",border:`1px solid ${s.color}33`,color:s.color,fontSize:13,
                  fontWeight:600,textDecoration:"none"}}>
                <ExternalLink size={13}/> {s.name}
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* Add deal modal */}
      <Modal open={open} onClose={()=>setOpen(false)} title="Add Supplier Deal" width={500}>
        <Field label="Deal Title *">
          <input style={inputStyle} value={form.title} onChange={e=>sf("title",e.target.value)} placeholder="e.g. Hennessy VS — 10% case discount"/>
        </Field>
        <Field label="Description">
          <textarea style={{...inputStyle,height:60}} value={form.description} onChange={e=>sf("description",e.target.value)}/>
        </Field>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
          <Field label="Category">
            <select style={selectStyle} value={form.category} onChange={e=>sf("category",e.target.value)}>
              <option value="">All categories</option>
              {CATEGORIES.map(c=><option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Product Name">
            <input style={inputStyle} value={form.product_name} onChange={e=>sf("product_name",e.target.value)} placeholder="Hennessy VS 750ml"/>
          </Field>
          <Field label="Discount %">
            <input style={inputStyle} type="number" value={form.discount_pct} onChange={e=>sf("discount_pct",e.target.value)} placeholder="10"/>
          </Field>
          <Field label="Deal Price ($)">
            <input style={inputStyle} type="number" value={form.deal_price} onChange={e=>sf("deal_price",e.target.value)} placeholder="54.99"/>
          </Field>
          <Field label="Valid Until">
            <input style={inputStyle} type="date" value={form.valid_until} onChange={e=>sf("valid_until",e.target.value)}/>
          </Field>
          <Field label="Source">
            <select style={selectStyle} value={form.source} onChange={e=>sf("source",e.target.value)}>
              <option value="manual">Manual</option>
              <option value="breakthru">Breakthru</option>
              <option value="rndc">RNDC</option>
              <option value="mclane">McLane</option>
            </select>
          </Field>
        </div>
        <div style={{display:"flex",gap:8,marginTop:14}}>
          <Btn variant="gold" onClick={async()=>{
            if(!form.title){toast.error("Title required");return;}
            try{
              const {default:api}=await import("../services/api");
              await api.post("/deals/manual",{...form,
                discount_pct:form.discount_pct?parseFloat(form.discount_pct):null,
                deal_price:form.deal_price?parseFloat(form.deal_price):null,
                valid_until:form.valid_until||null,
              });
              toast.success("Deal added!");qc.invalidateQueries(["deals"]);setOpen(false);
            }catch(e){toast.error("Failed to add deal");}
          }}>Add Deal</Btn>
          <Btn onClick={()=>setOpen(false)}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}
