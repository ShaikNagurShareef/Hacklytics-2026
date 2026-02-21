import { Info, Shield, Phone } from "lucide-react";

export function TrustIndicators() {
  return (
    <footer className="mt-auto border-t border-[var(--border)] px-4 py-3 space-y-2">
      <p className="text-[13px] text-[var(--muted-foreground)] text-center">
        This is not a substitute for professional medical advice.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-4 text-[13px]">
        <span className="inline-flex items-center gap-1.5 text-[var(--muted-foreground)]">
          <Info className="h-4 w-4" strokeWidth={1.5} />
          Powered by AI
        </span>
        <a
          href="#privacy"
          className="inline-flex items-center gap-1.5 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          <Shield className="h-4 w-4" strokeWidth={1.5} />
          Your data is private
        </a>
        <a
          href="tel:911"
          className="inline-flex items-center gap-1.5 text-red-600 hover:text-red-700 font-medium"
        >
          <Phone className="h-4 w-4" strokeWidth={1.5} />
          Emergency? Call 911
        </a>
      </div>
    </footer>
  );
}
