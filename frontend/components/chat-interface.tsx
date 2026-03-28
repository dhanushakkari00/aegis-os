"use client";

import { startTransition, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  HeartPulse,
  LoaderCircle,
  MapPin,
  MountainSnow,
  Paperclip,
  Send,
  Sparkles,
  X
} from "lucide-react";

import { NearbyMap } from "@/components/nearby-map";
import { UrgencyBadge } from "@/components/urgency-badge";
import { ConfidenceMeter } from "@/components/confidence-meter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  analyzeCase,
  createCase,
  getNearbyHospitals,
  uploadCaseArtifact,
  type NearbySearchResult
} from "@/lib/api";
import { medicalSeedInput, disasterSeedInput } from "@/lib/demo-data";
import type { CaseDetail, CaseMode } from "@/lib/types";

type ChatMessage =
  | { role: "user"; text: string; files: string[]; mode: CaseMode }
  | {
      role: "assistant";
      caseData: CaseDetail;
      nearbyData?: NearbySearchResult | null;
    };

const demoPrompts = [
  {
    label: "Medical emergency",
    text: medicalSeedInput,
    mode: "medical_triage" as CaseMode,
    icon: HeartPulse,
    color: "text-critical border-critical/20 bg-critical/10"
  },
  {
    label: "Disaster report",
    text: disasterSeedInput,
    mode: "disaster_response" as CaseMode,
    icon: MountainSnow,
    color: "text-signal border-signal/20 bg-signal/10"
  }
];

export function ChatInterface() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<CaseMode>("auto_detect");
  const [files, setFiles] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const handleSubmit = async (text: string, overrideMode?: CaseMode) => {
    if (!text.trim() || sending) return;

    const activeMode = overrideMode ?? mode;
    const userMsg: ChatMessage = {
      role: "user",
      text,
      files: files.map((f) => f.name),
      mode: activeMode
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);
    setError(null);
    scrollToBottom();

    try {
      const created = await createCase({ mode: activeMode, raw_input: text });

      for (const file of files) {
        const artifactType = file.type.startsWith("image/")
          ? "image"
          : file.type.startsWith("audio/")
            ? "audio"
            : file.type === "application/pdf"
              ? "document"
              : "attachment";
        await uploadCaseArtifact(created.id, file, artifactType);
      }
      setFiles([]);

      const analyzed = await analyzeCase(created.id, activeMode);

      let nearbyData: NearbySearchResult | null = null;
      if (
        analyzed.detected_case_type === "medical" ||
        analyzed.urgency_level === "critical" ||
        analyzed.urgency_level === "high"
      ) {
        try {
          nearbyData = await getNearbyHospitals(analyzed.id);
        } catch {
          // Nearby search is best-effort.
        }
      }

      const assistantMsg: ChatMessage = {
        role: "assistant",
        caseData: analyzed,
        nearbyData
      };

      setMessages((prev) => [...prev, assistantMsg]);
      scrollToBottom();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setSending(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = Array.from(e.target.files ?? []);
    setFiles((prev) => [...prev, ...newFiles]);
    e.target.value = "";
  };

  return (
    <div className="flex h-[calc(100vh-180px)] flex-col">
      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-3xl border border-cyan/20 bg-cyan/10 shadow-glow mb-6">
              <Sparkles className="h-10 w-10 text-cyan" />
            </div>
            <h2 className="font-display text-3xl font-semibold text-white">
              Emergency Intelligence
            </h2>
            <p className="mt-3 max-w-md text-slate-400">
              Describe an emergency situation, upload evidence files, and Aegis OS
              will analyze, classify, and provide structured operational intelligence.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              {demoPrompts.map((demo) => {
                const Icon = demo.icon;
                return (
                  <button
                    key={demo.label}
                    type="button"
                    onClick={() => {
                      setMode(demo.mode);
                      void handleSubmit(demo.text, demo.mode);
                    }}
                    className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition hover:bg-white/10 ${demo.color}`}
                  >
                    <Icon className="h-4 w-4" />
                    {demo.label}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={`msg-${i}`} className="flex justify-end">
                <div className="max-w-[70%] rounded-[20px] rounded-br-md border border-cyan/20 bg-cyan/10 p-4">
                  <p className="text-sm text-white whitespace-pre-wrap">{msg.text}</p>
                  {msg.files.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {msg.files.map((f) => (
                        <span
                          key={f}
                          className="rounded-full bg-cyan/20 px-2 py-0.5 text-xs text-cyan"
                        >
                          📎 {f}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="mt-2 text-xs text-cyan/60">{msg.mode.replaceAll("_", " ")}</p>
                </div>
              </div>
            ) : (
              <div key={`msg-${i}`} className="flex justify-start">
                <div className="max-w-[85%] space-y-4">
                  {/* Urgency + Confidence */}
                  <div className="flex items-center gap-3">
                    <UrgencyBadge urgency={msg.caseData.urgency_level} />
                    <span className="text-sm text-slate-400">
                      {Math.round(msg.caseData.confidence * 100)}% confidence
                    </span>
                    <span className="text-xs text-slate-500">
                      {msg.caseData.detected_case_type}
                    </span>
                  </div>

                  {/* Handoff Summary */}
                  <Card className="p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-cyan mb-2">
                      Handoff Summary
                    </p>
                    <p className="text-sm text-slate-200">{msg.caseData.handoff_summary}</p>
                  </Card>

                  {/* Recommended Actions */}
                  {msg.caseData.recommended_actions.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
                        Recommended Actions
                      </p>
                      {msg.caseData.recommended_actions.map((action) => (
                        <div
                          key={`${action.priority}-${action.title}`}
                          className="rounded-2xl border border-white/10 bg-white/5 p-3"
                        >
                          <div className="flex items-center gap-2">
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan/20 text-xs font-bold text-cyan">
                              P{action.priority}
                            </span>
                            <span className="font-medium text-white text-sm">{action.title}</span>
                            {action.is_immediate && (
                              <span className="rounded-full bg-critical/20 px-2 py-0.5 text-xs text-critical">
                                Immediate
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-slate-300 pl-8">{action.description}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Missing Information */}
                  {(msg.caseData.structured_result_json?.missing_information?.length ?? 0) > 0 && (
                    <div className="rounded-2xl border border-signal/20 bg-signal/10 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-signal mb-2">
                        Missing Critical Information
                      </p>
                      {msg.caseData.structured_result_json!.missing_information.map((item) => (
                        <div key={item.item} className="flex items-start gap-2 mt-1">
                          <span className="text-xs text-signal mt-0.5">⚠</span>
                          <div>
                            <span className="text-sm text-white font-medium">{item.item}</span>
                            <span className="text-xs text-slate-400 ml-2">{item.reason}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Nearby Hospitals Map */}
                  {msg.nearbyData && <NearbyMap data={msg.nearbyData} />}

                  {/* Full detail link */}
                  <button
                    type="button"
                    onClick={() => {
                      startTransition(() => {
                        router.push(`/analyze?caseId=${msg.caseData.id}`);
                      });
                    }}
                    className="text-xs text-cyan hover:underline"
                  >
                    View full analysis →
                  </button>
                </div>
              </div>
            )
          )
        )}

        {sending && (
          <div className="flex justify-start" role="status" aria-label="Analyzing">
            <Card className="flex items-center gap-3 p-4">
              <LoaderCircle className="h-4 w-4 animate-spin text-cyan" aria-hidden="true" />
              <p className="text-sm text-slate-200">Analyzing emergency situation...</p>
            </Card>
          </div>
        )}

        {error && (
          <div className="flex justify-start" role="alert">
            <Card className="border-critical/30 bg-critical/10 p-4">
              <p className="text-sm text-rose-100">{error}</p>
            </Card>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-white/10 pt-4">
        {files.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {files.map((file, idx) => (
              <span
                key={`file-${idx}`}
                className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300"
              >
                📎 {file.name}
                <button
                  type="button"
                  onClick={() => setFiles((prev) => prev.filter((_, i) => i !== idx))}
                  className="ml-1 text-slate-500 hover:text-white"
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2">
          {/* Mode selector */}
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as CaseMode)}
            className="h-10 rounded-xl border border-white/10 bg-white/5 px-3 text-sm text-white outline-none focus:ring-2 focus:ring-cyan/50"
            aria-label="Analysis mode"
          >
            <option value="auto_detect">Auto</option>
            <option value="medical_triage">Medical</option>
            <option value="disaster_response">Disaster</option>
          </select>

          {/* File upload */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,audio/*,application/pdf,text/plain"
            onChange={handleFileChange}
            className="hidden"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Attach files"
            className="shrink-0"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          {/* Text input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSubmit(input);
              }
            }}
            placeholder="Describe the emergency situation..."
            className="h-10 flex-1 rounded-xl border border-white/10 bg-white/5 px-4 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-cyan/50"
            disabled={sending}
            aria-label="Emergency intake message"
          />

          {/* Send */}
          <Button
            type="button"
            size="icon"
            disabled={sending || !input.trim()}
            onClick={() => void handleSubmit(input)}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
