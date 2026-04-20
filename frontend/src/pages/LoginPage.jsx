import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { authAPI } from "../services/api";
import { useAuthStore } from "../store/authStore";
import { Store, Eye, EyeOff, ShieldCheck } from "lucide-react";

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [step, setStep] = useState("credentials"); // "credentials" | "mfa"
  const [mfaType, setMfaType] = useState("");
  const [tempToken, setTempToken] = useState("");
  const [form, setForm] = useState({ username: "", password: "", mfaCode: "" });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authAPI.login({ username: form.username, password: form.password });
      const data = res.data;
      if (data.mfa_required) {
        setTempToken(data.temp_token);
        setMfaType(data.mfa_type);
        setStep("mfa");
        toast.success(data.mfa_type === "sms" ? "SMS code sent!" : "Enter your authenticator code");
      } else {
        setAuth(data.access_token, data.user);
        toast.success(`Welcome back, ${data.user.full_name || data.user.username}!`);
        navigate("/dashboard");
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleMFA = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authAPI.verifyMFA({ temp_token: tempToken, code: form.mfaCode, method: mfaType });
      const data = res.data;
      setAuth(data.access_token, data.user);
      toast.success("Verified! Welcome back.");
      navigate("/dashboard");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Invalid code");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%", padding: "10px 12px",
    background: "#1a1a18", border: "1px solid #2a2a28",
    borderRadius: 8, color: "#f0f0ee", fontSize: 14,
    outline: "none", boxSizing: "border-box",
  };

  const btnStyle = {
    width: "100%", padding: "11px",
    background: "#d4af37", border: "none", borderRadius: 8,
    color: "#111", fontWeight: 700, fontSize: 14, cursor: "pointer",
    opacity: loading ? 0.7 : 1,
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0e0e0c", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "system-ui, sans-serif" }}>
      <div style={{ width: 360, padding: "36px 32px", background: "#141412", border: "1px solid #222", borderRadius: 16 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ width: 52, height: 52, background: "#d4af37", borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
            <Store size={26} color="#111" />
          </div>
          <div style={{ color: "#f0f0ee", fontWeight: 700, fontSize: 20 }}>Zach's Liquor Store</div>
          <div style={{ color: "#666", fontSize: 13, marginTop: 4 }}>Inventory Management System</div>
        </div>

        {step === "credentials" ? (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, color: "#888", display: "block", marginBottom: 5 }}>Username</label>
              <input style={inputStyle} placeholder="username" value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, color: "#888", display: "block", marginBottom: 5 }}>Password</label>
              <div style={{ position: "relative" }}>
                <input style={{ ...inputStyle, paddingRight: 40 }} type={showPw ? "text" : "password"}
                  placeholder="password" value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "#666", cursor: "pointer" }}>
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            <button type="submit" style={btnStyle} disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleMFA}>
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <ShieldCheck size={36} color="#d4af37" style={{ margin: "0 auto 8px" }} />
              <div style={{ color: "#f0f0ee", fontWeight: 600 }}>Two-Factor Authentication</div>
              <div style={{ color: "#666", fontSize: 13, marginTop: 4 }}>
                {mfaType === "sms" ? "Enter the SMS code sent to your phone" : "Enter the code from your authenticator app"}
              </div>
            </div>
            <div style={{ marginBottom: 20 }}>
              <input style={{ ...inputStyle, textAlign: "center", letterSpacing: 6, fontSize: 18 }}
                placeholder="000000" maxLength={8} value={form.mfaCode}
                onChange={e => setForm(f => ({ ...f, mfaCode: e.target.value }))}
                autoFocus required />
            </div>
            <button type="submit" style={btnStyle} disabled={loading}>
              {loading ? "Verifying..." : "Verify"}
            </button>
            <button type="button" onClick={() => setStep("credentials")}
              style={{ ...btnStyle, background: "transparent", color: "#666", marginTop: 8, border: "1px solid #333" }}>
              Back to login
            </button>
          </form>
        )}

        <div style={{ marginTop: 20, padding: "12px", background: "#1a1a18", borderRadius: 8, fontSize: 12, color: "#555" }}>
          <div>Demo: <span style={{ color: "#888" }}>zach / Zach1234!</span></div>
          <div>Staff: <span style={{ color: "#888" }}>staff / Staff123!</span></div>
        </div>
      </div>
    </div>
  );
}
