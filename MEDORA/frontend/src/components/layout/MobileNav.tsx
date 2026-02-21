import { useNavigate, useLocation } from "react-router-dom";
import { User } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { agents } from "./Sidebar";

export function MobileNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  return (
    <>
      <motion.nav
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[var(--background)]/80 backdrop-blur-lg border-t border-[var(--border)] pb-safe supports-[backdrop-filter]:bg-[var(--background)]/60"
      >
        <div className="flex items-center justify-around h-16 px-2">
          {agents.map(({ to, icon: Icon, short }) => {
            const active = location.pathname === to;
            return (
              <button
                key={to}
                type="button"
                onClick={() => navigate(to)}
                className={cn(
                  "relative flex flex-col items-center justify-center gap-1 min-w-[64px] h-full rounded-xl transition-colors duration-200",
                  active ? "text-[var(--primary)]" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                )}
                aria-label={short}
                aria-current={active ? "page" : undefined}
              >
                {active && (
                  <motion.div
                    layoutId="mobile-nav-pill"
                    className="absolute inset-x-2 top-2 bottom-2 bg-[var(--primary)]/10 rounded-lg -z-10"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className={cn("h-6 w-6", active && "fill-current/10")} strokeWidth={1.5} />
                <span className="text-[10px] font-semibold tracking-wide">{short}</span>
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => navigate(isAuthenticated ? "/profile" : "/login")}
            className={cn(
              "relative flex flex-col items-center justify-center gap-1 min-w-[64px] h-full rounded-xl transition-colors duration-200",
              location.pathname === "/profile" ? "text-[var(--primary)]" : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            )}
            aria-label="Profile"
          >
            {location.pathname === "/profile" && (
              <motion.div
                layoutId="mobile-nav-pill"
                className="absolute inset-x-2 top-2 bottom-2 bg-[var(--primary)]/10 rounded-lg -z-10"
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )}
            <User className={cn("h-6 w-6", location.pathname === "/profile" && "fill-current/10")} strokeWidth={1.5} />
            <span className="text-[10px] font-semibold tracking-wide">Profile</span>
          </button>
        </div>
      </motion.nav>
      {/* Spacer to prevent content from being hidden behind the fixed navbar */}
      <div className="md:hidden h-16 flex-shrink-0" aria-hidden="true" />
    </>
  );
}
