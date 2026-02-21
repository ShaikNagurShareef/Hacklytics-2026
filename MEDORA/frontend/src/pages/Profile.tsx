import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mail,
  Calendar,
  Stethoscope,
  UtensilsCrossed,
  Heart,
  LogOut,
  ChevronRight,
  Shield,
  Sparkles,
  MessageSquare,
  Pencil,
  Check,
  X,
  User as UserIcon,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getMyChats, updateProfile } from "@/api/client";
import type { ChatSessionListItem } from "@/api/types";
import { cn } from "@/lib/utils";

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
    day: "numeric",
  });
}

function initials(name: string | null, email: string) {
  if (name && name.trim()) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

const stats = [
  { label: "Virtual Doctor", icon: Stethoscope, color: "text-teal-500", bg: "bg-teal-500/10", border: "border-teal-500/20" },
  { label: "Dietary", icon: UtensilsCrossed, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  { label: "Wellbeing", icon: Heart, color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/20" },
];

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

export function Profile() {
  const { user, logout, setUser } = useAuth();
  const [chats, setChats] = useState<ChatSessionListItem[]>([]);
  const [chatsLoading, setChatsLoading] = useState(true);
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState("");
  const [savingName, setSavingName] = useState(false);

  useEffect(() => {
    getMyChats()
      .then(setChats)
      .catch(() => setChats([]))
      .finally(() => setChatsLoading(false));
  }, []);

  if (!user) return null;

  const displayName = user.full_name?.trim() || "Member";
  const memberSince = formatDate(user.created_at);

  const handleSaveName = async () => {
    const val = editNameValue.trim();
    setSavingName(true);
    try {
      const updated = await updateProfile({ full_name: val || null });
      setUser(updated);
      setEditingName(false);
    } finally {
      setSavingName(false);
    }
  };

  const startEditName = () => {
    setEditNameValue(user.full_name ?? "");
    setEditingName(true);
  };

  return (
    <div className="min-h-screen bg-[var(--background)] font-sans text-[var(--foreground)] pb-20 selection:bg-[var(--primary)]/20">
      {/* Premium Hero section with Glassmorphism and Gradients */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[var(--background)] via-[var(--primary)]/5 to-[var(--background)] pt-8 pb-32">
        {/* Animated Background Blobs */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[60%] rounded-full bg-[var(--primary)]/10 blur-[100px] mix-blend-multiply dark:mix-blend-screen animate-pulse" style={{ animationDuration: "8s" }}></div>
          <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-teal-500/10 blur-[120px] mix-blend-multiply dark:mix-blend-screen animate-pulse" style={{ animationDuration: "10s", animationDelay: "2s" }}></div>
        </div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="rounded-[2rem] bg-white/40 dark:bg-black/40 backdrop-blur-xl border border-white/20 dark:border-white/10 shadow-2xl shadow-teal-500/5 p-8 sm:p-10 flex flex-col md:flex-row items-center md:items-start gap-8"
          >
            {/* Avatar Profile Ring */}
            <div className="relative group shrink-0">
              <div className="absolute -inset-1 rounded-full bg-gradient-to-tr from-[var(--primary)] to-teal-300 opacity-70 group-hover:opacity-100 blur transition duration-500"></div>
              <div className="relative h-28 w-28 sm:h-32 sm:w-32 rounded-full bg-[var(--background)] flex items-center justify-center border-4 border-[var(--background)] overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)]/20 to-teal-500/20" />
                <span className="text-4xl sm:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-[var(--primary)] to-teal-700 dark:to-teal-400 drop-shadow-sm">
                  {initials(editingName ? editNameValue : user.full_name, user.email)}
                </span>
              </div>
            </div>

            {/* Profile Info & Edit Toggle */}
            <div className="flex-1 text-center md:text-left space-y-4">
              <AnimatePresence mode="wait">
                {editingName ? (
                  <motion.div
                    key="edit"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="flex flex-col sm:flex-row items-center gap-3"
                  >
                    <div className="relative w-full sm:w-auto">
                      <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                      <input
                        type="text"
                        value={editNameValue}
                        onChange={(e) => setEditNameValue(e.target.value)}
                        placeholder="Display name"
                        className="w-full sm:w-[250px] pl-9 pr-4 py-2.5 rounded-xl border border-[var(--border)] bg-white/50 dark:bg-black/50 backdrop-blur-md focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/50 transition-all font-medium text-lg text-[var(--foreground)]"
                        autoFocus
                        onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveName}
                        disabled={savingName}
                        className="p-2.5 rounded-xl bg-gradient-to-r from-[var(--primary)] to-teal-500 text-white shadow-lg shadow-teal-500/25 hover:shadow-teal-500/40 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:hover:translate-y-0"
                      >
                        <Check className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => setEditingName(false)}
                        className="p-2.5 rounded-xl bg-white/50 dark:bg-white/5 backdrop-blur-md border border-[var(--border)] text-[var(--foreground)] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="view"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="space-y-1"
                  >
                    <div className="flex items-center justify-center md:justify-start gap-3">
                      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
                        {displayName}
                      </h1>
                      <button
                        onClick={startEditName}
                        className="p-2 rounded-full text-[var(--muted-foreground)] hover:text-[var(--primary)] hover:bg-[var(--primary)]/10 transition-all active:scale-95"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="flex flex-col sm:flex-row items-center justify-center md:justify-start gap-2 sm:gap-4 text-[var(--muted-foreground)] font-medium">
                      <span className="flex items-center gap-1.5 flex-wrap justify-center">
                        <Mail className="h-4 w-4 text-[var(--primary)]/70" />
                        {user.email}
                      </span>
                      <span className="hidden sm:inline text-[var(--border)]">•</span>
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-4 w-4 text-[var(--primary)]/70" />
                        Joined {memberSince}
                      </span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Action Buttons */}
              <div className="pt-4 flex flex-wrap items-center justify-center md:justify-start gap-3">
                <Link
                  to="/virtual-doctor"
                  className="group relative inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold overflow-hidden transition-all hover:scale-105 active:scale-95"
                >
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-teal-500 via-[var(--primary)] to-emerald-500 opacity-90 group-hover:opacity-100 transition-opacity"></div>
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
                  <Sparkles className="relative z-10 h-4 w-4 text-white" />
                  <span className="relative z-10 text-white">Ask MEDORA</span>
                </Link>
                <button
                  onClick={logout}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium bg-white/50 dark:bg-white/5 backdrop-blur-md border border-[var(--border)] text-[var(--foreground)] hover:bg-black/5 dark:hover:bg-white/10 hover:border-red-500/30 hover:text-red-500 transition-all active:scale-95"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content Sections */}
      <div className="relative z-20 max-w-5xl mx-auto px-4 sm:px-6 -mt-16 space-y-8">
        
        {/* Your Agents Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-6 px-2">
            <div className="h-8 w-1 rounded-full bg-[var(--primary)]"></div>
            <h2 className="text-xl font-bold tracking-tight">Your Specialized Agents</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 lg:gap-6">
            {stats.map(({ label, icon: Icon, color, bg, border }, i) => (
              <motion.div
                key={label}
                whileHover={{ y: -5, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
              >
                <Link
                  to={label === "Virtual Doctor" ? "/virtual-doctor" : label === "Dietary" ? "/dietary" : "/wellbeing"}
                  className={cn(
                    "group relative block p-6 rounded-2xl bg-white/60 dark:bg-[#1A1A1A]/60 backdrop-blur-xl border border-[var(--border)] shadow-sm hover:shadow-xl transition-all overflow-hidden",
                    border
                  )}
                >
                  {/* Subtle hover gradient background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  
                  <div className="flex items-start justify-between relative z-10">
                    <div className={cn("p-3 rounded-xl", bg, color)}>
                      <Icon className="h-6 w-6 stroke-[1.5px]" />
                    </div>
                    <div className={cn("p-2 rounded-full bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)] group-hover:text-[var(--primary)] group-hover:border-[var(--primary)]/30 transition-colors shadow-sm")}>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="mt-5 relative z-10">
                    <h3 className="font-semibold text-lg text-[var(--foreground)]">{label}</h3>
                    <p className="text-sm text-[var(--muted-foreground)] mt-1">
                      {label === "Virtual Doctor" ? "Medical advice & triage" : label === "Dietary" ? "Nutrition & meal plans" : "Mental health support"}
                    </p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chat History Section */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="lg:col-span-2"
          >
            <div className="flex items-center gap-3 mb-6 px-2">
              <div className="h-8 w-1 rounded-full bg-[var(--primary)]"></div>
              <h2 className="text-xl font-bold tracking-tight">Recent Conversations</h2>
            </div>
            
            <div className="bg-white/60 dark:bg-[#1A1A1A]/60 backdrop-blur-xl rounded-[2rem] border border-[var(--border)] shadow-sm overflow-hidden flex flex-col h-[400px]">
              {chatsLoading ? (
                <div className="flex-1 flex flex-col items-center justify-center text-[var(--muted-foreground)] gap-3">
                  <div className="h-8 w-8 border-4 border-[var(--primary)]/30 border-t-[var(--primary)] rounded-full animate-spin"></div>
                  <p className="text-sm font-medium animate-pulse">Loading history...</p>
                </div>
              ) : chats.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-transparent to-[var(--primary)]/5">
                  <div className="h-16 w-16 mb-4 rounded-2xl bg-[var(--primary)]/10 text-[var(--primary)] flex items-center justify-center">
                    <MessageSquare className="h-8 w-8 stroke-[1.5px]" />
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--foreground)] mb-2">No history yet</h3>
                  <p className="text-sm text-[var(--muted-foreground)] max-w-[250px]">
                    Your conversations with our specialized agents will appear here.
                  </p>
                  <Link
                    to="/virtual-doctor"
                    className="mt-6 px-6 py-2.5 rounded-xl bg-[var(--primary)] text-white font-medium hover:scale-105 active:scale-95 transition-all shadow-lg shadow-[var(--primary)]/20"
                  >
                    Start a chat
                  </Link>
                </div>
              ) : (
                <ul className="flex-1 overflow-y-auto scrollbar-thin divide-y divide-[var(--border)]/50 p-2">
                  {chats.map((chat, i) => (
                    <motion.li 
                      key={chat.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <Link
                        to={`${agentTypeToPath(chat.agent_type)}?session=${encodeURIComponent(chat.client_session_id)}`}
                        className="group flex items-center gap-4 p-4 rounded-xl hover:bg-white/80 dark:hover:bg-white-[0.02] transition-all"
                      >
                        <div className="relative shrink-0">
                          <div className="absolute -inset-1 rounded-xl bg-[var(--primary)]/20 opacity-0 group-hover:opacity-100 blur transition-opacity"></div>
                          <span className="relative flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--background)] to-[var(--hover)] border border-[var(--border)] text-[var(--primary)] shadow-sm group-hover:border-[var(--primary)]/30 transition-colors">
                            <MessageSquare className="h-5 w-5" />
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-[var(--foreground)] truncate group-hover:text-[var(--primary)] transition-colors">
                            {chat.title || "New chat"}
                          </p>
                          <div className="flex items-center gap-2 mt-1 text-sm text-[var(--muted-foreground)] font-medium">
                            <span className="truncate max-w-[120px] bg-[var(--hover)] px-2 py-0.5 rounded-md border border-[var(--border)] text-xs inline-block">
                              {chat.agent_type || "Ask"}
                            </span>
                            <span>•</span>
                            <span className="truncate">
                              {new Date(chat.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </div>
                        <div className="h-8 w-8 rounded-full bg-[var(--background)] border border-[var(--border)] flex items-center justify-center text-[var(--muted-foreground)] group-hover:bg-[var(--primary)] group-hover:text-white group-hover:border-[var(--primary)] group-hover:scale-110 shadow-sm transition-all shrink-0">
                          <ChevronRight className="h-4 w-4" />
                        </div>
                      </Link>
                    </motion.li>
                  ))}
                </ul>
              )}
            </div>
          </motion.section>

          {/* Privacy & Settings */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="lg:col-span-1"
          >
            <div className="flex items-center gap-3 mb-6 px-2">
              <div className="h-8 w-1 rounded-full bg-[var(--primary)]"></div>
              <h2 className="text-xl font-bold tracking-tight">Privacy & Security</h2>
            </div>
            
            <div className="bg-gradient-to-b from-white/60 to-white/40 dark:from-[#1A1A1A]/60 dark:to-[#1A1A1A]/40 backdrop-blur-xl rounded-[2rem] border border-[var(--border)] shadow-sm p-6 sm:p-8 flex flex-col gap-6 relative overflow-hidden">
              {/* Decorative background element */}
              <div className="absolute -right-6 -top-6 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl"></div>
              
              <div className="relative z-10">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 mb-6 shadow-sm">
                  <Shield className="h-7 w-7" strokeWidth={1.5} />
                </div>
                <h3 className="font-bold text-xl text-[var(--foreground)] mb-3">Your Data is Secure</h3>
                <p className="text-[var(--muted-foreground)] leading-relaxed">
                  We employ enterprise-grade encryption to ensure your health conversations remain entirely private. 
                </p>
                <div className="mt-6 space-y-3">
                  <div className="flex items-center gap-3 text-sm font-medium text-[var(--foreground)] bg-[var(--hover)] p-3 rounded-xl border border-[var(--border)]">
                    <Check className="h-4 w-4 text-emerald-500 shrink-0" /> End-to-end security
                  </div>
                  <div className="flex items-center gap-3 text-sm font-medium text-[var(--foreground)] bg-[var(--hover)] p-3 rounded-xl border border-[var(--border)]">
                    <Check className="h-4 w-4 text-emerald-500 shrink-0" /> No third-party sharing
                  </div>
                </div>
              </div>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
