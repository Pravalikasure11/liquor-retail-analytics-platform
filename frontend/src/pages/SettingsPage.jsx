import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { authAPI } from "../services/api";
import { useAuthStore } from "../store/authStore";
import { PageHeader, Card, Btn, Field, Modal, Badge, inputStyle } from "../components/ui.jsx";
import { ShieldCheck, ShieldOff, Smartphone, Key, Eye, EyeOff } from "lucide-react";

export function SettingsPage() {
  const qc = useQueryClient();
  const { user } = useAuthStore();
  const [totpModal, setTotpModal] = useState(false);
  const [smsModal, setSmsModal] = useState(false);
  const [qrData, setQrData] = useState(null);
  const [totpCode, setTotpCode] = useState("");
  const [smsPhone, setSmsPhone] = useState("");
  const [smsCode, setSmsCode] = useState("");
  const [smsSent, setSmsSent] = useState(false);
  const [backupCodes, setBackupCodes] = useState(null);

  const { data: me, refetch: refetchMe } = useQuery({
    queryKey: ["me"],
    queryFn: () => authAPI.me().then(r => r.data),
  });

  const setupTOTP = async () => {
    try {
      const res = await authAPI.setupTOTP();
      setQrData(res.data);
      setTotpModal(true);
    } catch (e) { toast.error("Failed to setup TOTP"); }
  };

  const confirmTOTP = async () => {
    try {
      const res = await authAPI.confirmTOTP(totpCode);
      setBackupCodes(res.data.backup_codes);
      toast.success("TOTP MFA enabled!");
      refetchMe();
      setTotpCode("");
    } catch (e) { toast.error(e.response?.data?.detail || "Invalid code"); }
  };

  const setupSMS = async () => {
    try {
      await authAPI.setupSMS(smsPhone);
      setSmsSent(true);
      toast.success("Code sent!");
    } catch (e) { toast.error("Failed to send SMS"); }
  };

  const confirmSMS = async () => {
    try {
      await authAPI.confirmSMS(smsCode);
      toast.success("SMS MFA enabled!");
      refetchMe();
      setSmsModal(false);
      setSmsSent(false);
    } catch (e) { toast.error(e.response?.data?.detail || "Invalid code"); }
  };

  const disableMFA = async () => {
    if (!confirm("Disable MFA? This reduces account security.")) return;
    try {
      await authAPI.disableMFA();
      toast.success("MFA disabled");
      refetchMe();
    } catch (e) { toast.error("Failed"); }
  };

  return (
    <div style={{ flex: 1, overflow: "auto" }}>
      <PageHeader title="Settings" subtitle="Account, security, and system configuration" />

      <div style={{ padding: "16px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Account info */}
        <Card title="Account">
          <div style={{ padding: "12px 18px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {[
                { label: "Username", value: me?.username },
                { label: "Full Name", value: me?.full_name || "—" },
                { label: "Email", value: me?.email },
                { label: "Phone", value: me?.phone || "Not set" },
                { label: "Role", value: me?.is_admin ? "Admin" : "Staff" },
                { label: "Last Login", value: me?.last_login ? new Date(me.last_login).toLocaleString() : "—" },
              ].map(f => (
                <div key={f.label}>
                  <div style={{ fontSize: 11, color: "#aaa", marginBottom: 3 }}>{f.label}</div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{f.value}</div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* MFA */}
        <Card title="Two-Factor Authentication (MFA)">
          <div style={{ padding: "12px 18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              {me?.mfa_enabled ? (
                <><ShieldCheck size={20} color="#639922" />
                  <div>
                    <div style={{ fontWeight: 600 }}>MFA is enabled</div>
                    <div style={{ fontSize: 12, color: "#aaa" }}>Method: {me.mfa_type === "totp" ? "Authenticator app (TOTP)" : "SMS"}</div>
                  </div>
                  <Badge color="green">Active</Badge>
                </>
              ) : (
                <><ShieldOff size={20} color="#E24B4A" />
                  <div>
                    <div style={{ fontWeight: 600 }}>MFA is disabled</div>
                    <div style={{ fontSize: 12, color: "#aaa" }}>Enable MFA to secure your account</div>
                  </div>
                  <Badge color="red">Disabled</Badge>
                </>
              )}
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {!me?.mfa_enabled && (
                <>
                  <Btn variant="gold" onClick={setupTOTP}><Key size={14} /> Enable Authenticator App</Btn>
                  <Btn onClick={() => setSmsModal(true)}><Smartphone size={14} /> Enable SMS MFA</Btn>
                </>
              )}
              {me?.mfa_enabled && (
                <Btn variant="danger" onClick={disableMFA}><ShieldOff size={14} /> Disable MFA</Btn>
              )}
            </div>
          </div>
        </Card>

        {/* Supplier credentials info */}
        <Card title="Supplier Portal Configuration">
          <div style={{ padding: "12px 18px" }}>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 12 }}>
              Configure supplier login credentials to enable automatic deal monitoring. Credentials are stored securely and used only to fetch promotions from supplier portals.
            </p>
            <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, padding: "12px 14px", fontSize: 13, color: "#92400e" }}>
              <strong>Supported portals:</strong> Breakthru Beverage, RNDC, Southern Glazer's, and custom URLs.
              To configure, go to Suppliers → Edit Supplier → enter portal credentials.
            </div>
          </div>
        </Card>

        {/* System info */}
        <Card title="System Information">
          <div style={{ padding: "12px 18px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {[
              { label: "App Version", value: "1.0.0" },
              { label: "Database", value: "PostgreSQL (Railway)" },
              { label: "Storage", value: "Cloud (Railway)" },
              { label: "Auth", value: "JWT + MFA" },
            ].map(f => (
              <div key={f.label} style={{ background: "#fafafa", borderRadius: 8, padding: "10px 12px" }}>
                <div style={{ fontSize: 11, color: "#aaa", marginBottom: 2 }}>{f.label}</div>
                <div style={{ fontWeight: 500, fontSize: 13 }}>{f.value}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* TOTP Setup Modal */}
      <Modal open={totpModal} onClose={() => { setTotpModal(false); setQrData(null); setBackupCodes(null); setTotpCode(""); }} title="Set Up Authenticator App" width={420}>
        {!backupCodes ? (
          <>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 16 }}>
              Scan this QR code with Google Authenticator or Authy, then enter the 6-digit code to confirm.
            </p>
            {qrData?.qr_code && (
              <div style={{ textAlign: "center", marginBottom: 16 }}>
                <img src={qrData.qr_code} alt="TOTP QR Code" style={{ width: 200, height: 200, border: "1px solid #f0f0f0", borderRadius: 8 }} />
                <div style={{ fontSize: 11, color: "#aaa", marginTop: 8, fontFamily: "monospace", wordBreak: "break-all" }}>{qrData.secret}</div>
              </div>
            )}
            <Field label="Enter 6-digit code from app">
              <input style={{ ...inputStyle, textAlign: "center", letterSpacing: 6, fontSize: 18 }}
                placeholder="000000" maxLength={6} value={totpCode}
                onChange={e => setTotpCode(e.target.value)} />
            </Field>
            <Btn variant="gold" onClick={confirmTOTP} style={{ marginTop: 8 }}>Verify & Enable</Btn>
          </>
        ) : (
          <>
            <div style={{ background: "#f8fdf4", border: "1px solid #d4edda", borderRadius: 8, padding: 14, marginBottom: 16 }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: "#3B6D11" }}>✓ TOTP MFA Enabled!</div>
              <p style={{ fontSize: 13, color: "#888", marginBottom: 12 }}>
                Save these backup codes. Each can be used once if you lose access to your authenticator app.
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                {backupCodes.map((c, i) => (
                  <code key={i} style={{ background: "#fff", border: "1px solid #d4edda", borderRadius: 6, padding: "4px 10px", fontSize: 13, fontFamily: "monospace" }}>{c}</code>
                ))}
              </div>
            </div>
            <Btn variant="gold" onClick={() => { setTotpModal(false); setBackupCodes(null); }}>Done</Btn>
          </>
        )}
      </Modal>

      {/* SMS Setup Modal */}
      <Modal open={smsModal} onClose={() => { setSmsModal(false); setSmsSent(false); }} title="Set Up SMS MFA" width={380}>
        {!smsSent ? (
          <>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 14 }}>Enter your phone number to receive a verification code.</p>
            <Field label="Phone number (with country code)">
              <input style={inputStyle} placeholder="+1 555 000 0000" value={smsPhone} onChange={e => setSmsPhone(e.target.value)} />
            </Field>
            <Btn variant="gold" onClick={setupSMS} style={{ marginTop: 8 }}>Send Code</Btn>
          </>
        ) : (
          <>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 14 }}>Enter the 6-digit code sent to {smsPhone}.</p>
            <Field label="Verification code">
              <input style={{ ...inputStyle, textAlign: "center", letterSpacing: 6, fontSize: 18 }}
                placeholder="000000" maxLength={6} value={smsCode} onChange={e => setSmsCode(e.target.value)} />
            </Field>
            <Btn variant="gold" onClick={confirmSMS} style={{ marginTop: 8 }}>Verify & Enable</Btn>
          </>
        )}
      </Modal>
    </div>
  );
}

export default SettingsPage;
