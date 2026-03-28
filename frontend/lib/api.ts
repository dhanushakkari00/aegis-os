"use client";

import type {
  CaseDetail,
  CaseMode,
  DashboardSummary,
  DetectedCaseType,
  QueueCase
} from "@/lib/types";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "/api/v1").replace(/\/$/, "");

type ValidationDetail = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

function formatValidationDetail(detail: ValidationDetail) {
  const location = Array.isArray(detail.loc) && detail.loc.length > 0
    ? `${detail.loc.join(".")}: `
    : "";
  return `${location}${detail.msg ?? detail.type ?? "Validation error"}`;
}

function normalizeErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object") {
          return formatValidationDetail(item as ValidationDetail);
        }
        return typeof item === "string" ? item : null;
      })
      .filter((item): item is string => Boolean(item));

    return messages.length > 0 ? messages.join(" | ") : null;
  }

  if (detail && typeof detail === "object") {
    const maybeMessage = "message" in detail ? detail.message : null;
    if (typeof maybeMessage === "string" && maybeMessage.trim()) {
      return maybeMessage;
    }
    return JSON.stringify(detail);
  }

  if (typeof detail === "number" || typeof detail === "boolean") {
    return String(detail);
  }

  return null;
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
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown; message?: unknown };
      detail = normalizeErrorDetail(payload.detail) ?? normalizeErrorDetail(payload.message) ?? detail;
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

export async function updateCase(caseId: string, payload: Partial<Pick<CaseDetail, "raw_input">> & { mode?: CaseMode }) {
  return request<CaseDetail>(`/cases/${caseId}`, {
    method: "PATCH",
    headers: toJsonHeaders(),
    body: JSON.stringify(payload)
  });
}

export async function listCases() {
  return request<QueueCase[]>("/cases");
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/dashboard/summary");
}

export function getDashboardIncidentMapUrl() {
  return `${API_BASE}/dashboard/incident-map`;
}

export type NearbyResource = {
  name: string;
  address: string;
  lat: number;
  lng: number;
  place_id: string;
  google_maps_uri?: string | null;
  resource_type: string;
  phone_number?: string | null;
  rating: number | null;
  open_now: boolean | null;
  primary_type?: string | null;
};

export type NearbySearchResult = {
  query_location: string;
  case_type: DetectedCaseType;
  lat: number | null;
  lng: number | null;
  hospitals: NearbyResource[];
  clinics: NearbyResource[];
  ambulance_services: NearbyResource[];
  safe_houses: NearbyResource[];
};

export async function getNearbyResources(caseId: string) {
  return request<NearbySearchResult>(`/cases/${caseId}/nearby-resources`);
}

export async function searchNearby(location: string, caseType: DetectedCaseType = "unclear") {
  return request<NearbySearchResult>(
    `/nearby?location=${encodeURIComponent(location)}&case_type=${encodeURIComponent(caseType)}`
  );
}

export function getCaseResourceMapUrl(caseId: string) {
  return `${API_BASE}/cases/${caseId}/resource-map`;
}
