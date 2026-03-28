"use client";

import { useId, useState } from "react";
import { FileAudio, FileImage, FileText, UploadCloud } from "lucide-react";

import { cn } from "@/lib/utils";

function iconForType(type: string) {
  if (type.startsWith("image/")) {
    return FileImage;
  }
  if (type.startsWith("audio/")) {
    return FileAudio;
  }
  return FileText;
}

export function FileDropzone({
  files,
  onFilesChange
}: {
  files: File[];
  onFilesChange: (files: File[]) => void;
}) {
  const inputId = useId();
  const [active, setActive] = useState(false);

  return (
    <div
      className={cn(
        "rounded-[24px] border border-dashed border-white/10 bg-white/5 p-5 transition",
        active && "border-cyan/40 bg-cyan/10"
      )}
      onDragEnter={() => setActive(true)}
      onDragLeave={() => setActive(false)}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        setActive(false);
        onFilesChange([...files, ...Array.from(event.dataTransfer.files)]);
      }}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-medium text-white">Artifacts</p>
          <p className="text-sm text-slate-300">
            Drag PDFs, images, transcripts, or mixed notes here.
          </p>
        </div>
        <label
          htmlFor={inputId}
          className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-100 transition hover:bg-white/10"
        >
          <UploadCloud className="h-4 w-4 text-cyan" />
          Add files
        </label>
      </div>
      <input
        id={inputId}
        type="file"
        multiple
        className="sr-only"
        accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md"
        onChange={(event) => onFilesChange([...files, ...Array.from(event.target.files ?? [])])}
      />
      <div className="mt-4 space-y-2">
        {files.length ? (
          files.map((file) => {
            const Icon = iconForType(file.type);
            return (
              <div
                key={`${file.name}-${file.size}`}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-ink/70 px-4 py-3 text-sm"
              >
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4 text-cyan" />
                  <div>
                    <p className="text-white">{file.name}</p>
                    <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      {Math.max(1, Math.round(file.size / 1024))} KB
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="text-xs uppercase tracking-[0.24em] text-slate-400 hover:text-white"
                  onClick={() =>
                    onFilesChange(files.filter((item) => item.name !== file.name || item.size !== file.size))
                  }
                >
                  Remove
                </button>
              </div>
            );
          })
        ) : (
          <p className="text-sm text-slate-400">No files attached yet.</p>
        )}
      </div>
    </div>
  );
}

