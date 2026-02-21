import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Heart, Stethoscope, UtensilsCrossed } from "lucide-react";

const agents = [
  { to: "/virtual-doctor", label: "Virtual Doctor", icon: Stethoscope, short: "Doctor", desc: "Medical Q&A & image analysis" },
  { to: "/dietary", label: "Dietary", icon: UtensilsCrossed, short: "Dietary", desc: "Meal plans & nutrition" },
  { to: "/wellbeing", label: "Wellbeing", icon: Heart, short: "Wellbeing", desc: "Mental health support" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-background">
      {/* Desktop: dark sidebar - explicit dark bg so it always renders */}
      <aside
        className="hidden md:flex md:flex-col md:w-[280px] md:fixed md:inset-y-0 md:left-0 z-30 text-white"
        style={{ backgroundColor: "#18181B" }}
      >
        <div className="p-6 pb-4">
          <Link to="/virtual-doctor" className="flex items-center gap-2 text-white hover:opacity-90">
            <span className="text-xl font-semibold tracking-tight">MEDORA</span>
          </Link>
          <p className="text-zinc-400 text-xs mt-1">Premium healthcare AI</p>
        </div>
        <nav className="flex-1 px-4 space-y-3">
          {agents.map(({ to, label, icon: Icon, desc }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "block rounded-2xl border transition-all duration-200",
                  active
                    ? "border-white/20 bg-white/10"
                    : "border-white/5 bg-white/5 hover:bg-white/10 hover:border-white/10"
                )}
              >
                <div className="flex items-start gap-3 p-4">
                  <div
                    className={cn(
                      "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
                      active ? "bg-teal-500/30 text-teal-400" : "bg-white/10 text-zinc-400"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 pt-0.5">
                    <span className={cn(
                      "text-sm font-semibold",
                      active ? "text-white" : "text-zinc-200"
                    )}>
                      {label}
                    </span>
                    <p className="text-xs text-zinc-400 mt-0.5">{desc}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col md:pl-[280px] min-h-screen">
        <main className="flex-1 flex flex-col max-w-3xl mx-auto w-full px-4 py-4 md:py-6">
          {children}
        </main>
      </div>

      {/* Mobile: bottom navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-card border-t border-border pb-4">
        <div className="flex items-center justify-around h-16 px-2">
          {agents.map(({ to, icon: Icon, short }) => {
            const active = location.pathname === to;
            return (
              <button
                key={to}
                type="button"
                onClick={() => navigate(to)}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 min-w-[72px] py-2 rounded-xl transition-colors duration-200",
                  active
                    ? "text-primary"
                    : "text-muted-foreground"
                )}
              >
                <Icon className="h-6 w-6" />
                <span className="text-xs font-medium">{short}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Mobile: padding so content isn't hidden behind bottom nav */}
      <div className="md:hidden h-20 flex-shrink-0" aria-hidden />
    </div>
  );
}
