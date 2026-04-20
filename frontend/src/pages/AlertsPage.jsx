// AlertsPage.jsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productsAPI } from "../services/api";
import { PageHeader, Card, Badge, Btn, StockBar, Loading } from "../components/ui.jsx";
import { AlertTriangle, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { useState } from "react";
import { Modal, Field, inputStyle } from "../components/ui.jsx";

export function AlertsPage() {
  const qc = useQueryClient();
  const [restockModal, setRestockModal] = useState(null);
  const [restockQty, setRestockQty] = useState("");

  const { data: products, isLoading } = useQuery({
    queryKey: ["products-alerts"],
    queryFn: () => productsAPI.list({ low_stock: true }).then(r => r.data),
    refetchInterval: 60000,
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }) => productsAPI.update(id, data),
    onSuccess: () => { qc.invalidateQueries(["products-alerts"]); qc.invalidateQueries(["dashboard"]); toast.success("Stock updated!"); setRestockModal(null); },
  });

  const outOfStock = (products || []).filter(p => p.stock === 0);
  const lowStock   = (products || []).filter(p => p.stock > 0 && p.stock <= p.reorder_point);

  const handleRestock = () => {
    const qty = parseInt(restockQty);
    if (!qty || qty <= 0) { toast.error("Enter a valid quantity"); return; }
    updateMut.mutate({ id: restockModal.id, data: { stock: restockModal.stock + qty } });
  };

  return (
    <div style={{ flex: 1, overflow: "auto" }}>
      <PageHeader title="Stock Alerts"
        subtitle={`${outOfStock.length} out of stock · ${lowStock.length} low stock`}
      />
      <div style={{ padding: "16px 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginBottom: 20 }}>
          <div style={{ background: "#fff", border: "1px solid #fecaca", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #E24B4A" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>OUT OF STOCK</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#E24B4A" }}>{outOfStock.length}</div>
            <div style={{ fontSize: 12, color: "#aaa" }}>Order immediately</div>
          </div>
          <div style={{ background: "#fff", border: "1px solid #fde68a", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #BA7517" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>LOW STOCK</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#BA7517" }}>{lowStock.length}</div>
            <div style={{ fontSize: 12, color: "#aaa" }}>Below reorder point</div>
          </div>
          <div style={{ background: "#fff", border: "1px solid #bbf7d0", borderRadius: 12, padding: "16px 18px", borderTop: "3px solid #639922" }}>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>HEALTHY</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#639922" }}>
              {(products?.filter(p => p.stock > p.reorder_point)?.length || 0)}
            </div>
            <div style={{ fontSize: 12, color: "#aaa" }}>Well stocked</div>
          </div>
        </div>

        {outOfStock.length > 0 && (
          <Card title="🔴 Out of Stock — Order Now" style={{ marginBottom: 16 }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                  {["Product","Category","Reorder Qty","Action"].map(h => (
                    <th key={h} style={{ padding: "8px 14px", textAlign: "left", fontSize: 11, color: "#888", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {outOfStock.map(p => (
                    <tr key={p.id} style={{ borderBottom: "1px solid #f8f8f8" }}>
                      <td style={{ padding: "10px 14px", fontWeight: 600 }}>{p.name}</td>
                      <td style={{ padding: "10px 14px" }}><Badge color="gray">{p.category}</Badge></td>
                      <td style={{ padding: "10px 14px", color: "#888" }}>{p.reorder_qty} units</td>
                      <td style={{ padding: "10px 14px" }}>
                        <Btn size="sm" variant="gold" onClick={() => { setRestockModal(p); setRestockQty(String(p.reorder_qty)); }}>
                          <RefreshCw size={12} /> Restock
                        </Btn>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {lowStock.length > 0 && (
          <Card title="🟡 Low Stock — Reorder Soon">
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                  {["Product","Category","Stock Level","Reorder At","Action"].map(h => (
                    <th key={h} style={{ padding: "8px 14px", textAlign: "left", fontSize: 11, color: "#888", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {lowStock.map(p => (
                    <tr key={p.id} style={{ borderBottom: "1px solid #f8f8f8" }}>
                      <td style={{ padding: "10px 14px", fontWeight: 600 }}>{p.name}</td>
                      <td style={{ padding: "10px 14px" }}><Badge color="gray">{p.category}</Badge></td>
                      <td style={{ padding: "10px 14px" }}><StockBar stock={p.stock} reorderPoint={p.reorder_point} /></td>
                      <td style={{ padding: "10px 14px", color: "#888" }}>{p.reorder_point}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <Btn size="sm" onClick={() => { setRestockModal(p); setRestockQty(String(p.reorder_qty)); }}>
                          <RefreshCw size={12} /> Restock
                        </Btn>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {!isLoading && outOfStock.length === 0 && lowStock.length === 0 && (
          <Card><div style={{ textAlign: "center", padding: 40, color: "#aaa" }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
            <div style={{ fontWeight: 500 }}>All inventory levels are healthy!</div>
          </div></Card>
        )}
      </div>

      <Modal open={!!restockModal} onClose={() => setRestockModal(null)} title={`Restock: ${restockModal?.name}`} width={380}>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 14 }}>Current stock: <strong>{restockModal?.stock}</strong> units</p>
        <Field label="Units received">
          <input style={inputStyle} type="number" value={restockQty} onChange={e => setRestockQty(e.target.value)} min="1" />
        </Field>
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <Btn variant="gold" onClick={handleRestock} disabled={updateMut.isPending}>Confirm Receipt</Btn>
          <Btn onClick={() => setRestockModal(null)}>Cancel</Btn>
        </div>
      </Modal>
    </div>
  );
}

export default AlertsPage;
