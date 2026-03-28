"use client";

import type { NearbyHospital, NearbySearchResult } from "@/lib/api";

interface NearbyMapProps {
  data: NearbySearchResult;
}

export function NearbyMap({ data }: NearbyMapProps) {
  if (!data.hospitals.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <p className="text-sm text-slate-400">
          No nearby hospitals found for &quot;{data.query_location}&quot;.
        </p>
      </div>
    );
  }

  const mapQ = data.lat && data.lng
    ? `${data.lat},${data.lng}`
    : encodeURIComponent(data.query_location);
  const mapSrc = `https://www.google.com/maps/embed/v1/search?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? ""}&q=hospital+near+${mapQ}&zoom=13`;

  return (
    <div className="space-y-4 rounded-[24px] border border-white/10 bg-white/5 p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.24em] text-cyan">
          Nearby Hospitals
        </p>
        <p className="text-xs text-slate-400">{data.query_location}</p>
      </div>

      {process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ? (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <iframe
            title="Nearby hospitals map"
            src={mapSrc}
            className="h-[280px] w-full"
            allowFullScreen
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
      ) : (
        <div className="flex h-[200px] items-center justify-center rounded-2xl border border-dashed border-white/20 bg-white/5">
          <p className="text-sm text-slate-500">
            Map unavailable — set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
          </p>
        </div>
      )}

      <div className="space-y-2">
        {data.hospitals.map((hospital: NearbyHospital) => (
          <a
            key={hospital.place_id}
            href={`https://www.google.com/maps/place/?q=place_id:${hospital.place_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 rounded-2xl border border-white/10 bg-ink/70 p-3 transition hover:bg-white/10"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-critical/20 text-critical text-sm font-bold">
              H
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-white truncate">{hospital.name}</p>
              <p className="text-xs text-slate-400 truncate">{hospital.address}</p>
              {hospital.rating != null && (
                <p className="mt-1 text-xs text-signal">
                  ★ {hospital.rating.toFixed(1)}
                  {hospital.open_now != null && (
                    <span className={hospital.open_now ? "text-emerald-400 ml-2" : "text-slate-500 ml-2"}>
                      {hospital.open_now ? "Open now" : "Closed"}
                    </span>
                  )}
                </p>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
