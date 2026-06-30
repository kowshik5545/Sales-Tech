import { useState, type FormEvent } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      if (msg.toLowerCase().includes("401") || msg.toLowerCase().includes("invalid")) {
        setError("Invalid email or password");
      } else {
        setError(msg);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f5f5f5",
      fontFamily: '"Segoe UI", system-ui, sans-serif',
    }}>
      <div style={{
        background: "#ffffff",
        borderRadius: 16,
        boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
        padding: 48,
        width: 400,
        maxWidth: "90vw",
      }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: "#7c3aed", color: "#fff",
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            fontSize: 28, marginBottom: 16,
          }}>
            {"\uD83D\uDCDE"}
          </div>
          <h1 style={{
            fontSize: 22, fontWeight: 700, color: "#1a1a2e",
            margin: "0 0 6px", letterSpacing: "-0.02em",
          }}>
            Sales Rep Assistant
          </h1>
          <p style={{ fontSize: 14, color: "#64748b", margin: 0 }}>
            Sign in to continue
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 18 }}>
            <label style={{
              display: "block", fontSize: 13, fontWeight: 600,
              color: "#475569", marginBottom: 6,
            }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
              style={{
                width: "100%", padding: "11px 14px",
                fontSize: 14, fontFamily: "inherit",
                border: "1px solid #e5e7eb", borderRadius: 8,
                outline: "none", boxSizing: "border-box",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => { e.target.style.borderColor = "#7c3aed"; }}
              onBlur={(e) => { e.target.style.borderColor = "#e5e7eb"; }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{
              display: "block", fontSize: 13, fontWeight: 600,
              color: "#475569", marginBottom: 6,
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              style={{
                width: "100%", padding: "11px 14px",
                fontSize: 14, fontFamily: "inherit",
                border: "1px solid #e5e7eb", borderRadius: 8,
                outline: "none", boxSizing: "border-box",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => { e.target.style.borderColor = "#7c3aed"; }}
              onBlur={(e) => { e.target.style.borderColor = "#e5e7eb"; }}
            />
          </div>

          {error && (
            <div style={{
              padding: "10px 14px", background: "#fee2e2",
              border: "1px solid #ef4444", borderRadius: 8,
              color: "#ef4444", fontSize: 13, marginBottom: 16,
              lineHeight: 1.5,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            style={{
              width: "100%", padding: "12px 20px",
              fontSize: 15, fontWeight: 600, fontFamily: "inherit",
              background: busy ? "#a78bfa" : "#7c3aed",
              color: "#ffffff", border: "none", borderRadius: 8,
              cursor: busy ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => { if (!busy) e.currentTarget.style.background = "#6d28d9"; }}
            onMouseLeave={(e) => { if (!busy) e.currentTarget.style.background = "#7c3aed"; }}
          >
            {busy ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={{
          marginTop: 28, padding: 16,
          background: "#f8fafc", borderRadius: 10,
          fontSize: 12, color: "#64748b", lineHeight: 1.6,
        }}>
          <strong style={{ color: "#475569" }}>Demo Accounts:</strong><br />
          admin@example.com / admin123<br />
          manager@example.com / manager123<br />
          rep1@example.com / rep123<br />
          rep2@example.com / rep123
        </div>
      </div>
    </div>
  );
}
