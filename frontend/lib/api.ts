"use client";

import type {
  CaseDetail,
  CaseMode,
  DashboardSummary,
  QueueCase
} from "@/lib/types";

const API_BASE = "/api/v1";

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
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the default message when the response body is not JSON.
    }
    throw new Error(detail);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

export async function createCase(payload: { mode: CaseMode; raw_input: string }) {
  return request<CaseDetail>("/cases", {
    method: "POST",
    headers: toJsonHeaders(),
    body: JSON.stringify(payload)
  });
}

export async function uploadCaseArtifact(caseId: string, file: File, artifactType = "attachment") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("artifact_type", artifactType);

  return request<CaseDetail>(`/cases/${caseId}/upload`, {
    method: "POST",
    body: formData
  });
}

export async function analyzeCase(caseId: string, modeOverride?: CaseMode | null) {
  return request<CaseDetail>(`/cases/${caseId}/analyze`, {
    method: "POST",
    headers: toJsonHeaders(),
    body: JSON.stringify(modeOverride ? { mode_override: modeOverride } : {})
  });
}

export async function getCase(caseId: string) {
  return request<CaseDetail>(`/cases/${caseId}`);
}

export async function listCases() {
  return request<QueueCase[]>("/cases");
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/dashboard/summary");
}
