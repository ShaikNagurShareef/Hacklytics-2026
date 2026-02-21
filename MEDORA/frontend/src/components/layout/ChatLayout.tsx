import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { MobileNav } from "./MobileNav";
import { cn } from "@/lib/utils";

interface ChatLayoutProps {
  children: React.ReactNode;
  agentLabel: string;
  status: "online" | "thinking";
}

export function ChatLayout({ children, agentLabel, status }: ChatLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-[var(--background)]">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((c) => !c)}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <div
        className={cn(
          "flex-1 flex flex-col min-h-screen transition-[padding] duration-200",
          !sidebarCollapsed && "md:pl-[220px]",
          sidebarCollapsed && "md:pl-12"
        )}
      >
        <div className="flex-1 flex flex-col min-h-0">
          <Header
            agentLabel={agentLabel}
            status={status}
            onMenuClick={() => setMobileMenuOpen(true)}
          />

          <main className="flex-1 flex flex-col min-w-0 max-w-[768px] w-full mx-auto px-6 pt-8 pb-32">
            <AnimatePresence mode="wait">
              <motion.div
                key={agentLabel}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="flex-1 flex flex-col min-h-0"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>

      <MobileNav />
    </div>
  );
}
