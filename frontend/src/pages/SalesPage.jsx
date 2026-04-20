// SalesPage.jsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { salesAPI, productsAPI } from "../services/api";
import { PageHeader, Card, Badge, Btn, Modal, Field, Loading, inputStyle, selectStyle } from "../components/ui.jsx";
import { Plus, Trash2, ShoppingCart } from "lucide-react";

const fmt = (n) => "$" + Number(n || 0).toFixed(2);

export function SalesPage() {
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [items, setItems] = useState([{ product_id: "", qty: 1 }]);

  const { data: sales, isLoading } = useQuery({
    queryKey: ["sales"],
    queryFn: () => salesAPI.list({ limit: 100 }).then(r => r.data),
  });

  const { data: products } = useQuery({
    queryKey: ["products-all"],
    queryFn: () => productsAPI.list().then(r => r.data),
  });

  const createMut = useMutation({
    mutationFn: (data) => salesAPI.create(data),
    onSuccess: () => { qc.invalidateQueries(["sales"]); qc.invalidateQueries(["dashboard"]); qc.invalidateQueries(["products"]); toast.success("Sale recorded!"); setModalOpen(false); setItems([{ product_id: "", qty: 1 }]); },
    onError: (e) => toast.error(e.response?.data?.detail || "Failed"),
  });

  const deleteMut = useMutation({
    mutationFn: (id) => salesAPI.delete(id),
    onSuccess: () => { qc.invalidateQueries(["sales"]); qc.invalidateQueries(["dashboard"]); toast.success("Sale reversed"); },
  });

  const addItem = () => setItems(i => [...i, { product_id: "", qty: 1 }]);
  const removeItem = (idx) => setItems(i => i.filter((_, j) => j !== idx));
  const setItem = (idx, field, val) => setItems(i => i.map((item, j) => j === idx ? { ...item, [field]: val } : item));

  const preview = items.filter(i => i.product_id && i.qty > 0).map(i => {
    const p = products?.find(p => p.id === parseInt(i.product_id));
    if (!p) return null;
    return { name: p.name, qty: parseInt(i.qty), revenue: parseInt(i.qty) * p.sell_price, profit: parseInt(i.qty) * (p.sell_price - p.cost_price) };
  }).filter(Boolean);

  const totalRev = preview.reduce((s, x) => s + x.revenue, 0);
  const totalProfit = preview.reduce((s, x) => s + x.profit, 0);

  const handleCreate = () => {
    const saleItems = items.filter(i => i.product_id && i.qty > 0).map(i => ({ product_id: parseInt(i.product_id), quantity: parseInt(i.qty) }));
    if (!saleItems.length) { toast.error("Add at least one item"); return; }
    createMut.mutate({ items: saleItems });
  };

  return (
    <div style={{ flex: 1, overflow: "auto" }}>
      <PageHeader title="Sales" subtitle={`${sales?.length || 0} transactions`}
        actions={<Btn variant="gold" onClick={() => setModalOpen(true)}><Plus size={14} /> Record Sale</Btn>}
      />

      <div style={{ padding: "16px 24px" }}>
        <Card>
          <div style={{ overflowX: "auto" }}>
            {isLoading ? <Loading /> : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                    {["Date","Items","Revenue","Cost","Profit","Margin","Payment",""].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 11, color: "#888", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(sales || []).map(s => {
                    const margin = s.total_revenue > 0 ? Math.round(s.total_profit / s.total_revenue * 100) : 0;
                    return (
                      <tr key={s.id} style={{ borderBottom: "1px solid #f8f8f8" }}>
                        <td style={{ padding: "10px 14px", color: "#888", fontSize: 12 }}>{new Date(s.sale_date).toLocaleString()}</td>
                        <td style={{ padding: "10px 14px" }}>{s.items?.length || 0} item{s.items?.length !== 1 ? "s" : ""}</td>
                        <td style={{ padding: "10px 14px", fontWeight: 700, color: "#d4af37" }}>{fmt(s.total_revenue)}</td>
                        <td style={{ padding: "10px 14px", color: "#888" }}>{fmt(s.total_cost)}</td>
                        <td style={{ padding: "10px 14px", fontWeight: 700, color: "#639922" }}>{fmt(s.total_profit)}</td>
                        <td style={{ padding: "10px 14px" }}>
                          <Badge color={margin > 40 ? "green" : margin > 25 ? "amber" : "red"}>{margin}%</Badge>
                        </td>
                        <td style={{ padding: "10px 14px" }}><Badge color="gray">{s.payment_method}</Badge></td>
                        <td style={{ padding: "10px 14px" }}>
                          <Btn size="sm" variant="danger" onClick={() => { if (confirm("Reverse this sale?")) deleteMut.mutate(s.id); }}>
                            <Trash2 size={12} />
                          </Btn>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Record Sale" width={520}>
        {items.map((item, idx) => (
          <div key={idx} style={{ display: "grid", gridTemplateColumns: "1fr 80px 32px", gap: 8, marginBottom: 10, alignItems: "end" }}>
            <Field label={idx === 0 ? "Product" : ""}>
              <select style={selectStyle} value={item.product_id} onChange={e => setItem(idx, "product_id", e.target.value)}>
                <option value="">Select product...</option>
                {(products || []).map(p => <option key={p.id} value={p.id}>{p.name} (stock: {p.stock}) — ${p.sell_price}</option>)}
              </select>
            </Field>
            <Field label={idx === 0 ? "Qty" : ""}>
              <input style={inputStyle} type="number" min="1" value={item.qty} onChange={e => setItem(idx, "qty", e.target.value)} />
            </Field>
            <div style={{ paddingBottom: 0 }}>
              <Btn size="sm" variant="danger" onClick={() => removeItem(idx)}><Trash2 size={12} /></Btn>
            </div>
          </div>
        ))}
        <Btn size="sm" onClick={addItem} style={{ marginBottom: 16 }}><Plus size={12} /> Add item</Btn>

        {preview.length > 0 && (
          <div style={{ background: "#f8fdf4", border: "1px solid #d4edda", borderRadius: 8, padding: "12px 14px", marginBottom: 14, fontSize: 13 }}>
            {preview.map(p => (
              <div key={p.name} style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span>{p.qty}× {p.name}</span>
                <span style={{ color: "#639922" }}>${p.revenue.toFixed(2)}</span>
              </div>
            ))}
            <div style={{ borderTop: "1px solid #d4edda", paddingTop: 8, marginTop: 8, fontWeight: 700, display: "flex", justifyContent: "space-between" }}>
              <span>Total: ${totalRev.toFixed(2)}</span>
              <span style={{ color: "#639922" }}>Profit: ${totalProfit.toFixed(2)}</span>
            </div>
          </div>
        )}

        <div style={{ display: "flex", gap: 8 }}>
          <Btn variant="gold" onClick={handleCreate} disabled={createMut.isPending}>Record Sale</Btn>
          <Btn onClick={() => setModalOpen(false)}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}

export default SalesPage;
