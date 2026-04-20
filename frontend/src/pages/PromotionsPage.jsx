import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { PageHeader, Card, Modal, Field, Btn, Badge, Loading, Empty, inputStyle, selectStyle } from "../components/ui.jsx";
import { Plus, Edit2, Trash2, Tag, Calendar, Percent, Search, ToggleLeft, ToggleRight } from "lucide-react";
import api from "../services/api.js";

// In-store promotions stored as a local API endpoint
const promoAPI = {
  list:   ()         => api.get("/promotions/"),
  create: (data)     => api.post("/promotions/", data),
  update: (id, data) => api.patch(`/promotions/${id}`, data),
  delete: (id)       => api.delete(`/promotions/${id}`),
};

const PROMO_TYPES = ["Percentage Off", "Dollar Off", "Buy X Get Y", "Bundle Deal", "Happy Hour", "Clearance", "New Arrival", "Featured"];
const CATEGORIES  = ["Beer","Hard Liquor","Wine","Hard Cider","Cocktails","Cool Drinks","Cigarettes","E-Cigarettes","Snacks & Chips","Accessories","All Categories"];

const empty = {
  title: "", description: "", promo_type: "Percentage Off",
  discount_value: "", category: "All Categories",
  product_name: "", buy_qty: "", get_qty: "",
  start_date: new Date().toISOString().slice(0,10),
  end_date: "", is_active: true, notes: "",
};

const typeColor = (t) => {
  const map = {
    "Percentage Off": "green", "Dollar Off": "blue",
    "Buy X Get Y": "purple", "Bundle Deal": "amber",
    "Happy Hour": "gold", "Clearance": "red",
    "New Arrival": "green", "Featured": "amber",
  };
  return map[t] || "gray";
};

export default function PromotionsPage() {
  const qc = useQueryClient();
  const [open, setOpen]       = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm]       = useState(empty);
  const [search, setSearch]   = useState("");
  const [filterActive, setFilterActive] = useState("all");

  const { data: promos, isLoading, error } = useQuery({
    queryKey: ["promotions"],
    queryFn: () => promoAPI.list().then(r => r.data),
    retry: false,
  });

  const createMut = useMutation({
    mutationFn: d => promoAPI.create(d),
    onSuccess: () => { qc.invalidateQueries(["promotions"]); toast.success("Promotion added!"); setOpen(false); setForm(empty); },
    onError: e => toast.error(e.response?.data?.detail || "Failed to save"),
  });
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => promoAPI.update(id, data),
    onSuccess: () => { qc.invalidateQueries(["promotions"]); toast.success("Promotion updated!"); setOpen(false); setEditing(null); },
    onError: e => toast.error(e.response?.data?.detail || "Failed"),
  });
  const deleteMut = useMutation({
    mutationFn: id => promoAPI.delete(id),
    onSuccess: () => { qc.invalidateQueries(["promotions"]); toast.success("Promotion removed"); },
  });
  const toggleMut = useMutation({
    mutationFn: ({ id, is_active }) => promoAPI.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries(["promotions"]),
  });

  const openAdd  = () => { setForm(empty); setEditing(null); setOpen(true); };
  const openEdit = p => { setForm({ ...p, start_date: p.start_date?.slice(0,10)||"", end_date: p.end_date?.slice(0,10)||"" }); setEditing(p); setOpen(true); };
  const sf = (k,v) => setForm(f => ({ ...f, [k]: v }));

  const save = () => {
    if (!form.title.trim()) { toast.error("Title required"); return; }
    const data = { ...form, discount_value: form.discount_value ? parseFloat(form.discount_value) : null, buy_qty: form.buy_qty ? parseInt(form.buy_qty) : null, get_qty: form.get_qty ? parseInt(form.get_qty) : null };
    if (editing) updateMut.mutate({ id: editing.id, data });
    else createMut.mutate(data);
  };

  const today = new Date().toISOString().slice(0,10);

  const isExpired = p => p.end_date && p.end_date.slice(0,10) < today;
  const isActive  = p => p.is_active && !isExpired(p);

  const filtered = (promos || []).filter(p => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) ||
      (p.description||"").toLowerCase().includes(search.toLowerCase()) ||
      (p.product_name||"").toLowerCase().includes(search.toLowerCase());
    const matchStatus = filterActive === "all" ? true : filterActive === "active" ? isActive(p) : !isActive(p);
    return matchSearch && matchStatus;
  });

  const activeCount  = (promos||[]).filter(isActive).length;
  const expiredCount = (promos||[]).filter(isExpired).length;

  // If backend doesn't have promotions endpoint yet, show local storage fallback
  if (error) {
    return <LocalPromotionsPage />;
  }

  return <PromotionsUI
    promos={filtered} isLoading={isLoading}
    activeCount={activeCount} expiredCount={expiredCount}
    search={search} setSearch={setSearch}
    filterActive={filterActive} setFilterActive={setFilterActive}
    openAdd={openAdd} openEdit={openEdit}
    deleteMut={deleteMut} toggleMut={toggleMut}
    isActive={isActive} isExpired={isExpired}
    open={open} setOpen={setOpen} editing={editing} setEditing={setEditing}
    form={form} sf={sf} save={save} createMut={createMut} updateMut={updateMut}
  />;
}

// ── Fully local (no backend needed) ──────────────────────────────────────────
function LocalPromotionsPage() {
  const STORAGE_KEY = "zachs-promotions-v1";
  const load = () => { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; } };
  const save_local = (data) => localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

  const [promos, setPromos] = useState(load);
  const [open, setOpen]     = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm]     = useState(empty);
  const [search, setSearch] = useState("");
  const [filterActive, setFilterActive] = useState("all");
  const sf = (k,v) => setForm(f => ({ ...f, [k]: v }));

  const today = new Date().toISOString().slice(0,10);
  const isExpired = p => p.end_date && p.end_date < today;
  const isActive  = p => p.is_active && !isExpired(p);

  const savePromo = () => {
    if (!form.title.trim()) { toast.error("Title required"); return; }
    let updated;
    if (editing) {
      updated = promos.map(p => p.id === editing.id ? { ...form, id: editing.id } : p);
      toast.success("Updated!");
    } else {
      updated = [...promos, { ...form, id: Date.now() }];
      toast.success("Promotion added!");
    }
    setPromos(updated); save_local(updated); setOpen(false); setEditing(null); setForm(empty);
  };

  const deletePromo = id => {
    const updated = promos.filter(p => p.id !== id);
    setPromos(updated); save_local(updated); toast.success("Removed");
  };

  const togglePromo = id => {
    const updated = promos.map(p => p.id === id ? { ...p, is_active: !p.is_active } : p);
    setPromos(updated); save_local(updated);
  };

  const filtered = promos.filter(p => {
    const matchSearch = p.title.toLowerCase().includes(search.toLowerCase()) || (p.description||"").toLowerCase().includes(search.toLowerCase());
    const matchStatus = filterActive === "all" ? true : filterActive === "active" ? isActive(p) : !isActive(p);
    return matchSearch && matchStatus;
  });

  return <PromotionsUI
    promos={filtered} isLoading={false}
    activeCount={promos.filter(isActive).length}
    expiredCount={promos.filter(isExpired).length}
    search={search} setSearch={setSearch}
    filterActive={filterActive} setFilterActive={setFilterActive}
    openAdd={() => { setForm(empty); setEditing(null); setOpen(true); }}
    openEdit={p => { setForm(p); setEditing(p); setOpen(true); }}
    deleteMut={{ mutate: deletePromo }}
    toggleMut={{ mutate: ({ id, is_active }) => togglePromo(id) }}
    isActive={isActive} isExpired={isExpired}
    open={open} setOpen={setOpen} editing={editing} setEditing={setEditing}
    form={form} sf={sf} save={savePromo}
    createMut={{ isPending: false }} updateMut={{ isPending: false }}
  />;
}

// ── Shared UI ─────────────────────────────────────────────────────────────────
function PromotionsUI({ promos, isLoading, activeCount, expiredCount, search, setSearch, filterActive, setFilterActive, openAdd, openEdit, deleteMut, toggleMut, isActive, isExpired, open, setOpen, editing, setEditing, form, sf, save, createMut, updateMut }) {
  const today = new Date().toISOString().slice(0,10);

  return (
    <div style={{ flex:1, overflow:"auto" }}>
      <PageHeader title="In-Store Promotions" subtitle="Manage deals and offers running in the store"
        actions={<Btn variant="gold" onClick={openAdd}><Plus size={14}/> Add Promotion</Btn>}
      />
      <div style={{ padding:"16px 24px" }}>

        {/* Stats */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:20 }}>
          <div style={{ background:"#fff", border:"1px solid #ebebeb", borderRadius:12, padding:"14px 18px", borderTop:"3px solid #639922" }}>
            <div style={{ fontSize:12, color:"#888", marginBottom:4 }}>ACTIVE PROMOTIONS</div>
            <div style={{ fontSize:26, fontWeight:700, color:"#639922" }}>{activeCount}</div>
          </div>
          <div style={{ background:"#fff", border:"1px solid #ebebeb", borderRadius:12, padding:"14px 18px", borderTop:"3px solid #BA7517" }}>
            <div style={{ fontSize:12, color:"#888", marginBottom:4 }}>TOTAL PROMOTIONS</div>
            <div style={{ fontSize:26, fontWeight:700 }}>{promos.length + (filterActive !== "all" ? 0 : 0)}</div>
          </div>
          <div style={{ background:"#fff", border:"1px solid #ebebeb", borderRadius:12, padding:"14px 18px", borderTop:"3px solid #aaa" }}>
            <div style={{ fontSize:12, color:"#888", marginBottom:4 }}>EXPIRED</div>
            <div style={{ fontSize:26, fontWeight:700, color:"#aaa" }}>{expiredCount}</div>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display:"flex", gap:10, marginBottom:16, flexWrap:"wrap", alignItems:"center" }}>
          <div style={{ position:"relative" }}>
            <Search size={14} style={{ position:"absolute", left:10, top:"50%", transform:"translateY(-50%)", color:"#aaa" }}/>
            <input style={{ ...inputStyle, paddingLeft:32, width:240 }} placeholder="Search promotions..." value={search} onChange={e => setSearch(e.target.value)}/>
          </div>
          <div style={{ display:"flex", background:"#f5f5f3", borderRadius:8, padding:3, gap:2 }}>
            {[["all","All"],["active","Active"],["inactive","Inactive"]].map(([val,label]) => (
              <button key={val} onClick={() => setFilterActive(val)} style={{
                padding:"5px 12px", borderRadius:6, border:"none", cursor:"pointer", fontSize:12,
                background: filterActive===val ? "#111" : "transparent",
                color: filterActive===val ? "#fff" : "#888",
                fontWeight: filterActive===val ? 600 : 400,
              }}>{label}</button>
            ))}
          </div>
        </div>

        {/* Promotions grid */}
        {isLoading ? <Loading/> : promos.length === 0 ? (
          <Card>
            <Empty message={search ? "No promotions match your search." : "No promotions yet. Add your first deal or offer."} icon={Tag}/>
          </Card>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))", gap:14 }}>
            {promos.map(p => {
              const expired = isExpired(p);
              const active  = isActive(p);
              const borderColor = active ? "#639922" : expired ? "#ccc" : "#E24B4A";
              const daysLeft = p.end_date ? Math.ceil((new Date(p.end_date) - new Date()) / 86400000) : null;

              return (
                <div key={p.id} style={{ background:"#fff", border:`1px solid #ebebeb`, borderLeft:`4px solid ${borderColor}`, borderRadius:12, padding:"16px 18px", position:"relative" }}>
                  {/* Active toggle */}
                  <div style={{ position:"absolute", top:12, right:12 }}>
                    <button
                      onClick={() => toggleMut.mutate({ id: p.id, is_active: !p.is_active })}
                      style={{ background:"none", border:"none", cursor:"pointer", color: p.is_active ? "#639922" : "#ccc" }}
                      title={p.is_active ? "Click to deactivate" : "Click to activate"}
                    >
                      {p.is_active ? <ToggleRight size={22}/> : <ToggleLeft size={22}/>}
                    </button>
                  </div>

                  <div style={{ marginBottom:8, paddingRight:32 }}>
                    <Badge color={typeColor(p.promo_type)}>{p.promo_type}</Badge>
                    {expired && <span style={{ marginLeft:6 }}><Badge color="gray">Expired</Badge></span>}
                  </div>

                  <div style={{ fontWeight:700, fontSize:15, marginBottom:4 }}>{p.title}</div>

                  {/* Discount highlight */}
                  {p.discount_value && (
                    <div style={{ display:"inline-flex", alignItems:"center", gap:4, background:"#fef3c7", color:"#92400e", borderRadius:8, padding:"4px 10px", fontSize:13, fontWeight:700, marginBottom:8 }}>
                      <Percent size={13}/>
                      {p.promo_type === "Percentage Off" ? `${p.discount_value}% OFF` :
                       p.promo_type === "Dollar Off"     ? `$${p.discount_value} OFF` :
                       p.discount_value}
                    </div>
                  )}

                  {p.promo_type === "Buy X Get Y" && p.buy_qty && (
                    <div style={{ display:"inline-flex", alignItems:"center", gap:4, background:"#eeedfe", color:"#534AB7", borderRadius:8, padding:"4px 10px", fontSize:13, fontWeight:700, marginBottom:8 }}>
                      Buy {p.buy_qty} Get {p.get_qty||1} Free
                    </div>
                  )}

                  {p.description && <div style={{ fontSize:13, color:"#666", marginBottom:8, lineHeight:1.5 }}>{p.description}</div>}

                  <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginBottom:10 }}>
                    {p.category && p.category !== "All Categories" && <Badge color="blue">{p.category}</Badge>}
                    {p.product_name && <span style={{ fontSize:12, color:"#888" }}>📦 {p.product_name}</span>}
                  </div>

                  {/* Dates */}
                  <div style={{ fontSize:11, color:"#aaa", display:"flex", gap:10, alignItems:"center", marginBottom:12 }}>
                    <Calendar size={11}/>
                    {p.start_date && <span>From {p.start_date}</span>}
                    {p.end_date   && <span>Until {p.end_date}</span>}
                    {daysLeft !== null && daysLeft >= 0 && <span style={{ color: daysLeft <= 3 ? "#E24B4A" : "#BA7517", fontWeight:600 }}>
                      {daysLeft === 0 ? "Ends today!" : `${daysLeft} days left`}
                    </span>}
                  </div>

                  {p.notes && <div style={{ fontSize:12, color:"#888", fontStyle:"italic", marginBottom:10 }}>{p.notes}</div>}

                  <div style={{ display:"flex", gap:6 }}>
                    <Btn size="sm" onClick={() => openEdit(p)}><Edit2 size={12}/> Edit</Btn>
                    <Btn size="sm" variant="danger" onClick={() => { if(confirm("Remove this promotion?")) deleteMut.mutate(p.id); }}>
                      <Trash2 size={12}/> Delete
                    </Btn>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal open={open} onClose={() => { setOpen(false); setEditing(null); }} title={editing ? "Edit Promotion" : "Add New Promotion"} width={500}>
        <Field label="Promotion Title *">
          <input style={inputStyle} value={form.title} onChange={e => sf("title",e.target.value)} placeholder="e.g. Summer Beer Sale — 20% Off All Imports"/>
        </Field>

        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          <Field label="Promotion Type">
            <select style={selectStyle} value={form.promo_type} onChange={e => sf("promo_type",e.target.value)}>
              {PROMO_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Category">
            <select style={selectStyle} value={form.category} onChange={e => sf("category",e.target.value)}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
        </div>

        {/* Discount value */}
        {(form.promo_type === "Percentage Off" || form.promo_type === "Dollar Off") && (
          <Field label={form.promo_type === "Percentage Off" ? "Discount %" : "Discount Amount ($)"}>
            <input style={inputStyle} type="number" value={form.discount_value||""} onChange={e => sf("discount_value",e.target.value)} placeholder={form.promo_type === "Percentage Off" ? "e.g. 20" : "e.g. 5.00"} min="0"/>
          </Field>
        )}

        {form.promo_type === "Buy X Get Y" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <Field label="Buy quantity">
              <input style={inputStyle} type="number" value={form.buy_qty||""} onChange={e => sf("buy_qty",e.target.value)} placeholder="e.g. 2" min="1"/>
            </Field>
            <Field label="Get quantity free">
              <input style={inputStyle} type="number" value={form.get_qty||""} onChange={e => sf("get_qty",e.target.value)} placeholder="e.g. 1" min="1"/>
            </Field>
          </div>
        )}

        <Field label="Specific Product (optional — leave blank for whole category)">
          <input style={inputStyle} value={form.product_name||""} onChange={e => sf("product_name",e.target.value)} placeholder="e.g. Corona 12-Pack, Jack Daniel's 750ml..."/>
        </Field>

        <Field label="Description">
          <textarea style={{ ...inputStyle, height:70, resize:"vertical" }} value={form.description||""} onChange={e => sf("description",e.target.value)} placeholder="Tell customers what this deal is about..."/>
        </Field>

        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          <Field label="Start Date">
            <input style={inputStyle} type="date" value={form.start_date||""} onChange={e => sf("start_date",e.target.value)}/>
          </Field>
          <Field label="End Date (optional)">
            <input style={inputStyle} type="date" value={form.end_date||""} onChange={e => sf("end_date",e.target.value)}/>
          </Field>
        </div>

        <Field label="Internal Notes (not shown to customers)">
          <input style={inputStyle} value={form.notes||""} onChange={e => sf("notes",e.target.value)} placeholder="e.g. from supplier deal, check stock before promoting..."/>
        </Field>

        <div style={{ display:"flex", alignItems:"center", gap:8, margin:"12px 0" }}>
          <input type="checkbox" id="active" checked={form.is_active} onChange={e => sf("is_active",e.target.checked)}/>
          <label htmlFor="active" style={{ fontSize:13, cursor:"pointer" }}>Active (visible / running now)</label>
        </div>

        <div style={{ display:"flex", gap:8 }}>
          <Btn variant="gold" onClick={save} disabled={createMut.isPending||updateMut.isPending}>
            {editing ? "Save Changes" : "Add Promotion"}
          </Btn>
          <Btn onClick={() => { setOpen(false); setEditing(null); }}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}
