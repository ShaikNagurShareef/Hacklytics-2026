import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Stethoscope, Mail, Lock, User, ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

export function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signUp, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/virtual-doctor";

  if (isAuthenticated) {
    navigate(from, { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signUp(email, password, fullName.trim() || undefined);
      navigate(from, { replace: true });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Sign up failed. Please try again.";
      const safe = typeof msg === "string" && msg.length > 1 && !/^[\s\[\]{},:]+$/.test(msg)
        ? msg
        : "Sign up failed. Please try again.";
      setError(safe);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[var(--background)]">
      <div className="hidden md:flex md:w-1/2 bg-gradient-to-br from-teal-800 to-[var(--primary)] p-12 flex-col justify-between text-white">
        <div className="flex items-center gap-2">
          <Stethoscope className="h-8 w-8" strokeWidth={1.5} />
          <span className="text-xl font-semibold tracking-tight">MEDORA</span>
        </div>
        <div>
          <h2 className="text-3xl font-semibold leading-tight mb-3">
            Start your wellness journey today.
          </h2>
          <p className="text-white/80 text-lg max-w-sm">
            Create an account to save your conversations and get personalised health insights.
          </p>
        </div>
        <p className="text-sm text-white/60">Your data stays private and secure.</p>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 md:p-12">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-[400px]"
        >
          <div className="md:hidden flex items-center gap-2 mb-8 text-[var(--primary)]">
            <Stethoscope className="h-7 w-7" strokeWidth={1.5} />
            <span className="text-lg font-semibold tracking-tight">MEDORA</span>
          </div>

          <h1 className="text-2xl font-semibold text-[var(--foreground)] mb-1">Create an account</h1>
          <p className="text-[var(--muted-foreground)] mb-8">Enter your details to get started.</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div
                className={cn(
                  "rounded-xl px-4 py-3 text-sm",
                  "bg-red-50 text-red-800 dark:bg-red-950/40 dark:text-red-300"
                )}
                role="alert"
              >
                {error}
              </div>
            )}

            <div>
              <label htmlFor="signup-name" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
                Full name (optional)
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" strokeWidth={1.5} />
                <input
                  id="signup-name"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full h-12 pl-10 pr-4 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent transition-shadow"
                  placeholder="Jane Doe"
                />
              </div>
            </div>

            <div>
              <label htmlFor="signup-email" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" strokeWidth={1.5} />
                <input
                  id="signup-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full h-12 pl-10 pr-4 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent transition-shadow"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" strokeWidth={1.5} />
                <input
                  id="signup-password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full h-12 pl-10 pr-4 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent transition-shadow"
                  placeholder="At least 6 characters"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={cn(
                "w-full h-12 rounded-xl font-medium flex items-center justify-center gap-2 transition-all",
                "bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-95 active:scale-[0.99]",
                "disabled:opacity-60 disabled:pointer-events-none"
              )}
            >
              {loading ? (
                <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <>
                  Create account
                  <ArrowRight className="h-4 w-4" strokeWidth={2} />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-[var(--muted-foreground)]">
            Already have an account?{" "}
            <Link to="/login" className="text-[var(--primary)] font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
