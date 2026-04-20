import { X } from "lucide-react";
import { clsx } from "clsx";

// ── KPI Card ──────────────────────────────────────────────────────────────────
export function KPICard({ label, value, sub, color = "#378ADD", icon: Icon, trend }) {
  const isNeg = typeof trend === "number" && trend < 0;
  return (
    <div style={{
      background: "#fff", border: "1px solid #ebebeb", borderRadius: 12,
      padding: "16px 18px", borderTop: `3px solid ${color}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ fontSize: 12, color: "#888", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
        {Icon && <Icon size={16} color={color} style={{ opacity: 0.7 }} />}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: "#111", fontVariantNumeric: "tabular-nums" }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "#aaa", marginTop: 4 }}>{sub}</div>}
      {typeof trend === "number" && (
        <div style={{ fontSize: 12, color: isNeg ? "#E24B4A" : "#639922", marginTop: 4, fontWeight: 500 }}>
          {isNeg ? "▼" : "▲"} {Math.abs(trend)}% vs last period
        </div>
      )}
    </div>
  );
}

// ── Page Header ───────────────────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div style={{
      background: "#fff", borderBottom: "1px solid #ebebeb",
      padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between",
      flexShrink: 0,
    }}>
      <div>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: "#111", margin: 0 }}>{title}</h1>
        {subtitle && <p style={{ fontSize: 12, color: "#888", margin: "3px 0 0" }}>{subtitle}</p>}
      </div>
      {actions && <div style={{ display: "flex", gap: 8, alignItems: "center" }}>{actions}</div>}
    </div>
  );
}

// ── Button ────────────────────────────────────────────────────────────────────
export function Btn({ children, onClick, variant = "default", size = "md", disabled, type = "button", style: extraStyle }) {
  const base = {
    display: "inline-flex", alignItems: "center", gap: 6,
    border: "none", cursor: disabled ? "not-allowed" : "pointer",
    borderRadius: 8, fontWeight: 600, transition: "opacity 0.1s",
    opacity: disabled ? 0.5 : 1, fontFamily: "inherit",
  };
  const sizes = { sm: { padding: "5px 10px", fontSize: 12 }, md: { padding: "8px 16px", fontSize: 13 }, lg: { padding: "10px 20px", fontSize: 14 } };
  const variants = {
    default:  { background: "#fff", color: "#333", border: "1px solid #ddd" },
    primary:  { background: "#111", color: "#fff" },
    gold:     { background: "#d4af37", color: "#111" },
    danger:   { background: "#fff5f5", color: "#E24B4A", border: "1px solid #fecaca" },
    success:  { background: "#f0fdf4", color: "#3B6D11", border: "1px solid #bbf7d0" },
    ghost:    { background: "transparent", color: "#666" },
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      style={{ ...base, ...sizes[size], ...variants[variant], ...extraStyle }}>
      {children}
    </button>
  );
}

// ── Modal ─────────────────────────────────────────────────────────────────────
export function Modal({ open, onClose, title, children, width = 480 }) {
  if (!open) return null;
  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#fff", borderRadius: 14, width, maxWidth: "95vw", maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.15)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "18px 22px 14px", borderBottom: "1px solid #f0f0f0" }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: "#111" }}>{title}</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#aaa", padding: 4 }}>
            <X size={18} />
          </button>
        </div>
        <div style={{ padding: "16px 22px 20px" }}>{children}</div>
      </div>
    </div>
  );
}

// ── Form Field ────────────────────────────────────────────────────────────────
export function Field({ label, children, error }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ fontSize: 12, color: "#888", display: "block", marginBottom: 4, fontWeight: 500 }}>{label}</label>}
      {children}
      {error && <div style={{ fontSize: 11, color: "#E24B4A", marginTop: 3 }}>{error}</div>}
    </div>
  );
}

export const inputStyle = {
  width: "100%", padding: "8px 11px",
  border: "1px solid #e0e0e0", borderRadius: 8,
  fontSize: 13, color: "#111", background: "#fff",
  outline: "none", boxSizing: "border-box", fontFamily: "inherit",
};

export const selectStyle = { ...inputStyle };

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ children, color = "blue" }) {
  const colors = {
    blue:   { bg: "#e6f1fb", text: "#185FA5" },
    green:  { bg: "#eaf3de", text: "#3B6D11" },
    amber:  { bg: "#faeeda", text: "#854F0B" },
    red:    { bg: "#fcebeb", text: "#A32D2D" },
    gray:   { bg: "#f1efe8", text: "#5F5E5A" },
    gold:   { bg: "#fdf6e3", text: "#9a7b1c" },
    purple: { bg: "#eeedfe", text: "#534AB7" },
  };
  const c = colors[color] || colors.blue;
  return (
    <span style={{ background: c.bg, color: c.text, padding: "2px 9px", borderRadius: 99, fontSize: 11, fontWeight: 600, display: "inline-block" }}>
      {children}
    </span>
  );
}

// ── Stock Bar ─────────────────────────────────────────────────────────────────
export function StockBar({ stock, reorderPoint }) {
  const pct = Math.min(100, Math.round(stock / Math.max(reorderPoint * 2, 1) * 100));
  const color = stock === 0 ? "#E24B4A" : stock <= reorderPoint ? "#BA7517" : "#639922";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ width: 70, height: 6, background: "#f0f0f0", borderRadius: 99 }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 99 }} />
      </div>
      <span style={{ fontSize: 12, color, fontWeight: 600, minWidth: 24 }}>{stock}</span>
    </div>
  );
}

// ── Loading ───────────────────────────────────────────────────────────────────
export function Loading() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 60, color: "#aaa", gap: 10 }}>
      <div style={{ width: 20, height: 20, border: "2px solid #eee", borderTopColor: "#d4af37", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
      Loading...
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function Empty({ message = "No data found", icon: Icon }) {
  return (
    <div style={{ textAlign: "center", padding: "40px 20px", color: "#aaa" }}>
      {Icon && <Icon size={32} style={{ margin: "0 auto 12px", opacity: 0.4 }} />}
      <div style={{ fontSize: 14 }}>{message}</div>
    </div>
  );
}

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, title, action, style: extra }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #ebebeb", borderRadius: 12, ...extra }}>
      {title && (
        <div style={{ padding: "14px 18px 10px", borderBottom: "1px solid #f5f5f5", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: "#111" }}>{title}</span>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
