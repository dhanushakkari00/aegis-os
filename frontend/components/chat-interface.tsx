"use client";

import { startTransition, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LoaderCircle,
  LocateFixed,
  Mic,
  Paperclip,
  Send,
  Sparkles,
  Square,
  X
} from "lucide-react";

import { ResourcePanel } from "@/components/resource-panel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { UrgencyBadge } from "@/components/urgency-badge";
import {
  analyzeCase,
  createCase,
  getCaseResourceMapUrl,
  getNearbyResources,
  updateCase,
  uploadCaseArtifact,
  type NearbySearchResult
} from "@/lib/api";
import type { CaseDetail, CaseMode } from "@/lib/types";

type ChatMessage =
  | { role: "user"; text: string; files: string[]; mode: CaseMode }
  | {
      role: "assistant";
      caseData: CaseDetail;
      nearbyData?: NearbySearchResult | null;
    };

const RECORDING_FORMATS = [
  { mimeType: "audio/webm;codecs=opus", extension: "webm" },
  { mimeType: "audio/webm", extension: "webm" },
  { mimeType: "audio/ogg;codecs=opus", extension: "ogg" },
  { mimeType: "audio/ogg", extension: "ogg" },
  { mimeType: "audio/mp4", extension: "mp4" }
];

function getSupportedRecordingFormat() {
  if (typeof MediaRecorder === "undefined") {
    return null;
  }

  return (
    RECORDING_FORMATS.find((format) => MediaRecorder.isTypeSupported(format.mimeType)) ?? null
  );
}

function formatRecordingDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function buildArtifactOnlyMessage(files: File[]) {
  if (files.some((file) => file.type.startsWith("audio/"))) {
    return "Voice recording attached for analysis.";
  }

  return "Evidence files attached for analysis.";
}

function buildArtifactOnlyIntake(files: File[]) {
  if (files.some((file) => file.type.startsWith("audio/"))) {
    return "Voice recording attached for transcription and emergency analysis.";
  }

  return "Evidence files attached. Extract the critical facts from the uploaded artifacts.";
}

type CapturedLocation = {
  lat: number;
  lng: number;
  accuracyMeters: number | null;
  capturedAt: string;
};

function buildLocationContext(location: CapturedLocation | null) {
  if (!location) {
    return "";
  }

  const accuracy = location.accuracyMeters != null ? `${Math.round(location.accuracyMeters)}m` : "unknown";
  return `Device location shared by browser: latitude ${location.lat.toFixed(6)}, longitude ${location.lng.toFixed(6)}, accuracy ${accuracy}, captured_at ${location.capturedAt}.`;
}

function composeIntakeText(baseText: string, location: CapturedLocation | null) {
  const locationContext = buildLocationContext(location);
  return [baseText.trim(), locationContext].filter(Boolean).join("\n\n");
}

function buildFollowUpIntake(
  existingInput: string,
  updateText: string,
  previousAssistantResponse: string | null,
  location: CapturedLocation | null
) {
  const locationContext = buildLocationContext(location);
  return [
    existingInput.trim(),
    previousAssistantResponse ? `Previous Aegis OS response:\n${previousAssistantResponse}` : "",
    `Latest user update:\n${updateText.trim()}`,
    locationContext
  ]
    .filter(Boolean)
    .join("\n\n");
}

export function ChatInterface() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<CaseMode>("auto_detect");
  const [files, setFiles] = useState<File[]>([]);
  const [activeCase, setActiveCase] = useState<CaseDetail | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [capturedLocation, setCapturedLocation] = useState<CapturedLocation | null>(null);
  const [isCapturingLocation, setIsCapturingLocation] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isStartingRecording, setIsStartingRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordingMimeTypeRef = useRef("audio/webm");
  const recordingChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const resetConversation = () => {
    setMessages([]);
    setActiveCase(null);
    setInput("");
    setFiles([]);
    setCapturedLocation(null);
    setError(null);
  };

  const clearRecordingTimer = () => {
    if (recordingTimerRef.current !== null) {
      window.clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  };

  const releaseMediaStream = () => {
    if (!mediaStreamRef.current) {
      return;
    }

    for (const track of mediaStreamRef.current.getTracks()) {
      track.stop();
    }
    mediaStreamRef.current = null;
  };

  useEffect(() => {
    if (!isRecording) {
      return undefined;
    }

    recordingTimerRef.current = window.setInterval(() => {
      setRecordingSeconds((previous) => previous + 1);
    }, 1000);

    return () => {
      clearRecordingTimer();
    };
  }, [isRecording]);

  useEffect(() => {
    return () => {
      clearRecordingTimer();

      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.ondataavailable = null;
        mediaRecorderRef.current.onstop = null;
        if (mediaRecorderRef.current.state !== "inactive") {
          mediaRecorderRef.current.stop();
        }
      }

      releaseMediaStream();
    };
  }, []);

  const handleSubmit = async (
    text: string,
    overrideMode?: CaseMode,
    forceNewCase = false
  ) => {
    const trimmedText = text.trim();
    if (
      (!trimmedText && files.length === 0 && !capturedLocation) ||
      sending ||
      isRecording ||
      isStartingRecording ||
      isCapturingLocation
    ) {
      return;
    }

    const activeMode = overrideMode ?? mode;
    const continuingExistingCase = Boolean(activeCase) && !forceNewCase;
    const textOnlyFallback = capturedLocation
      ? "Current location shared for emergency analysis."
      : buildArtifactOnlyMessage(files);
    const intakeOnlyFallback = capturedLocation
      ? "User shared current browser location for emergency analysis."
      : buildArtifactOnlyIntake(files);
    const latestTurnText = trimmedText || intakeOnlyFallback;
    const messageText = trimmedText || textOnlyFallback;
    const intakeText = composeIntakeText(latestTurnText, capturedLocation);
    const userMsg: ChatMessage = {
      role: "user",
      text: messageText,
      files: files.map((f) => f.name),
      mode: activeMode
    };

    setMessages((prev) => (forceNewCase ? [userMsg] : [...prev, userMsg]));
    setInput("");
    setSending(true);
    setError(null);
    if (forceNewCase) {
      setActiveCase(null);
    }
    scrollToBottom();

    try {
      const previousAssistantResponse =
        activeCase?.structured_result_json?.assistant_response ?? activeCase?.handoff_summary ?? null;
      const targetCase = continuingExistingCase && activeCase
        ? await updateCase(activeCase.id, {
            mode: activeMode,
            raw_input: buildFollowUpIntake(
              activeCase.raw_input,
              latestTurnText,
              previousAssistantResponse,
              capturedLocation
            )
          })
        : await createCase({ mode: activeMode, raw_input: intakeText });

      for (const file of files) {
        const artifactType = file.type.startsWith("image/")
          ? "image"
          : file.type.startsWith("audio/")
            ? "audio"
            : file.type === "application/pdf"
              ? "document"
              : "attachment";
        await uploadCaseArtifact(targetCase.id, file, artifactType);
      }
      setFiles([]);
      setCapturedLocation(null);

      const analyzed = await analyzeCase(targetCase.id, activeMode);
      setActiveCase(analyzed);

      let nearbyData: NearbySearchResult | null = null;
      if (
        analyzed.structured_result_json?.extracted_location ||
        (analyzed.structured_result_json?.location_lat != null &&
          analyzed.structured_result_json?.location_lng != null)
      ) {
        try {
          nearbyData = await getNearbyResources(analyzed.id);
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

  const startRecording = async () => {
    if (sending || isRecording || isStartingRecording) {
      return;
    }

    if (
      typeof window === "undefined" ||
      typeof MediaRecorder === "undefined" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      setError("Microphone capture is not available in this browser.");
      return;
    }

    setError(null);
    setIsStartingRecording(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredFormat = getSupportedRecordingFormat();
      const recorder = preferredFormat
        ? new MediaRecorder(stream, { mimeType: preferredFormat.mimeType })
        : new MediaRecorder(stream);

      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recordingChunksRef.current = [];
      recordingMimeTypeRef.current = recorder.mimeType || preferredFormat?.mimeType || "audio/webm";

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordingChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Audio capture failed. Please stop and try again.");
      };

      recorder.onstop = () => {
        const mimeType = recordingMimeTypeRef.current.split(";", 1)[0] || "audio/webm";
        const extension = mimeType.includes("ogg")
          ? "ogg"
          : mimeType.includes("mp4")
            ? "mp4"
            : "webm";
        const blob = new Blob(recordingChunksRef.current, { type: mimeType });

        recordingChunksRef.current = [];
        clearRecordingTimer();
        releaseMediaStream();
        mediaRecorderRef.current = null;
        setIsRecording(false);
        setRecordingSeconds(0);

        if (blob.size === 0) {
          setError("No audio was captured. Please try again.");
          return;
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const recordedFile = new File([blob], `aegis-voice-${timestamp}.${extension}`, {
          type: mimeType
        });
        setFiles((previous) => [...previous, recordedFile]);
      };

      recorder.start(250);
      setRecordingSeconds(0);
      setIsRecording(true);
    } catch (recordingError) {
      releaseMediaStream();
      setError(
        recordingError instanceof DOMException && recordingError.name === "NotAllowedError"
          ? "Microphone permission was denied."
          : "Unable to access the microphone."
      );
    } finally {
      setIsStartingRecording(false);
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) {
      return;
    }

    if (recorder.state !== "inactive") {
      recorder.stop();
      return;
    }

    clearRecordingTimer();
    releaseMediaStream();
    setIsRecording(false);
    setRecordingSeconds(0);
  };

  const captureLocation = async () => {
    if (sending || isCapturingLocation) {
      return;
    }

    if (typeof window === "undefined" || !navigator.geolocation) {
      setError("Location capture is not available in this browser.");
      return;
    }

    setError(null);
    setIsCapturingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCapturedLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracyMeters: position.coords.accuracy ?? null,
          capturedAt: new Date(position.timestamp).toISOString()
        });
        setIsCapturingLocation(false);
      },
      (geoError) => {
        setError(
          geoError.code === geoError.PERMISSION_DENIED
            ? "Location permission was denied."
            : "Unable to capture current location."
        );
        setIsCapturingLocation(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const canSubmit = Boolean(input.trim() || files.length > 0 || capturedLocation);

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
              Describe the emergency, attach evidence, or share your location. Aegis OS will
              respond conversationally, keep the same case thread, and escalate only when enough
              evidence exists.
            </p>
            <div className="mt-8 max-w-xl rounded-[28px] border border-white/10 bg-white/5 p-5 text-left">
              <p className="text-xs uppercase tracking-[0.24em] text-cyan">How It Works</p>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Start with anything: a greeting, a symptom report, a field note, an image, a PDF,
                live audio, or your location. The backend keeps a single case thread and sends the
                previous analysis back into Gemini on every follow-up turn.
              </p>
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
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.22em] text-slate-300">
                      {msg.caseData.structured_result_json?.decision_state?.replaceAll("_", " ")}
                    </span>
                    <span className="text-sm text-slate-400">
                      {Math.round(msg.caseData.confidence * 100)}% confidence
                    </span>
                    <span className="text-xs text-slate-500">
                      {msg.caseData.detected_case_type}
                    </span>
                  </div>

                  <Card className="border-cyan/20 bg-cyan/10 p-4">
                    <p className="text-xs uppercase tracking-[0.24em] text-cyan mb-2">
                      Aegis Reply
                    </p>
                    <p className="text-sm leading-7 text-white">
                      {msg.caseData.structured_result_json?.assistant_response ?? msg.caseData.handoff_summary}
                    </p>
                  </Card>

                  {msg.caseData.structured_result_json?.final_verdict ? (
                    <Card className="p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-signal mb-2">
                        Final Verdict
                      </p>
                      <p className="text-sm text-slate-200">
                        {msg.caseData.structured_result_json.final_verdict}
                      </p>
                    </Card>
                  ) : null}

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
                          {action.rationale ? (
                            <p className="mt-1 pl-8 text-[11px] uppercase tracking-[0.2em] text-slate-500">
                              Why: {action.rationale}
                            </p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}

                  {(msg.caseData.structured_result_json?.follow_up_questions?.length ?? 0) > 0 && (
                    <div className="rounded-2xl border border-cyan/20 bg-cyan/10 p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-cyan mb-2">
                        Ask Next In Chat
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {msg.caseData.structured_result_json!.follow_up_questions.map((question) => (
                          <button
                            key={question}
                            type="button"
                            onClick={() => setInput(question)}
                            className="rounded-full border border-cyan/20 bg-white/5 px-3 py-2 text-left text-xs text-slate-100 transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70"
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                      <p className="mt-3 text-xs text-slate-400">
                        Your next reply will update this same case and re-run analysis.
                      </p>
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

                  {msg.nearbyData ? (
                    <ResourcePanel
                      data={msg.nearbyData}
                      mapPreviewUrl={getCaseResourceMapUrl(msg.caseData.id)}
                    />
                  ) : null}

                  {/* Full detail link */}
                  <button
                    type="button"
                    onClick={() => {
                      startTransition(() => {
                        router.push(`/cases/${msg.caseData.id}`);
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
        {activeCase ? (
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-cyan">Active Case Thread</p>
              <p className="mt-1 text-sm text-slate-300">
                Replies continue case <span className="font-mono text-slate-100">{activeCase.id}</span>
                {activeCase.structured_result_json?.decision_state ? (
                  <> • {activeCase.structured_result_json.decision_state.replaceAll("_", " ")}</>
                ) : null}
              </p>
            </div>
            <Button type="button" variant="secondary" size="sm" onClick={resetConversation}>
              Start new case
            </Button>
          </div>
        ) : null}

        <div className="sr-only" aria-live="polite">
          {isStartingRecording
            ? "Starting microphone capture."
            : isRecording
              ? `Recording audio. ${formatRecordingDuration(recordingSeconds)} elapsed.`
              : "Microphone idle."}
        </div>

        {(isStartingRecording || isRecording) && (
          <div
            className="mb-3 flex items-center gap-3 rounded-2xl border border-critical/20 bg-critical/10 px-4 py-3"
            role="status"
            aria-live="polite"
          >
            {isStartingRecording ? (
              <LoaderCircle className="h-4 w-4 animate-spin text-critical" aria-hidden="true" />
            ) : (
              <span
                className="h-2.5 w-2.5 rounded-full bg-critical shadow-[0_0_16px_rgba(255,96,96,0.7)]"
                aria-hidden="true"
              />
            )}
            <div>
              <p className="text-sm font-medium text-rose-100">
                {isStartingRecording
                  ? "Preparing microphone capture..."
                  : `Recording live audio ${formatRecordingDuration(recordingSeconds)}`}
              </p>
              <p className="text-xs text-rose-200/75">
                Stop recording to attach the clip to this emergency intake.
              </p>
            </div>
          </div>
        )}

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

        {capturedLocation ? (
          <div className="mb-3 flex items-center justify-between gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-emerald-200">
                Browser location attached
              </p>
              <p className="text-xs text-emerald-100/80">
                {capturedLocation.lat.toFixed(5)}, {capturedLocation.lng.toFixed(5)}
                {capturedLocation.accuracyMeters != null
                  ? ` • ±${Math.round(capturedLocation.accuracyMeters)}m`
                  : ""}
              </p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setCapturedLocation(null)}
            >
              Clear
            </Button>
          </div>
        ) : null}

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
            disabled={sending || isRecording || isStartingRecording}
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          <Button
            type="button"
            variant={capturedLocation ? "default" : "ghost"}
            size="icon"
            onClick={() => void captureLocation()}
            aria-label="Share current location"
            className="shrink-0"
            disabled={sending || isCapturingLocation}
          >
            {isCapturingLocation ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <LocateFixed className="h-4 w-4" />
            )}
          </Button>

          <Button
            type="button"
            variant={isRecording ? "critical" : "ghost"}
            size="icon"
            onClick={() => {
              if (isRecording) {
                stopRecording();
                return;
              }

              void startRecording();
            }}
            aria-label={isRecording ? "Stop microphone recording" : "Start microphone recording"}
            aria-pressed={isRecording}
            className="shrink-0"
            disabled={sending || isStartingRecording || isCapturingLocation}
          >
            {isStartingRecording ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : isRecording ? (
              <Square className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
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
            placeholder={activeCase ? "Add clarifying details to this case..." : "Describe the emergency situation..."}
            className="h-10 flex-1 rounded-xl border border-white/10 bg-white/5 px-4 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-cyan/50"
            disabled={sending}
            aria-label="Emergency intake message"
          />

          {/* Send */}
          <Button
            type="button"
            size="icon"
            disabled={sending || isRecording || isStartingRecording || !canSubmit}
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
