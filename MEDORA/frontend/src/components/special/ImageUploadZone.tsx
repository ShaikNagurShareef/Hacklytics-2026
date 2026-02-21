import { useState } from "react";
import { ImagePlus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageUploadZoneProps {
  onSelect: (file: File) => void;
  onClear?: () => void;
  previewUrl?: string | null;
  analyzing?: boolean;
}

export function ImageUploadZone({
  onSelect,
  onClear,
  previewUrl,
  analyzing,
}: ImageUploadZoneProps) {
  const [drag, setDrag] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files[0];
    if (file?.type.startsWith("image/")) onSelect(file);
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file?.type.startsWith("image/")) onSelect(file);
    e.target.value = "";
  };

  return (
    <div className="rounded-xl border-2 border-dashed border-[var(--border)] p-6 text-center">
      {previewUrl ? (
        <div className="relative inline-block">
          <img
            src={previewUrl}
            alt="Upload preview"
            className="max-h-48 rounded-lg object-contain border border-[var(--border)]"
          />
          {analyzing && (
            <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-black/50">
              <span className="text-white text-sm font-medium">Analyzing...</span>
            </div>
          )}
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              className="absolute -top-2 -right-2 flex h-8 w-8 items-center justify-center rounded-full bg-red-500 text-white shadow"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      ) : (
        <label
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          className={cn(
            "flex flex-col items-center gap-2 cursor-pointer",
            drag && "opacity-80"
          )}
        >
          <ImagePlus className="h-10 w-10 text-[var(--muted-foreground)]" strokeWidth={1.5} />
          <span className="text-[15px] text-[var(--muted-foreground)]">
            Drag and drop an image, or click to browse
          </span>
          <input type="file" accept="image/*" onChange={handleFile} className="hidden" />
        </label>
      )}
    </div>
  );
}
