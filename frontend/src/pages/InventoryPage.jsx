import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { productsAPI } from "../services/api";
import { PageHeader, Modal, Field, Btn, Badge, Loading, Empty, inputStyle, selectStyle, StockBar } from "../components/ui.jsx";
import { Plus, Edit2, Trash2, Search, Filter, Download } from "lucide-react";

const CATEGORIES = ["Beer","Hard Liquor","Wine","Tobacco","Vapes","Cool Drinks","Snacks"];
const SIZE_BUCKETS = ["Mini Shot","200 ml","Pint","Fifth","Liter","Half Gallon","Single Can","6-pack","12-pack","24-pack / Case","Pack","Carton","Bottle","Unit"];
const PRICE_TIERS = ["Budget","Value","Mid-range","Premium","Luxury"];
const DEMAND_BANDS = ["Low","Medium","High"];

const CAT_COLORS = {
  "Hard Liquor":"#d4af37","Beer":"#378ADD","Tobacco":"#888780",
  "Vapes":"#534AB7","Cool Drinks":"#0F6E56","Snacks":"#BA7517","Wine":"#D4537E"
};

const emptyForm = {
  name:"",brand_family:"",category:"Beer",subcategory:"",product_line:"",
  size_label:"",size_bucket:"",price_tier:"Value",demand_band:"Low",
  cost_price:"",sell_price:"",stock:"",reorder_point:"5",reorder_qty:"12",
  supplier_name:"",description:"",is_active:true
};

export default function InventoryPage() {
  const qc = useQueryClient();
  const [open,setOpen]=useState(false);
  const [editing,setEditing]=useState(null);
  const [form,setForm]=useState(emptyForm);
  const [search,setSearch]=useState("");
  const [catFilter,setCatFilter]=useState("");
  const [sizeFilter,setSizeFilter]=useState("");
  const [lowStockOnly,setLowStockOnly]=useState(false);
  const [view,setView]=useState("table"); // table | cards

  const { data:products,isLoading } = useQuery({
    queryKey:["products",search,catFilter,sizeFilter,lowStockOnly],
    queryFn:()=>productsAPI.list({
      search:search||undefined,category:catFilter||undefined,
      size_bucket:sizeFilter||undefined,low_stock:lowStockOnly||undefined
    }).then(r=>r.data)
  });

  const { data:categories } = useQuery({
    queryKey:["product-categories"],
    queryFn:()=>productsAPI.categories().then(r=>r.data)
  });

  const createMut = useMutation({
    mutationFn:d=>productsAPI.create(d),
    onSuccess:()=>{ qc.invalidateQueries(["products"]); toast.success("Product added!"); setOpen(false); setForm(emptyForm); },
    onError:e=>toast.error(e.response?.data?.detail||"Failed")
  });
  const updateMut = useMutation({
    mutationFn:({id,data})=>productsAPI.update(id,data),
    onSuccess:()=>{ qc.invalidateQueries(["products"]); toast.success("Updated!"); setOpen(false); setEditing(null); },
    onError:e=>toast.error(e.response?.data?.detail||"Failed")
  });
  const deleteMut = useMutation({
    mutationFn:id=>productsAPI.delete(id),
    onSuccess:()=>{ qc.invalidateQueries(["products"]); toast.success("Removed"); }
  });

  const sf=(k,v)=>setForm(f=>({...f,[k]:v}));
  const openAdd=()=>{ setForm(emptyForm); setEditing(null); setOpen(true); };
  const openEdit=p=>{ setForm({...p,cost_price:String(p.cost_price),sell_price:String(p.sell_price),stock:String(p.stock),reorder_point:String(p.reorder_point),reorder_qty:String(p.reorder_qty)}); setEditing(p); setOpen(true); };

  const save=()=>{
    if(!form.name){ toast.error("Name required"); return; }
    const data={...form,cost_price:parseFloat(form.cost_price)||0,sell_price:parseFloat(form.sell_price)||0,
      stock:parseInt(form.stock)||0,reorder_point:parseInt(form.reorder_point)||5,reorder_qty:parseInt(form.reorder_qty)||12};
    if(editing) updateMut.mutate({id:editing.id,data});
    else createMut.mutate(data);
  };

  const exportCSV=()=>{
    if(!products) return;
    const headers=["Name","Brand","Category","Subcategory","Size","Price Tier","Cost","Sell Price","Margin%","Stock","Reorder Point","Supplier"];
    const rows=products.map(p=>[p.name,p.brand_family,p.category,p.subcategory,p.size_bucket,p.price_tier,p.cost_price,p.sell_price,p.margin_pct,p.stock,p.reorder_point,p.supplier_name]);
    const csv=[headers,...rows].map(r=>r.join(",")).join("\n");
    const a=document.createElement("a"); a.href="data:text/csv;charset=utf-8,"+encodeURIComponent(csv);
    a.download="zachs-inventory.csv"; a.click();
  };

  const margin=(p)=>p.sell_price?Math.round((p.sell_price-p.cost_price)/p.sell_price*100):0;

  return (
    <div style={{flex:1,overflow:"auto"}}>
      <PageHeader title="Inventory" subtitle={`${products?.length||0} products`} actions={
        <div style={{display:"flex",gap:8}}>
          <Btn onClick={exportCSV}><Download size={14}/> Export</Btn>
          <Btn variant="gold" onClick={openAdd}><Plus size={14}/> Add Product</Btn>
        </div>
      }/>
      <div style={{padding:"16px 24px"}}>

        {/* Filters */}
        <div style={{display:"flex",gap:8,marginBottom:14,flexWrap:"wrap",alignItems:"center"}}>
          <div style={{position:"relative"}}>
            <Search size={13} style={{position:"absolute",left:9,top:"50%",transform:"translateY(-50%)",color:"#aaa"}}/>
            <input style={{...inputStyle,paddingLeft:30,width:240}} placeholder="Search products, brands, SKU..." value={search} onChange={e=>setSearch(e.target.value)}/>
          </div>
          <select style={{...selectStyle,width:140}} value={catFilter} onChange={e=>setCatFilter(e.target.value)}>
            <option value="">All Categories</option>
            {CATEGORIES.map(c=><option key={c} value={c}>{c} {categories?.find(x=>x.category===c) ? `(${categories.find(x=>x.category===c).count})`:""}</option>)}
          </select>
          <select style={{...selectStyle,width:130}} value={sizeFilter} onChange={e=>setSizeFilter(e.target.value)}>
            <option value="">All Sizes</option>
            {SIZE_BUCKETS.map(s=><option key={s} value={s}>{s}</option>)}
          </select>
          <label style={{display:"flex",alignItems:"center",gap:6,fontSize:13,cursor:"pointer"}}>
            <input type="checkbox" checked={lowStockOnly} onChange={e=>setLowStockOnly(e.target.checked)}/>
            Low stock only
          </label>
        </div>

        {/* Category quick filters */}
        <div style={{display:"flex",gap:6,marginBottom:14,flexWrap:"wrap"}}>
          <button onClick={()=>setCatFilter("")}
            style={{padding:"4px 12px",borderRadius:99,border:"1px solid #ddd",fontSize:12,cursor:"pointer",
              background:catFilter===""?"#111":"#fff",color:catFilter===""?"#fff":"#666"}}>
            All
          </button>
          {CATEGORIES.map(c=>(
            <button key={c} onClick={()=>setCatFilter(c===catFilter?"":c)}
              style={{padding:"4px 12px",borderRadius:99,border:`1px solid ${catFilter===c?(CAT_COLORS[c]||"#ddd"):"#ddd"}`,fontSize:12,cursor:"pointer",
                background:catFilter===c?(CAT_COLORS[c]||"#111"):"#fff",
                color:catFilter===c?"#fff":"#666"}}>
              {c}
            </button>
          ))}
        </div>

        {isLoading ? <Loading/> : (
          <div style={{background:"#fff",border:"1px solid #ebebeb",borderRadius:12,overflow:"hidden"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
              <thead>
                <tr style={{background:"#fafafa",borderBottom:"1px solid #f0f0f0"}}>
                  {["Product","Category / Size","Price Tier","Cost","Sell","Margin","Stock","Actions"].map(h=>(
                    <th key={h} style={{padding:"10px 14px",textAlign:"left",fontSize:11,fontWeight:600,color:"#888",textTransform:"uppercase",letterSpacing:"0.04em",whiteSpace:"nowrap"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(products||[]).length===0&&(
                  <tr><td colSpan={8} style={{padding:"40px",textAlign:"center",color:"#aaa"}}>
                    No products found. Add your first product or run the import script.
                  </td></tr>
                )}
                {(products||[]).map(p=>(
                  <tr key={p.id} style={{borderBottom:"1px solid #f8f8f8"}}
                    onMouseEnter={e=>e.currentTarget.style.background="#fafafa"}
                    onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                    <td style={{padding:"10px 14px"}}>
                      <div style={{fontWeight:600,fontSize:13}}>{p.name}</div>
                      {p.brand_family&&<div style={{fontSize:11,color:"#aaa"}}>{p.brand_family}</div>}
                      {p.sku&&<div style={{fontSize:10,color:"#ccc"}}>{p.sku}</div>}
                    </td>
                    <td style={{padding:"10px 14px"}}>
                      <div style={{display:"flex",flexDirection:"column",gap:3}}>
                        <span style={{display:"inline-block",padding:"2px 8px",borderRadius:99,fontSize:10,fontWeight:600,
                          background:(CAT_COLORS[p.category]||"#888")+"22",color:CAT_COLORS[p.category]||"#888"}}>
                          {p.category}
                        </span>
                        {p.size_bucket&&<span style={{fontSize:11,color:"#888"}}>{p.size_bucket}</span>}
                        {p.subcategory&&<span style={{fontSize:10,color:"#bbb"}}>{p.subcategory}</span>}
                      </div>
                    </td>
                    <td style={{padding:"10px 14px"}}>
                      <span style={{fontSize:11,color:"#888"}}>{p.price_tier||"—"}</span>
                    </td>
                    <td style={{padding:"10px 14px",fontVariantNumeric:"tabular-nums"}}>${p.cost_price?.toFixed(2)}</td>
                    <td style={{padding:"10px 14px",fontWeight:600,fontVariantNumeric:"tabular-nums"}}>${p.sell_price?.toFixed(2)}</td>
                    <td style={{padding:"10px 14px"}}>
                      <span style={{color:margin(p)>35?"#639922":margin(p)>20?"#BA7517":"#E24B4A",fontWeight:600,fontSize:12}}>
                        {margin(p)}%
                      </span>
                    </td>
                    <td style={{padding:"10px 14px"}}><StockBar stock={p.stock} reorderPoint={p.reorder_point}/></td>
                    <td style={{padding:"10px 14px"}}>
                      <div style={{display:"flex",gap:4}}>
                        <Btn size="sm" onClick={()=>openEdit(p)}><Edit2 size={11}/></Btn>
                        <Btn size="sm" variant="danger" onClick={()=>{ if(confirm(`Remove ${p.name}?`)) deleteMut.mutate(p.id); }}>
                          <Trash2 size={11}/>
                        </Btn>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={open} onClose={()=>{setOpen(false);setEditing(null);}} title={editing?"Edit Product":"Add Product"} width={560}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
          <Field label="Product Name *" style={{gridColumn:"1/-1"}}>
            <input style={inputStyle} value={form.name} onChange={e=>sf("name",e.target.value)} placeholder="e.g. Don Julio Blanco 750ml"/>
          </Field>
          <Field label="Brand Family">
            <input style={inputStyle} value={form.brand_family||""} onChange={e=>sf("brand_family",e.target.value)} placeholder="Don Julio"/>
          </Field>
          <Field label="Category">
            <select style={selectStyle} value={form.category} onChange={e=>sf("category",e.target.value)}>
              {CATEGORIES.map(c=><option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Subcategory">
            <input style={inputStyle} value={form.subcategory||""} onChange={e=>sf("subcategory",e.target.value)} placeholder="Tequila, Vodka, Whiskey..."/>
          </Field>
          <Field label="Product Line">
            <input style={inputStyle} value={form.product_line||""} onChange={e=>sf("product_line",e.target.value)} placeholder="Blanco, Reposado, Core..."/>
          </Field>
          <Field label="Size Label">
            <input style={inputStyle} value={form.size_label||""} onChange={e=>sf("size_label",e.target.value)} placeholder="750ml, 12-pack, 50ml..."/>
          </Field>
          <Field label="Size Bucket">
            <select style={selectStyle} value={form.size_bucket||""} onChange={e=>sf("size_bucket",e.target.value)}>
              <option value="">Select size</option>
              {SIZE_BUCKETS.map(s=><option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Price Tier">
            <select style={selectStyle} value={form.price_tier||"Value"} onChange={e=>sf("price_tier",e.target.value)}>
              {PRICE_TIERS.map(t=><option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Demand">
            <select style={selectStyle} value={form.demand_band||"Low"} onChange={e=>sf("demand_band",e.target.value)}>
              {DEMAND_BANDS.map(d=><option key={d} value={d}>{d}</option>)}
            </select>
          </Field>
          <Field label="Cost Price ($)">
            <input style={inputStyle} type="number" step="0.01" value={form.cost_price} onChange={e=>sf("cost_price",e.target.value)} placeholder="0.00"/>
          </Field>
          <Field label="Sell Price ($)">
            <input style={inputStyle} type="number" step="0.01" value={form.sell_price} onChange={e=>sf("sell_price",e.target.value)} placeholder="0.00"/>
          </Field>
          {form.sell_price&&form.cost_price&&(
            <div style={{gridColumn:"1/-1",background:"#f0fdf4",borderRadius:8,padding:"8px 12px",fontSize:12,color:"#3B6D11"}}>
              Margin: {Math.round((parseFloat(form.sell_price)-parseFloat(form.cost_price))/parseFloat(form.sell_price)*100)}%
            </div>
          )}
          <Field label="Current Stock">
            <input style={inputStyle} type="number" value={form.stock} onChange={e=>sf("stock",e.target.value)} placeholder="0"/>
          </Field>
          <Field label="Reorder Point">
            <input style={inputStyle} type="number" value={form.reorder_point} onChange={e=>sf("reorder_point",e.target.value)} placeholder="5"/>
          </Field>
          <Field label="Supplier">
            <input style={inputStyle} value={form.supplier_name||""} onChange={e=>sf("supplier_name",e.target.value)} placeholder="Breakthru, RNDC..."/>
          </Field>
          <Field label="Description / Notes">
            <textarea style={{...inputStyle,height:50,resize:"vertical"}} value={form.description||""} onChange={e=>sf("description",e.target.value)}/>
          </Field>
          <div style={{display:"flex",alignItems:"center",gap:8}}>
            <input type="checkbox" id="active" checked={form.is_active} onChange={e=>sf("is_active",e.target.checked)}/>
            <label htmlFor="active" style={{fontSize:13}}>Active</label>
          </div>
        </div>
        <div style={{display:"flex",gap:8,marginTop:14}}>
          <Btn variant="gold" onClick={save} disabled={createMut.isPending||updateMut.isPending}>
            {editing?"Save Changes":"Add Product"}
          </Btn>
          <Btn onClick={()=>{setOpen(false);setEditing(null);}}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}
