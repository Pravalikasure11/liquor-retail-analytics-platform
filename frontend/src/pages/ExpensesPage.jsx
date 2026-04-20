import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { expensesAPI } from "../services/api";
import { PageHeader, Modal, Field, Btn, Badge, Card, Loading, inputStyle, selectStyle } from "../components/ui.jsx";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Plus, Edit2, Trash2, Receipt } from "lucide-react";

const COLORS = ["#378ADD","#639922","#BA7517","#E24B4A","#534AB7","#0F6E56","#D4537E","#888780"];

const emptyForm = { title: "", amount: "", category_id: "", vendor: "", expense_date: new Date().toISOString().slice(0,10), notes: "", is_recurring: false, recurrence: "" };

export default function ExpensesPage() {
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editExp, setEditExp] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const { data: expenses, isLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => expensesAPI.list().then(r => r.data),
  });

  const { data: categories } = useQuery({
    queryKey: ["expense-cats"],
    queryFn: () => expensesAPI.listCategories().then(r => r.data),
  });

  const createMut = useMutation({
    mutationFn: (d) => expensesAPI.create(d),
    onSuccess: () => { qc.invalidateQueries(["expenses"]); toast.success("Expense added!"); setModalOpen(false); setForm(emptyForm); },
    onError: (e) => toast.error(e.response?.data?.detail || "Failed"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }) => expensesAPI.update(id, data),
    onSuccess: () => { qc.invalidateQueries(["expenses"]); toast.success("Updated!"); setModalOpen(false); },
  });

  const deleteMut = useMutation({
    mutationFn: (id) => expensesAPI.delete(id),
    onSuccess: () => { qc.invalidateQueries(["expenses"]); toast.success("Deleted"); },
  });

  const totalExpenses = (expenses || []).reduce((s, e) => s + e.amount, 0);

  // Monthly breakdown
  const monthlyMap = {};
  (expenses || []).forEach(e => {
    const m = e.expense_date?.slice(0, 7) || "unknown";
    monthlyMap[m] = (monthlyMap[m] || 0) + e.amount;
  });
  const monthlyData = Object.entries(monthlyMap).sort().slice(-6).map(([m, v]) => ({ month: m.slice(5), amount: Math.round(v) }));

  // By category
  const catMap = {};
  (expenses || []).forEach(e => {
    const cat = categories?.find(c => c.id === e.category_id)?.name || "Uncategorized";
    catMap[cat] = (catMap[cat] || 0) + e.amount;
  });
  const catData = Object.entries(catMap).sort((a, b) => b[1] - a[1]);

  const openAdd = () => { setForm(emptyForm); setEditExp(null); setModalOpen(true); };
  const openEdit = (e) => { setForm({ ...e, expense_date: e.expense_date?.slice(0, 10) || "" }); setEditExp(e); setModalOpen(true); };
  const handleSave = () => {
    const data = { ...form, amount: parseFloat(form.amount), category_id: form.category_id ? parseInt(form.category_id) : null };
    if (editExp) updateMut.mutate({ id: editExp.id, data });
    else createMut.mutate(data);
  };

  return (
    <div style={{ flex: 1, overflow: "auto" }}>
      <PageHeader title="Expenses" subtitle={`Total: $${totalExpenses.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
        actions={<Btn variant="gold" onClick={openAdd}><Plus size={14} /> Add Expense</Btn>}
      />

      <div style={{ padding: "16px 24px" }}>
        {/* Summary cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 20 }}>
          <div style={{ background: "#fff", border: "1px solid #ebebeb", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #E24B4A" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>TOTAL EXPENSES</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>${totalExpenses.toFixed(2)}</div>
          </div>
          <div style={{ background: "#fff", border: "1px solid #ebebeb", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #BA7517" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>THIS MONTH</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>
              ${(monthlyData[monthlyData.length - 1]?.amount || 0).toFixed(2)}
            </div>
          </div>
          <div style={{ background: "#fff", border: "1px solid #ebebeb", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #378ADD" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>CATEGORIES</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{catData.length}</div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <Card title="Monthly Expenses">
            <div style={{ padding: "0 16px 16px" }}>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={v => "$" + v} />
                  <Tooltip formatter={v => ["$" + v.toFixed(2), "Expenses"]} />
                  <Bar dataKey="amount" fill="#E24B4A" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="By Category">
            <div style={{ padding: "8px 18px" }}>
              {catData.map(([cat, amt], i) => {
                const max = catData[0]?.[1] || 1;
                const pct = Math.round(amt / max * 100);
                return (
                  <div key={cat} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 13 }}>{cat}</span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>${amt.toFixed(2)}</span>
                    </div>
                    <div style={{ height: 6, background: "#f0f0f0", borderRadius: 99 }}>
                      <div style={{ width: `${pct}%`, height: "100%", background: COLORS[i % COLORS.length], borderRadius: 99 }} />
                    </div>
                  </div>
                );
              })}
              {catData.length === 0 && <div style={{ color: "#aaa", fontSize: 13, padding: "12px 0" }}>No expenses recorded yet.</div>}
            </div>
          </Card>
        </div>

        {/* Table */}
        <Card title="All Expenses">
          <div style={{ overflowX: "auto" }}>
            {isLoading ? <Loading /> : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                    {["Date","Title","Category","Vendor","Amount","Recurring",""].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 11, fontWeight: 600, color: "#888", textTransform: "uppercase" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(expenses || []).map(e => {
                    const cat = categories?.find(c => c.id === e.category_id);
                    return (
                      <tr key={e.id} style={{ borderBottom: "1px solid #f8f8f8" }}
                        onMouseEnter={ev => ev.currentTarget.style.background = "#fafafa"}
                        onMouseLeave={ev => ev.currentTarget.style.background = "transparent"}>
                        <td style={{ padding: "10px 14px", color: "#888", fontSize: 12 }}>{e.expense_date?.slice(0, 10)}</td>
                        <td style={{ padding: "10px 14px", fontWeight: 500 }}>{e.title}</td>
                        <td style={{ padding: "10px 14px" }}>{cat ? <Badge color="blue">{cat.name}</Badge> : <Badge color="gray">Uncategorized</Badge>}</td>
                        <td style={{ padding: "10px 14px", color: "#888" }}>{e.vendor || "—"}</td>
                        <td style={{ padding: "10px 14px", fontWeight: 700, color: "#E24B4A" }}>${e.amount.toFixed(2)}</td>
                        <td style={{ padding: "10px 14px" }}>{e.is_recurring ? <Badge color="purple">{e.recurrence}</Badge> : <span style={{ color: "#ccc" }}>—</span>}</td>
                        <td style={{ padding: "10px 14px" }}>
                          <div style={{ display: "flex", gap: 4 }}>
                            <Btn size="sm" onClick={() => openEdit(e)}><Edit2 size={12} /></Btn>
                            <Btn size="sm" variant="danger" onClick={() => { if (confirm("Delete?")) deleteMut.mutate(e.id); }}><Trash2 size={12} /></Btn>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
            {!isLoading && expenses?.length === 0 && <div style={{ padding: 32, textAlign: "center", color: "#aaa", fontSize: 13 }}>No expenses yet. Add your first one.</div>}
          </div>
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editExp ? "Edit Expense" : "Add Expense"} width={480}>
        <Field label="Title"><input style={inputStyle} value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Electricity bill" /></Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Amount ($)"><input style={inputStyle} type="number" step="0.01" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" /></Field>
          <Field label="Date"><input style={inputStyle} type="date" value={form.expense_date} onChange={e => setForm(f => ({ ...f, expense_date: e.target.value }))} /></Field>
          <Field label="Category">
            <select style={selectStyle} value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
              <option value="">Select category...</option>
              {(categories || []).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Vendor"><input style={inputStyle} value={form.vendor || ""} onChange={e => setForm(f => ({ ...f, vendor: e.target.value }))} placeholder="Vendor name" /></Field>
        </div>
        <Field label="Notes"><textarea style={{ ...inputStyle, height: 60, resize: "vertical" }} value={form.notes || ""} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></Field>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <input type="checkbox" id="recurring" checked={form.is_recurring} onChange={e => setForm(f => ({ ...f, is_recurring: e.target.checked }))} />
          <label htmlFor="recurring" style={{ fontSize: 13 }}>Recurring expense</label>
          {form.is_recurring && (
            <select style={{ ...selectStyle, width: 120 }} value={form.recurrence || ""} onChange={e => setForm(f => ({ ...f, recurrence: e.target.value }))}>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          )}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Btn variant="gold" onClick={handleSave} disabled={createMut.isPending || updateMut.isPending}>Save</Btn>
          <Btn onClick={() => setModalOpen(false)}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}
