"use client";

import {
  buildDemoDashboard,
  demoCases,
  simulateAnalysis
} from "@/lib/demo-data";
import type {
  Artifact,
  CaseDetail,
  CaseMode,
  DashboardSummary,
  QueueCase
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const STORAGE_KEY = "aegis-os-demo-cases";
const ENABLE_DEMO_FALLBACK = process.env.NEXT_PUBLIC_ENABLE_DEMO_FALLBACK === "true";

function isBrowser() {
  return typeof window !== "undefined";
}

function toJsonHeaders() {
  return {
    Accept: "application/json",
    "Content-Type": "application/json"
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

function saveCases(cases: CaseDetail[]) {
  if (!isBrowser()) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cases));
}

function loadCases(): CaseDetail[] {
  if (!isBrowser()) {
    return demoCases();
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    const seeded = demoCases();
    saveCases(seeded);
    return seeded;
  }

  try {
    const parsed = JSON.parse(raw) as CaseDetail[];
    return parsed.length ? parsed : demoCases();
  } catch {
    const seeded = demoCases();
    saveCases(seeded);
    return seeded;
  }
}

function upsertCase(updated: CaseDetail) {
  const current = loadCases();
  const next = [updated, ...current.filter((item) => item.id !== updated.id)];
  saveCases(next);
  return updated;
}

function createLocalCase(mode: CaseMode, rawInput: string): CaseDetail {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    mode,
    raw_input: rawInput,
    detected_case_type: "unclear",
    urgency_level: "moderate",
    confidence: 0,
    handoff_summary: "Awaiting analysis",
    structured_result_json: null,
    artifacts: [],
    analysis_runs: [],
    recommended_actions: [],
    created_at: now,
    updated_at: now
  };
}

export async function createCase(payload: { mode: CaseMode; raw_input: string }) {
  try {
    return await request<CaseDetail>("/cases", {
      method: "POST",
      headers: toJsonHeaders(),
      body: JSON.stringify(payload)
    });
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while creating the case.");
    }
    const local = createLocalCase(payload.mode, payload.raw_input);
    return upsertCase(local);
  }
}

export async function uploadCaseArtifact(caseId: string, file: File, artifactType = "attachment") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("artifact_type", artifactType);

  try {
    return await request<CaseDetail>(`/cases/${caseId}/upload`, {
      method: "POST",
      body: formData
    });
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while uploading the artifact.");
    }
    const cases = loadCases();
    const existing = cases.find((item) => item.id === caseId);
    if (!existing) {
      throw new Error("Case not found.");
    }

    const excerpt = file.type === "text/plain" ? (await file.text()).slice(0, 600) : null;
    const artifact: Artifact = {
      id: crypto.randomUUID(),
      filename: file.name,
      mime_type: file.type || "application/octet-stream",
      size_bytes: file.size,
      artifact_type: artifactType,
      storage_provider: "demo",
      storage_uri: `demo://${caseId}/${file.name}`,
      content_excerpt: excerpt,
      created_at: new Date().toISOString()
    };
    existing.artifacts = [artifact, ...existing.artifacts];
    existing.updated_at = new Date().toISOString();
    return upsertCase(existing);
  }
}

export async function analyzeCase(caseId: string, modeOverride?: CaseMode | null) {
  try {
    return await request<CaseDetail>(`/cases/${caseId}/analyze`, {
      method: "POST",
      headers: toJsonHeaders(),
      body: JSON.stringify(modeOverride ? { mode_override: modeOverride } : {})
    });
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while analyzing the case.");
    }
    const cases = loadCases();
    const existing = cases.find((item) => item.id === caseId);
    if (!existing) {
      throw new Error("Case not found.");
    }

    const mode = modeOverride ?? existing.mode;
    const structured = simulateAnalysis(existing.raw_input, mode);
    existing.mode = mode;
    existing.detected_case_type = structured.case_type;
    existing.urgency_level = structured.urgency_level;
    existing.confidence = structured.confidence;
    existing.handoff_summary = structured.handoff_summary;
    existing.structured_result_json = structured;
    existing.recommended_actions = structured.recommended_actions;
    existing.analysis_runs = [
      {
        id: crypto.randomUUID(),
        status: "succeeded",
        mode_used: mode,
        model_name: "demo-fallback",
        prompt_name: "local-simulation",
        created_at: new Date().toISOString(),
        latency_ms: 120
      },
      ...existing.analysis_runs
    ];
    existing.updated_at = new Date().toISOString();
    return upsertCase(existing);
  }
}

export async function getCase(caseId: string) {
  try {
    return await request<CaseDetail>(`/cases/${caseId}`);
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while loading the case.");
    }
    const found = loadCases().find((item) => item.id === caseId);
    if (!found) {
      throw new Error("Case not found.");
    }
    return found;
  }
}

export async function listCases() {
  try {
    return await request<QueueCase[]>("/cases");
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while listing cases.");
    }
    return loadCases().map((item) => ({
      id: item.id,
      mode: item.mode,
      detected_case_type: item.detected_case_type,
      urgency_level: item.urgency_level,
      confidence: item.confidence,
      handoff_summary: item.handoff_summary,
      created_at: item.created_at
    }));
  }
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    return await request<DashboardSummary>("/dashboard/summary");
  } catch {
    if (!ENABLE_DEMO_FALLBACK) {
      throw new Error("Backend connection failed while loading dashboard summary.");
    }
    return buildDemoDashboard(loadCases());
  }
}
