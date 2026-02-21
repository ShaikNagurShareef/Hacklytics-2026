import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  Heart,
  Stethoscope,
  UtensilsCrossed,
  PanelLeftClose,
  PanelLeft,
  Plus,
  Sun,
  Moon,
  LogOut,
  MessageCircle,
  ScanLine,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChats } from "@/api/client";
import type { ChatSessionListItem } from "@/api/types";

const SIDEBAR_WIDTH = 220;

export const agents = [
  { to: "/ask", label: "Ask MEDORA", short: "Ask", icon: MessageCircle },
  { to: "/virtual-doctor", label: "Virtual Doctor", short: "Doctor", icon: Stethoscope },
  { to: "/dietary", label: "Dietary", short: "Dietary", icon: UtensilsCrossed },
  { to: "/wellbeing", label: "Wellbeing", short: "Wellbeing", icon: Heart },
  { to: "/diagnostic", label: "Diagnostics", short: "Dx", icon: ScanLine },
] as const;

function agentTypeToPath(agentType: string | null): string {
  if (!agentType) return "/ask";
  const m: Record<string, string> = {
    ask: "/ask",
    "virtual-doctor": "/virtual-doctor",
    dietary: "/dietary",
    wellbeing: "/wellbeing",
    diagnostic: "/diagnostic",
  };
  return m[agentType] ?? "/ask";
}

function agentTypeIcon(agentType: string | null) {
  switch (agentType) {
    case "virtual-doctor": return Stethoscope;
    case "dietary": return UtensilsCrossed;
    case "wellbeing": return Heart;
    case "diagnostic": return ScanLine;
    default: return MessageCircle;
  }
}

function agentTypeColor(agentType: string | null): string {
  switch (agentType) {
    case "virtual-doctor": return "text-teal-500";
    case "dietary": return "text-amber-500";
    case "wellbeing": return "text-rose-500";
    case "diagnostic": return "text-violet-500";
    default: return "text-[var(--primary)]";
  }
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ collapsed, onToggle, mobileOpen = false, onMobileClose }: SidebarProps) {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const s = localStorage.getItem("medora-theme");
    if (s === "dark" || s === "light") return s === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const [recentChats, setRecentChats] = useState<ChatSessionListItem[]>([]);
  const [chatsLoading, setChatsLoading] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("medora-theme", dark ? "dark" : "light");
  }, [dark]);

  // Fetch recent chats when authenticated, and refresh on route changes
  useEffect(() => {
    if (!isAuthenticated) {
      setRecentChats([]);
      return;
    }
    setChatsLoading(true);
    getMyChats()
      .then((chats) => setRecentChats(chats.slice(0, 10))) // show latest 10
      .catch(() => setRecentChats([]))
      .finally(() => setChatsLoading(false));
  }, [isAuthenticated, location.pathname]);

  const sidebarContent = (
    <div className="flex flex-col h-full min-w-[220px]">
      <div className="p-4 flex items-center justify-between">
        <Link
          to="/ask"
          onClick={() => onMobileClose?.()}
          className="text-[18px] font-semibold text-[var(--sidebar-foreground)] tracking-tight hover:opacity-80 transition-opacity"
        >
          MEDORA
        </Link>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          onClick={onToggle}
          className="hidden md:block p-1.5 rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose className="h-4 w-4" strokeWidth={1.5} />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          onClick={() => onMobileClose?.()}
          className="md:hidden p-1.5 rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
          aria-label="Close menu"
        >
          <PanelLeftClose className="h-4 w-4" strokeWidth={1.5} />
        </motion.button>
      </div>

      <div className="px-3 pb-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          type="button"
          className="w-full flex items-center justify-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--background)] py-2.5 text-[13px] font-medium text-[var(--foreground)] hover:bg-[var(--hover)] hover:border-[var(--primary)]/30 transition-all shadow-sm hover:shadow-md"
        >
          <Plus className="h-4 w-4" strokeWidth={1.5} />
          <span>New chat</span>
        </motion.button>
      </div>

      <div className="px-2 flex-1 overflow-y-auto scrollbar-thin">
        <p className="px-2 text-[11px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
          Agent
        </p>
        <nav className="space-y-1">
          {agents.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                onClick={() => onMobileClose?.()}
                className={cn(
                  "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-medium transition-colors duration-200 group overflow-hidden",
                  active
                    ? "text-[var(--primary)] bg-[var(--active)]"
                    : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--hover)]"
                )}
              >
                {active && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 bg-[var(--primary)]/5 border-l-2 border-[var(--primary)]"
                    initial={false}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <Icon className={cn("h-4 w-4 shrink-0 relative z-10", active && "text-[var(--primary)]")} strokeWidth={1.5} />
                <span className="relative z-10">{label}</span>
              </Link>
            );
          })}
        </nav>

        <p className="px-2 mt-6 text-[11px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
          Recent
        </p>

        {/* Recent chat history */}
        {!isAuthenticated ? (
          <div className="px-2 py-6 flex flex-col items-center justify-center text-center opacity-50">
            <MessageCircle className="h-7 w-7 text-[var(--muted-foreground)] mb-2" strokeWidth={1} />
            <p className="text-[12px] text-[var(--muted-foreground)]">
              Sign in to see history
            </p>
          </div>
        ) : chatsLoading ? (
          <div className="px-2 py-6 flex flex-col items-center justify-center text-center opacity-50">
            <div className="h-5 w-5 border-2 border-[var(--primary)]/30 border-t-[var(--primary)] rounded-full animate-spin mb-2"></div>
            <p className="text-[12px] text-[var(--muted-foreground)]">Loading…</p>
          </div>
        ) : recentChats.length === 0 ? (
          <div className="px-2 py-6 flex flex-col items-center justify-center text-center opacity-50">
            <MessageCircle className="h-7 w-7 text-[var(--muted-foreground)] mb-2" strokeWidth={1} />
            <p className="text-[12px] text-[var(--muted-foreground)]">
              Start a conversation with MEDORA
            </p>
          </div>
        ) : (
          <nav className="space-y-0.5">
            {recentChats.map((chat) => {
              const ChatIcon = agentTypeIcon(chat.agent_type);
              const iconColor = agentTypeColor(chat.agent_type);
              const chatPath = `${agentTypeToPath(chat.agent_type)}?session=${encodeURIComponent(chat.client_session_id)}`;
              return (
                <Link
                  key={chat.id}
                  to={chatPath}
                  onClick={() => onMobileClose?.()}
                  className={cn(
                    "flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] transition-colors duration-150 group",
                    "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--hover)]"
                  )}
                  title={chat.title || "New chat"}
                >
                  <ChatIcon className={cn("h-3.5 w-3.5 shrink-0", iconColor)} strokeWidth={1.5} />
                  <span className="flex-1 truncate">{chat.title || "New chat"}</span>
                </Link>
              );
            })}
          </nav>
        )}
      </div>

      <div className="p-3 border-t border-[var(--sidebar-border)] flex items-center gap-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--primary)]/60 text-white text-xs font-medium shadow-sm">
          {user ? (user.full_name?.trim() ? user.full_name.trim().slice(0, 2).toUpperCase() : user.email.slice(0, 2).toUpperCase()) : "?"}
        </div>
        <Link
          to={isAuthenticated ? "/profile" : "/login"}
          onClick={() => onMobileClose?.()}
          className="flex-1 min-w-0 flex flex-col"
        >
          <span className="text-[13px] font-medium text-[var(--foreground)] truncate group-hover:text-[var(--primary)] transition-colors">
            {isAuthenticated ? (user?.full_name?.trim() || "User") : "Guest User"}
          </span>
          <span className="text-[11px] text-[var(--muted-foreground)] truncate">
            {isAuthenticated ? user?.email : "Sign in to save history"}
          </span>
        </Link>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          type="button"
          onClick={() => setDark((d) => !d)}
          className="p-2 rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
          aria-label={dark ? "Light mode" : "Dark mode"}
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </motion.button>
        {isAuthenticated ? (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            type="button"
            onClick={logout}
            className="p-2 rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--hover)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Sign out"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
          </motion.button>
        ) : null}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? 0 : SIDEBAR_WIDTH }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="hidden md:flex flex-col fixed inset-y-0 left-0 z-30 bg-[var(--sidebar)] border-r border-[var(--sidebar-border)] overflow-hidden"
      >
        <div className="flex flex-col h-full min-w-[220px]">
          {sidebarContent}
        </div>
      </motion.aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => onMobileClose?.()}
              className="fixed inset-0 z-40 bg-black/50 md:hidden"
              aria-hidden
            />
            <motion.aside
              initial={{ x: -220 }}
              animate={{ x: 0 }}
              exit={{ x: -220 }}
              transition={{ type: "tween", duration: 0.2 }}
              className="fixed inset-y-0 left-0 z-50 w-[220px] flex flex-col md:hidden bg-[var(--sidebar)] border-r border-[var(--sidebar-border)] shadow-xl"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {collapsed && (
        <button
          type="button"
          onClick={onToggle}
          className="hidden md:flex fixed left-0 top-4 z-30 h-9 w-9 items-center justify-center rounded-r-lg bg-[var(--sidebar)] border border-l-0 border-[var(--sidebar-border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          aria-label="Expand sidebar"
        >
          <PanelLeft className="h-4 w-4" strokeWidth={1.5} />
        </button>
      )}
    </>
  );
}

export { SIDEBAR_WIDTH };
