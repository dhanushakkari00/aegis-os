"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { MapPinned, Radar } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { LocationPulse } from "@/lib/types";
import { urgencyMeta } from "@/components/urgency-badge";

export function IncidentMapCard({
  pulses,
  mapPreviewUrl
}: {
  pulses: LocationPulse[];
  mapPreviewUrl?: string;
}) {
  const [showMap, setShowMap] = useState(Boolean(mapPreviewUrl));

  useEffect(() => {
    setShowMap(Boolean(mapPreviewUrl));
  }, [mapPreviewUrl]);

  const hasMapCoordinates = pulses.some((pulse) => pulse.lat != null && pulse.lng != null);

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div>
          <CardTitle>Incident Pulse Map</CardTitle>
          <CardDescription>
            Spatial awareness snapshot for active reports and browser-shared locations.
          </CardDescription>
        </div>
        {showMap && hasMapCoordinates ? (
          <MapPinned className="h-5 w-5 text-cyan" />
        ) : (
          <Radar className="h-5 w-5 text-surge" />
        )}
      </CardHeader>
      {showMap && mapPreviewUrl && hasMapCoordinates ? (
        <div className="relative h-[320px] overflow-hidden rounded-[24px] border border-white/10 bg-white/5">
          <Image
            src={mapPreviewUrl}
            alt="Incident overview map"
            fill
            unoptimized
            className="object-cover"
            onError={() => setShowMap(false)}
          />
        </div>
      ) : (
        <div className="relative min-h-[320px] rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_center,rgba(78,232,255,0.08),transparent_60%),linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))] p-6">
          <div className="absolute inset-0 bg-command-grid bg-[size:48px_48px] opacity-[0.15]" />
          {pulses.slice(0, 6).map((pulse, index) => {
            const positions = [
              "left-[16%] top-[18%]",
              "left-[58%] top-[25%]",
              "left-[32%] top-[56%]",
              "left-[70%] top-[62%]",
              "left-[18%] top-[75%]",
              "left-[48%] top-[12%]"
            ];
            return (
              <div key={`${pulse.label}-${index}`} className={`absolute ${positions[index]}`}>
                <div
                  className={`h-4 w-4 rounded-full border ${urgencyMeta[pulse.severity].className}`}
                />
                <div className="mt-3 w-36 rounded-2xl border border-white/10 bg-ink/85 p-3 text-xs text-slate-200 shadow-lg">
                  <p className="font-medium text-white">{pulse.label}</p>
                  <p className="mt-1 line-clamp-3">{pulse.note}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
