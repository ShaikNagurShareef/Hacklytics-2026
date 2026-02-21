export function Footer() {
  return (
    <footer className="py-4 text-center">
      <p className="text-[12px] text-[var(--muted-foreground)]">
        MEDORA may make mistakes. Not a substitute for medical advice.
      </p>
      <div className="flex items-center justify-center gap-3 mt-2 text-[12px] text-[var(--muted-foreground)]">
        <a href="#privacy" className="hover:text-[var(--foreground)] transition-colors">
          Privacy
        </a>
        <span>·</span>
        <a href="#terms" className="hover:text-[var(--foreground)] transition-colors">
          Terms
        </a>
        <span>·</span>
        <a href="tel:911" className="hover:text-[var(--foreground)] font-medium">
          Emergency: 911
        </a>
      </div>
    </footer>
  );
}
