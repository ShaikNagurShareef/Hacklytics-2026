import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("MEDORA ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div
          className="flex min-h-screen flex-col items-center justify-center bg-[#FAFAFA] px-4 dark:bg-[var(--background)]"
          role="alert"
        >
          <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" strokeWidth={1.5} />
          <h1 className="text-lg font-semibold text-[var(--foreground)]">Something went wrong</h1>
          <p className="mt-2 max-w-md text-center text-[13px] text-[var(--muted-foreground)]">
            {this.state.error.message}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#14B8A6] px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
