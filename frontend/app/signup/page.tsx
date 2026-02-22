"use client";

import { useState } from "react";
import { signUp, signIn } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Eye, EyeOff, AlertTriangle, Lock, Mail, User } from "lucide-react";
import Link from "next/link";

export default function SignUpPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      setLoading(false);
      return;
    }

    const { error } = await signUp.email({ name, email, password });
    if (error) {
      setError(error.message || "Registration failed. Please try again.");
      setLoading(false);
    } else {
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-accent-blue/20"
            style={{
              left: `${(i * 5) % 100}%`,
              top: `${(i * 7) % 100}%`,
            }}
            animate={{
              y: [0, -100 - Math.random() * 100],
              opacity: [0, 0.5, 0],
            }}
            transition={{
              duration: 4 + Math.random() * 4,
              repeat: Infinity,
              delay: Math.random() * 3,
            }}
          />
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md px-6 relative z-10"
      >
        {/* Logo */}
        <motion.div
          className="flex flex-col items-center mb-8"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="relative mb-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 w-20 h-20"
            >
              <svg viewBox="0 0 80 80" className="w-20 h-20">
                <polygon
                  points="40,4 72,22 72,58 40,76 8,58 8,22"
                  fill="none"
                  stroke="rgba(68,136,255,0.2)"
                  strokeWidth="1"
                />
              </svg>
            </motion.div>
            <div className="w-20 h-20 flex items-center justify-center">
              <svg viewBox="0 0 80 80" className="w-16 h-16">
                <defs>
                  <linearGradient id="hex-grad-signup" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#00ff88" />
                    <stop offset="100%" stopColor="#4488ff" />
                  </linearGradient>
                </defs>
                <polygon
                  points="40,8 68,24 68,56 40,72 12,56 12,24"
                  fill="url(#hex-grad-signup)"
                  opacity="0.9"
                />
                <text x="40" y="46" textAnchor="middle" fill="white" fontSize="18" fontWeight="bold">S</text>
              </svg>
            </div>
          </div>
          <h1 className="font-[var(--font-syne)] text-4xl font-extrabold tracking-wider text-text">
            STREAM
          </h1>
          <p className="text-muted text-sm tracking-[0.3em] mt-1 uppercase">
            Anti-Corruption Intelligence Engine
          </p>
        </motion.div>

        {/* Signup Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bg-surface/80 backdrop-blur-xl border border-border rounded-2xl p-8 shadow-2xl"
        >
          <h2 className="font-[var(--font-syne)] text-xl font-bold text-text mb-1">
            Create your STREAM account
          </h2>
          <p className="text-muted text-sm mb-6">
            Request access to the procurement intelligence platform.
          </p>

          {error && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 bg-accent-red/10 border border-accent-red/30 rounded-lg px-4 py-3 mb-4"
            >
              <AlertTriangle size={16} className="text-accent-red flex-shrink-0" />
              <span className="text-accent-red text-sm">{error}</span>
            </motion.div>
          )}

          {/* Google Sign Up */}
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={async () => {
              setLoading(true);
              setError("");
              await signIn.social({ provider: "google", callbackURL: "/dashboard" });
            }}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 bg-bg border border-border rounded-lg py-3 text-text hover:border-border/80 hover:bg-surface2/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed mb-5"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="font-[var(--font-syne)] font-semibold text-sm">Sign up with Google</span>
          </motion.button>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex-1 h-px bg-border" />
            <span className="text-muted/50 text-[10px] uppercase tracking-widest font-[var(--font-syne)]">or with email</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-muted text-xs uppercase tracking-wider mb-2 block">
                Full Name
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-bg border border-border rounded-lg pl-10 pr-4 py-3 text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-all font-[var(--font-space-mono)] text-sm"
                  placeholder="Nitheesh Kumar"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-muted text-xs uppercase tracking-wider mb-2 block">
                Email Address
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-bg border border-border rounded-lg pl-10 pr-4 py-3 text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-all font-[var(--font-space-mono)] text-sm"
                  placeholder="analyst@stream.gov.in"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-muted text-xs uppercase tracking-wider mb-2 block">
                Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-bg border border-border rounded-lg pl-10 pr-12 py-3 text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-all font-[var(--font-space-mono)] text-sm"
                  placeholder="Min. 8 characters"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-muted text-xs uppercase tracking-wider mb-2 block">
                Confirm Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-bg border border-border rounded-lg pl-10 pr-4 py-3 text-text placeholder:text-muted/50 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-all font-[var(--font-space-mono)] text-sm"
                  placeholder="Repeat password"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="w-full bg-accent-blue/10 border border-accent-blue/30 text-accent-blue font-[var(--font-syne)] font-bold py-3 rounded-lg hover:bg-accent-blue/20 hover:border-accent-blue/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-accent-blue/30 border-t-accent-blue rounded-full animate-spin" />
              ) : (
                <>
                  <Shield size={16} />
                  Create Account
                </>
              )}
            </motion.button>
          </form>

          <div className="mt-5 pt-4 border-t border-border text-center">
            <p className="text-muted text-sm">
              Already have an account?{" "}
              <Link href="/login" className="text-accent-green hover:text-accent-green/80 font-[var(--font-syne)] font-bold transition-colors">
                Sign In
              </Link>
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center mt-6"
        >
          <p className="text-muted/40 text-xs font-[var(--font-space-mono)]">
            AES-256 Encrypted · Session Monitored · Audit Logged
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
