import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { dealsAPI, productsAPI } from "../../services/api";
import {
  LayoutDashboard, Package, ShoppingCart, Receipt, BarChart3,
  Calendar, Bell, Tag, Settings, LogOut, Store, Wifi,
  Truck, Megaphone, Search, X
} from "lucide-react";

const NAV = [
  { to: "/dashboard",   label: "Dashboard",        icon: LayoutDashboard },
  { to: "/inventory",   label: "Inventory",         icon: Package },
  { to: "/sales",       label: "Sales",             icon: ShoppingCart },
  { to: "/expenses",    label: "Expenses",          icon: Receipt },
  { section: "Analytics" },
  { to: "/analytics",   label: "Sales Analytics",   icon: BarChart3 },
  { to: "/seasonal",    label: "Seasonal",          icon: Calendar },
  { section: "Store" },
  { to: "/promotions",  label: "In-Store Promotions", icon: Megaphone },
  { to: "/alerts",      label: "Stock Alerts",      icon: Bell, badge: "alerts" },
  { to: "/deals",       label: "Supplier Deals",    icon: Tag,  badge: "deals" },
  { to: "/suppliers",   label: "Suppliers",         icon: Truck },
  { section: "Account" },
  { to: "/settings",    label: "Settings",          icon: Settings },
];

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState("");

  const { data: dealsData } = useQuery({
    queryKey: ["deals-unread"],
    queryFn: () => dealsAPI.unreadCount().then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: searchResults } = useQuery({
    queryKey: ["search", searchQ],
    queryFn: () => productsAPI.list({ search: searchQ }).then(r => r.data),
    enabled: searchQ.length >= 2,
  });

  const handleLogout = () => { logout(); navigate("/login"); };

  const openSearch = () => { setSearchOpen(true); setSearchQ(""); };
  const closeSearch = () => { setSearchOpen(false); setSearchQ(""); };

  const goToProduct = () => {
    navigate("/inventory?search=" + encodeURIComponent(searchQ));
    closeSearch();
  };

  return (
    <div style={{ display:"flex", height:"100vh", fontFamily:"'Inter', system-ui, sans-serif", background:"#f8f8f6" }}>

      {/* Sidebar */}
      <aside style={{ width:220, flexShrink:0, background:"#111110", color:"#e8e0d0", display:"flex", flexDirection:"column", borderRight:"1px solid #222" }}>
        {/* Logo */}
        <div style={{ padding:"20px 16px 14px", borderBottom:"1px solid #222" }}>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <div style={{ width:32, height:32, background:"#d4af37", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center" }}>
              <Store size={18} color="#111" />
            </div>
            <div>
              <div style={{ fontWeight:600, fontSize:14, color:"#f0f0ee" }}>Zach's Liquor</div>
              <div style={{ fontSize:11, color:"#555", display:"flex", alignItems:"center", gap:3 }}>
                <Wifi size={10} color="#4caf80"/> Connected
              </div>
            </div>
          </div>
        </div>

        {/* Global Search button */}
        <div style={{ padding:"10px 10px 4px" }}>
          <button onClick={openSearch} style={{
            width:"100%", display:"flex", alignItems:"center", gap:8, padding:"7px 10px",
            background:"#1a1a18", border:"1px solid #2a2a28", borderRadius:8,
            color:"#666", fontSize:12, cursor:"pointer",
          }}>
            <Search size={13}/> Search products...
            <span style={{ marginLeft:"auto", fontSize:10, color:"#444" }}>⌘K</span>
          </button>
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:"4px 8px", overflowY:"auto" }}>
          {NAV.map((item, i) => {
            if (item.section) return (
              <div key={i} style={{ padding:"12px 8px 4px", fontSize:10, fontWeight:600, color:"#444", textTransform:"uppercase", letterSpacing:"0.08em" }}>
                {item.section}
              </div>
            );
            const Icon = item.icon;
            const badgeCount = item.badge === "deals" ? dealsData?.count : null;
            return (
              <NavLink key={item.to} to={item.to} style={({ isActive }) => ({
                display:"flex", alignItems:"center", gap:9, padding:"7px 10px",
                borderRadius:8, textDecoration:"none", fontSize:13, marginBottom:1,
                background: isActive ? "#1e1e1c" : "transparent",
                color: isActive ? "#d4af37" : "#888",
                transition:"all 0.1s",
              })}>
                <Icon size={15}/>
                <span style={{ flex:1 }}>{item.label}</span>
                {badgeCount > 0 && (
                  <span style={{ background:"#E24B4A", color:"#fff", borderRadius:99, fontSize:10, padding:"1px 6px", fontWeight:600 }}>
                    {badgeCount}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User */}
        <div style={{ padding:"12px", borderTop:"1px solid #222" }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8 }}>
            <div style={{ width:28, height:28, background:"#d4af37", borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, fontWeight:700, color:"#111" }}>
              {user?.username?.[0]?.toUpperCase() || "Z"}
            </div>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize:12, fontWeight:500, color:"#ddd", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{user?.full_name || user?.username}</div>
              <div style={{ fontSize:10, color:"#555" }}>{user?.is_admin ? "Admin" : "Staff"}</div>
            </div>
          </div>
          <button onClick={handleLogout} style={{ width:"100%", display:"flex", alignItems:"center", gap:8, padding:"6px 8px", background:"none", border:"none", color:"#666", fontSize:12, cursor:"pointer", borderRadius:6 }}>
            <LogOut size={13}/> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex:1, overflow:"auto", display:"flex", flexDirection:"column" }}>
        <Outlet />
      </main>

      {/* Global Search Modal */}
      {searchOpen && (
        <div onClick={closeSearch} style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000, display:"flex", alignItems:"flex-start", justifyContent:"center", paddingTop:80 }}>
          <div onClick={e => e.stopPropagation()} style={{ width:520, background:"#fff", borderRadius:14, boxShadow:"0 20px 60px rgba(0,0,0,0.2)", overflow:"hidden" }}>
            {/* Search input */}
            <div style={{ display:"flex", alignItems:"center", gap:10, padding:"14px 18px", borderBottom:"1px solid #f0f0f0" }}>
              <Search size={18} color="#aaa"/>
              <input
                autoFocus
                style={{ flex:1, border:"none", outline:"none", fontSize:16, color:"#111", fontFamily:"inherit" }}
                placeholder="Search products by name, SKU, category..."
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && searchQ) goToProduct(); if (e.key === "Escape") closeSearch(); }}
              />
              <button onClick={closeSearch} style={{ background:"none", border:"none", cursor:"pointer", color:"#aaa" }}>
                <X size={18}/>
              </button>
            </div>

            {/* Results */}
            <div style={{ maxHeight:380, overflowY:"auto" }}>
              {searchQ.length < 2 ? (
                <div style={{ padding:"20px 18px", color:"#aaa", fontSize:13, textAlign:"center" }}>Type at least 2 characters to search</div>
              ) : !searchResults || searchResults.length === 0 ? (
                <div style={{ padding:"20px 18px", color:"#aaa", fontSize:13, textAlign:"center" }}>No products found for "{searchQ}"</div>
              ) : (
                <>
                  <div style={{ padding:"8px 18px 4px", fontSize:11, color:"#aaa", textTransform:"uppercase", letterSpacing:"0.05em" }}>
                    {searchResults.length} product{searchResults.length !== 1 ? "s" : ""} found
                  </div>
                  {searchResults.map(p => {
                    const stockColor = p.stock === 0 ? "#E24B4A" : p.stock <= p.reorder_point ? "#BA7517" : "#639922";
                    return (
                      <div key={p.id}
                        onClick={() => { navigate("/inventory"); closeSearch(); }}
                        style={{ padding:"10px 18px", borderBottom:"1px solid #f8f8f8", cursor:"pointer", display:"flex", alignItems:"center", gap:12 }}
                        onMouseEnter={e => e.currentTarget.style.background = "#fafafa"}
                        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                      >
                        <div style={{ width:36, height:36, background:"#f5f5f3", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, flexShrink:0 }}>
                          {p.category === "Beer" ? "🍺" : p.category === "Wine" ? "🍷" : p.category === "Hard Liquor" ? "🥃" : p.category === "Cigarettes" ? "🚬" : p.category === "Snacks & Chips" ? "🍿" : "📦"}
                        </div>
                        <div style={{ flex:1, minWidth:0 }}>
                          <div style={{ fontWeight:600, fontSize:13, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{p.name}</div>
                          <div style={{ fontSize:11, color:"#aaa" }}>{p.category} · {p.sku} · ${p.sell_price}</div>
                        </div>
                        <div style={{ textAlign:"right", flexShrink:0 }}>
                          <div style={{ fontSize:13, fontWeight:700, color:stockColor }}>{p.stock} in stock</div>
                          <div style={{ fontSize:11, color:"#aaa" }}>{Math.round((p.sell_price - p.cost_price) / p.sell_price * 100)}% margin</div>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}
            </div>

            {searchQ && (
              <div style={{ padding:"10px 18px", borderTop:"1px solid #f0f0f0", display:"flex", justifyContent:"flex-end" }}>
                <button onClick={goToProduct} style={{ background:"#111", color:"#fff", border:"none", borderRadius:8, padding:"7px 14px", fontSize:12, cursor:"pointer", fontFamily:"inherit" }}>
                  View all results in Inventory →
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
