import { AlertTriangle, Phone } from "lucide-react";

export function EmergencyBanner() {
  return (
    <div className="rounded-xl bg-gradient-to-r from-red-600 to-red-700 text-white p-4 shadow-lg animate-pulse">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-6 w-6 shrink-0" strokeWidth={1.5} />
        <div>
          <p className="font-semibold">Seek immediate care</p>
          <p className="text-sm opacity-90 mt-1">
            If you or someone else is in danger, call emergency services now.
          </p>
          <div className="flex flex-wrap gap-4 mt-3 text-sm">
            <a href="tel:911" className="inline-flex items-center gap-1.5 font-medium">
              <Phone className="h-4 w-4" /> 911
            </a>
            <a href="tel:988" className="inline-flex items-center gap-1.5 font-medium">
              <Phone className="h-4 w-4" /> Crisis line: 988
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
