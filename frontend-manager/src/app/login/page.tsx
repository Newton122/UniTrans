"use client";

import { useState, FormEvent, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthContext } from "@/context/AuthContext";
import styles from "./login.module.css";

/* ──────────────────────────────────────────
   SVG Icons
────────────────────────────────────────── */
const PersonIcon = ({ size = 18, color = "#9ca3af" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="7" r="4" />
    <path d="M4 20c0-4 3.58-7 8-7s8 3 8 7" />
  </svg>
);

const LockIcon = ({ size = 18, color = "#9ca3af" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="5" y="11" width="14" height="10" rx="2" />
    <path d="M8 11V7a4 4 0 0 1 8 0v4" />
  </svg>
);

const EyeIcon = ({ size = 18, color = "#9ca3af" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12S5 5 12 5s11 7 11 7-4 7-11 7S1 12 1 12z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon = ({ size = 18, color = "#9ca3af" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

const ShieldIcon = ({ size = 20, color = "#132a5c" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2L4 6v6c0 5.25 3.5 10.15 8 11.5C16.5 22.15 20 17.25 20 12V6L12 2z" />
  </svg>
);

const BarChartIcon = ({ size = 18, color = "#fff" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <path d="M8 17V13" /><path d="M12 17V9" /><path d="M16 17V11" />
  </svg>
);

const PeopleIcon = ({ size = 18, color = "#fff" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="9" cy="7" r="3" />
    <path d="M2 20c0-3.31 3.13-6 7-6s7 2.69 7 6" />
    <circle cx="17" cy="7" r="2.5" />
    <path d="M22 20c0-2.76-2.24-5-5-5" />
  </svg>
);

const SignInIcon = ({ size = 16, color = "#fff" }: { size?: number; color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    <polyline points="10 17 15 12 10 7" />
    <line x1="15" y1="12" x2="3" y2="12" />
  </svg>
);

/* ──────────────────────────────────────────
   Page
────────────────────────────────────────── */
export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuthContext();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, isLoading, router]);

  const [email, setEmail]             = useState("");
  const [password, setPassword]       = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe]   = useState(false);
  const [error, setError]             = useState("");
  const [loading, setLoading]         = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim())  { setError("Email is required."); return; }
    if (!password)      { setError("Password is required."); return; }
    setLoading(true);
    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("managers only")) {
        setError("Access denied: this portal is for managers only.");
      } else {
        setError("Invalid email or password. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>

      {/* ══ LEFT — full-bleed bus photo + dark gradient overlay ══ */}
      <div className={styles.leftPanel}>
        <div className={styles.leftOverlay} />

        <div className={styles.leftContent}>
          {/* Logo circle */}
          <div className={styles.logoCircle}>
            <img src="/bus-logo.png" alt="UNITRANS" className={styles.logoImg} />
          </div>

          <h1 className={styles.brand}>UNITRANS</h1>
          <p className={styles.brandSub}>Transport Management System</p>
          <div className={styles.brandRule} />
          <h2 className={styles.portalLabel }>Manager Portal</h2>
          <p className={styles.portalDesc}>
            Sign in to access your dashboard and manage transportation operations efficiently.
          </p>

          {/* Three feature badges at the bottom */}
          <div className={styles.badges}>
            <div className={styles.badge}>
              <div className={styles.badgeIcon}><ShieldIcon size={18} color="#fff" /></div>
              <div>
                <div className={styles.badgeTitle}>Secure Access</div>
                <div className={styles.badgeDesc}>Protected login for authorized managers</div>
              </div>
            </div>
            <div className={styles.badge}>
              <div className={styles.badgeIcon}><BarChartIcon size={18} /></div>
              <div>
                <div className={styles.badgeTitle}>Real-time Insights</div>
                <div className={styles.badgeDesc}>Monitor operations and performance instantly</div>
              </div>
            </div>
            <div className={styles.badge}>
              <div className={styles.badgeIcon}><PeopleIcon size={18} /></div>
              <div>
                <div className={styles.badgeTitle}>Efficient Management</div>
                <div className={styles.badgeDesc}>Manage routes, buses, schedules and more</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ══ RIGHT — light gray bg + floating white card ══ */}
      <div className={styles.rightPanel}>
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Welcome Back!</h2>
          <p className={styles.cardSub}>Please sign in to your manager account</p>

          {error && <div className={styles.errorBanner}>{error}</div>}

          <form onSubmit={handleSubmit} className={styles.form}>
            {/* Username */}
            <div className={styles.field}>
              <label className={styles.label} htmlFor="email">Username</label>
              <div className={styles.inputWrap}>
                <span className={styles.inputIcon}><PersonIcon /></span>
                <input
                  id="email" type="email" autoComplete="email"
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  className={styles.input} placeholder="Enter your username"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password */}
            <div className={styles.field}>
              <label className={styles.label} htmlFor="password">Password</label>
              <div className={styles.inputWrap}>
                <span className={styles.inputIcon}><LockIcon /></span>
                <input
                  id="password" type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  className={styles.inputToggle} placeholder="Enter your password"
                  disabled={loading}
                />
                <button
                  type="button" className={styles.eyeBtn}
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1} aria-label={showPassword ? "Hide" : "Show"}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            {/* Remember / Forgot */}
            <div className={styles.row}>
              <label className={styles.checkLabel}>
                <input type="checkbox" checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className={styles.checkbox} />
                Remember me
              </label>
              <Link href="#" className={styles.forgotLink}>Forgot password?</Link>
            </div>

            {/* Sign In */}
            <button type="submit" className={styles.submitBtn} disabled={loading}>
              <SignInIcon />
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          {/* OR */}
          <div className={styles.orRow}>
            <span className={styles.orLine} /><span className={styles.orText}>OR</span><span className={styles.orLine} />
          </div>

          {/* SSO */}
          <button type="button" className={styles.ssoBtn}
            onClick={() => alert("SSO is not yet configured.")}>
            <ShieldIcon size={18} color="#132a5c" />
            Single Sign-On (University Account)
          </button>

          <p className={styles.switchLine}>
            Don&apos;t have an account?{" "}
            <Link href="/register" className={styles.switchLink}>Create Account</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
