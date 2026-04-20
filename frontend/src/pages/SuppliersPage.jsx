import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { PageHeader, Card, Modal, Field, Btn, Badge, Loading, Empty, inputStyle, selectStyle } from "../components/ui.jsx";
import { Plus, Edit2, Trash2, Phone, Mail, Globe, Package, ChevronDown, ChevronUp, Search } from "lucide-react";
import api from "../services/api.js";

const suppliersAPI = {
  list:   ()         => api.get("/suppliers/"),
  create: (data)     => api.post("/suppliers/", data),
  update: (id, data) => api.patch(`/suppliers/${id}`, data),
  delete: (id)       => api.delete(`/suppliers/${id}`),
};

const PORTAL_TYPES = ["custom","breakthru","rndc","glazers"];
const empty = { name:"", contact_email:"", phone:"", address:"", website:"", portal_url:"", portal_username:"", portal_password:"", portal_type:"custom", lead_days:5, notes:"", monitor_deals:false };

export default function SuppliersPage() {
  const qc = useQueryClient();
  const [open, setOpen]       = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm]       = useState(empty);
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch]   = useState("");
  const [showPortal, setShowPortal] = useState(false);

  const { data: suppliers, isLoading } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => suppliersAPI.list().then(r => r.data),
  });

  const createMut = useMutation({
    mutationFn: d => suppliersAPI.create(d),
    onSuccess: () => { qc.invalidateQueries(["suppliers"]); toast.success("Supplier added!"); setOpen(false); setForm(empty); },
    onError: e => toast.error(e.response?.data?.detail || "Failed"),
  });
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => suppliersAPI.update(id, data),
    onSuccess: () => { qc.invalidateQueries(["suppliers"]); toast.success("Supplier updated!"); setOpen(false); setEditing(null); },
    onError: e => toast.error(e.response?.data?.detail || "Failed"),
  });
  const deleteMut = useMutation({
    mutationFn: id => suppliersAPI.delete(id),
    onSuccess: () => { qc.invalidateQueries(["suppliers"]); toast.success("Removed"); },
  });

  const openAdd  = () => { setForm(empty); setEditing(null); setShowPortal(false); setOpen(true); };
  const openEdit = s => { setForm({ ...s, portal_password:"" }); setEditing(s); setShowPortal(!!s.portal_url); setOpen(true); };
  const sf = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const save = () => {
    if (!form.name.trim()) { toast.error("Name required"); return; }
    const data = { ...form, lead_days: parseInt(form.lead_days) || 5 };
    if (!data.portal_password) delete data.portal_password;
    if (editing) updateMut.mutate({ id: editing.id, data });
    else createMut.mutate(data);
  };

  const filtered = (suppliers || []).filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    (s.contact_email||"").toLowerCase().includes(search.toLowerCase()) ||
    (s.phone||"").includes(search)
  );

  return (
    <div style={{ flex:1, overflow:"auto" }}>
      <PageHeader title="Suppliers" subtitle={`${suppliers?.length||0} suppliers`}
        actions={<Btn variant="gold" onClick={openAdd}><Plus size={14}/> Add Supplier</Btn>}
      />
      <div style={{ padding:"16px 24px" }}>

        {/* Search bar */}
        <div style={{ position:"relative", marginBottom:16, width:280 }}>
          <Search size={14} style={{ position:"absolute", left:10, top:"50%", transform:"translateY(-50%)", color:"#aaa" }}/>
          <input style={{ ...inputStyle, paddingLeft:32 }} placeholder="Search suppliers..." value={search} onChange={e => setSearch(e.target.value)}/>
        </div>

        {isLoading ? <Loading/> : filtered.length === 0 ? (
          <Card><Empty message="No suppliers yet. Add your first supplier." icon={Package}/></Card>
        ) : (
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            {filtered.map(s => (
              <div key={s.id} style={{ background:"#fff", border:"1px solid #ebebeb", borderRadius:12, overflow:"hidden" }}>

                {/* Main row */}
                <div style={{ padding:"14px 18px", display:"flex", alignItems:"center", gap:12 }}>
                  <div style={{ width:42, height:42, borderRadius:10, background:"#f5f5f3", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700, fontSize:16, color:"#888", flexShrink:0 }}>
                    {s.name[0].toUpperCase()}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontWeight:700, fontSize:14 }}>{s.name}</div>
                    <div style={{ display:"flex", gap:14, marginTop:3, flexWrap:"wrap" }}>
                      {s.contact_email && <span style={{ fontSize:12, color:"#888", display:"flex", alignItems:"center", gap:3 }}><Mail size={11}/>{s.contact_email}</span>}
                      {s.phone         && <span style={{ fontSize:12, color:"#888", display:"flex", alignItems:"center", gap:3 }}><Phone size={11}/>{s.phone}</span>}
                      {s.website       && <span style={{ fontSize:12, color:"#888", display:"flex", alignItems:"center", gap:3 }}><Globe size={11}/>{s.website}</span>}
                    </div>
                  </div>
                  <div style={{ display:"flex", alignItems:"center", gap:6, flexShrink:0 }}>
                    <Badge color="gray">{s.lead_days}d lead time</Badge>
                    {s.monitor_deals    && <Badge color="green">Auto-monitor</Badge>}
                    {s.portal_type !== "custom" && <Badge color="blue">{s.portal_type}</Badge>}
                    <button onClick={() => setExpanded(expanded===s.id ? null : s.id)} style={{ background:"none", border:"none", cursor:"pointer", color:"#bbb", padding:4 }}>
                      {expanded===s.id ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                    </button>
                    <Btn size="sm" onClick={() => openEdit(s)}><Edit2 size={12}/></Btn>
                    <Btn size="sm" variant="danger" onClick={() => { if(confirm(`Remove ${s.name}?`)) deleteMut.mutate(s.id); }}><Trash2 size={12}/></Btn>
                  </div>
                </div>

                {/* Expanded details */}
                {expanded===s.id && (
                  <div style={{ padding:"8px 18px 14px", borderTop:"1px solid #f5f5f5", background:"#fafafa" }}>
                    <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))", gap:12, marginTop:8 }}>
                      {[
                        ["Address",       s.address],
                        ["Lead Time",     s.lead_days+" days"],
                        ["Portal Type",   s.portal_type],
                        ["Portal URL",    s.portal_url],
                        ["Portal Login",  s.portal_username],
                        ["Password Set",  s.portal_password_set ? "Yes" : "No"],
                        ["Notes",         s.notes],
                      ].filter(([,v]) => v).map(([label, value]) => (
                        <div key={label}>
                          <div style={{ fontSize:11, color:"#aaa", marginBottom:2 }}>{label}</div>
                          <div style={{ fontSize:13, color:"#333", wordBreak:"break-word" }}>{value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal open={open} onClose={() => { setOpen(false); setEditing(null); }} title={editing ? `Edit: ${editing.name}` : "Add New Supplier"} width={520}>
        <Field label="Supplier Name *">
          <input style={inputStyle} value={form.name} onChange={e => sf("name",e.target.value)} placeholder="e.g. Breakthru Beverage"/>
        </Field>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          <Field label="Contact Email">
            <input style={inputStyle} type="email" value={form.contact_email||""} onChange={e => sf("contact_email",e.target.value)} placeholder="orders@supplier.com"/>
          </Field>
          <Field label="Phone">
            <input style={inputStyle} value={form.phone||""} onChange={e => sf("phone",e.target.value)} placeholder="555-000-1234"/>
          </Field>
          <Field label="Website">
            <input style={inputStyle} value={form.website||""} onChange={e => sf("website",e.target.value)} placeholder="https://supplier.com"/>
          </Field>
          <Field label="Lead Days">
            <input style={inputStyle} type="number" value={form.lead_days} onChange={e => sf("lead_days",e.target.value)} min="1"/>
          </Field>
        </div>
        <Field label="Address">
          <input style={inputStyle} value={form.address||""} onChange={e => sf("address",e.target.value)} placeholder="123 Main St, City, State"/>
        </Field>
        <Field label="Notes">
          <textarea style={{ ...inputStyle, height:60, resize:"vertical" }} value={form.notes||""} onChange={e => sf("notes",e.target.value)} placeholder="Any notes..."/>
        </Field>

        {/* Portal toggle */}
        <div onClick={() => setShowPortal(!showPortal)} style={{ display:"flex", alignItems:"center", gap:8, cursor:"pointer", padding:"10px 0", borderTop:"1px solid #f0f0f0", marginTop:4 }}>
          <span style={{ fontSize:13, fontWeight:600, color:"#333" }}>{showPortal ? "▾" : "▸"} Portal & Deal Monitoring</span>
          <span style={{ fontSize:11, color:"#aaa" }}>optional — for auto deal alerts</span>
        </div>

        {showPortal && (
          <div style={{ background:"#fafafa", border:"1px solid #eee", borderRadius:10, padding:"14px 16px", marginBottom:8 }}>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
              <Field label="Portal Type">
                <select style={selectStyle} value={form.portal_type} onChange={e => sf("portal_type",e.target.value)}>
                  {PORTAL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Portal URL">
                <input style={inputStyle} value={form.portal_url||""} onChange={e => sf("portal_url",e.target.value)} placeholder="https://portal.supplier.com"/>
              </Field>
              <Field label="Username / Email">
                <input style={inputStyle} value={form.portal_username||""} onChange={e => sf("portal_username",e.target.value)} placeholder="your login"/>
              </Field>
              <Field label={editing ? "Password (blank = keep existing)" : "Password"}>
                <input style={inputStyle} type="password" value={form.portal_password||""} onChange={e => sf("portal_password",e.target.value)} placeholder={editing ? "••••••••" : "your password"}/>
              </Field>
            </div>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginTop:10 }}>
              <input type="checkbox" id="mon" checked={form.monitor_deals} onChange={e => sf("monitor_deals",e.target.checked)}/>
              <label htmlFor="mon" style={{ fontSize:13, cursor:"pointer" }}>Check this portal automatically for deals every hour</label>
            </div>
          </div>
        )}

        <div style={{ display:"flex", gap:8, marginTop:12 }}>
          <Btn variant="gold" onClick={save} disabled={createMut.isPending||updateMut.isPending}>
            {editing ? "Save Changes" : "Add Supplier"}
          </Btn>
          <Btn onClick={() => { setOpen(false); setEditing(null); }}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}
