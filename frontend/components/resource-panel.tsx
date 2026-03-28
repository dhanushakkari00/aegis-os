"use client";

import Image from "next/image";
import { Ambulance, Building2, HeartPulse, House, MapPinned, Phone } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { NearbyResource, NearbySearchResult } from "@/lib/api";

interface ResourcePanelProps {
  data: NearbySearchResult;
  mapPreviewUrl?: string;
}

const resourceGroups = [
  {
    key: "safe_houses",
    label: "Safe Houses",
    emptyLabel: "No nearby shelters were identified.",
    icon: House,
    accent: "text-emerald-300 border-emerald-400/20 bg-emerald-400/10"
  },
  {
    key: "clinics",
    label: "Medical Clinics",
    emptyLabel: "No nearby clinics were identified.",
    icon: Building2,
    accent: "text-cyan border-cyan/20 bg-cyan/10"
  },
  {
    key: "ambulance_services",
    label: "Ambulance Services",
    emptyLabel: "No nearby ambulance services were identified.",
    icon: Ambulance,
    accent: "text-amber-300 border-amber-400/20 bg-amber-400/10"
  },
  {
    key: "hospitals",
    label: "Hospitals",
    emptyLabel: "No nearby hospitals were identified.",
    icon: HeartPulse,
    accent: "text-critical border-critical/20 bg-critical/10"
  }
] as const;

function resourceLink(resource: NearbyResource) {
  if (resource.google_maps_uri) {
    return resource.google_maps_uri;
  }
  if (resource.place_id) {
    return `https://www.google.com/maps/place/?q=place_id:${resource.place_id}`;
  }
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${resource.name} ${resource.address}`
  )}`;
}

export function ResourcePanel({ data, mapPreviewUrl }: ResourcePanelProps) {
  const hasAnyResults =
    data.hospitals.length > 0 ||
    data.clinics.length > 0 ||
    data.ambulance_services.length > 0 ||
    data.safe_houses.length > 0;

  return (
    <Card className="space-y-5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan">Routing Resources</p>
          <p className="mt-2 text-sm text-slate-300">
            {data.query_location}
            {data.case_type !== "unclear" ? ` • ${data.case_type.replaceAll("_", " ")}` : ""}
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.22em] text-slate-300">
          <MapPinned className="h-3.5 w-3.5 text-cyan" />
          Backend Maps Lookup
        </div>
      </div>

      {!hasAnyResults ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-400">
          No nearby resources were identified for this location yet.
        </div>
      ) : null}

      {mapPreviewUrl ? (
        <div className="relative h-[280px] overflow-hidden rounded-[28px] border border-white/10 bg-white/5">
          <Image
            src={mapPreviewUrl}
            alt={`Resource map for ${data.query_location}`}
            fill
            unoptimized
            className="object-cover"
          />
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-4">
        {resourceGroups.map((group) => {
          const Icon = group.icon;
          const items = data[group.key];
          return (
            <div key={group.key} className="space-y-3">
              <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.22em] ${group.accent}`}>
                <Icon className="h-3.5 w-3.5" />
                {group.label}
              </div>

              {items.length === 0 ? (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-500">
                  {group.emptyLabel}
                </div>
              ) : (
                items.map((resource) => (
                  <a
                    key={`${group.key}-${resource.place_id || `${resource.name}-${resource.address}`}`}
                    href={resourceLink(resource)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/70"
                  >
                    <p className="font-medium text-white">{resource.name}</p>
                    <p className="mt-1 text-sm text-slate-400">{resource.address}</p>
                    {resource.phone_number ? (
                      <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-200">
                        <Phone className="h-3.5 w-3.5 text-cyan" />
                        {resource.phone_number}
                      </div>
                    ) : null}
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                      {resource.rating != null ? (
                        <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                          Rating {resource.rating.toFixed(1)}
                        </span>
                      ) : null}
                      {resource.open_now != null ? (
                        <span
                          className={`rounded-full border px-2 py-1 ${
                            resource.open_now
                              ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
                              : "border-white/10 bg-white/5 text-slate-400"
                          }`}
                        >
                          {resource.open_now ? "Open now" : "Closed"}
                        </span>
                      ) : null}
                      <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                        Directions
                      </span>
                    </div>
                  </a>
                ))
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
