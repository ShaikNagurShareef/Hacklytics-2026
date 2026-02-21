import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Menu, User } from "lucide-react";
import { agents } from "./Sidebar";
import { useAuth } from "@/contexts/AuthContext";

interface HeaderProps {
  agentLabel: string;
  status: "online" | "thinking";
  onMenuClick?: () => void;
}

export function Header({ agentLabel, status, onMenuClick }: HeaderProps) {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const current = agents.find((a) => a.to === location.pathname);

  return (
    <header className="sticky top-0 z-20 h-14 flex-shrink-0 flex items-center justify-between px-4 border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-md supports-[backdrop-filter]:bg-[var(--background)]/60 transition-colors duration-200">
      <div className="flex items-center gap-3 min-w-0">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          onClick={onMenuClick}
          className="md:hidden flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] transition-colors"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" strokeWidth={1.5} />
        </motion.button>
        <div className="min-w-0">
          <motion.h1
            key={current?.label ?? agentLabel}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-[15px] font-semibold text-[var(--foreground)] truncate"
          >
            {current?.label ?? agentLabel}
          </motion.h1>
          <div className="flex items-center gap-1.5 text-[13px] text-[var(--muted-foreground)]">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                status === "online" ? "bg-emerald-500" : "bg-amber-400 animate-pulse"
              )}
              aria-hidden
            />
            <span>{status === "online" ? "Online" : "Thinking…"}</span>
          </div>
        </div>
      </div>
      {isAuthenticated ? (
        <Link
          to="/profile"
          aria-label="Profile"
        >
          <motion.div
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="hidden md:flex h-9 w-9 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
          >
            <User className="h-5 w-5" strokeWidth={1.5} />
          </motion.div>
        </Link>
      ) : (
        <Link
          to="/login"
        >
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="hidden md:flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
          >
            Sign in
          </motion.div>
        </Link>
      )}
    </header>
  );
}
