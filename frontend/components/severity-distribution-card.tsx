"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ShieldHalf } from "lucide-react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { SeverityBucket } from "@/lib/types";

export function SeverityDistributionCard({ buckets }: { buckets: SeverityBucket[] }) {
  return (
    <Card className="min-h-[360px]">
      <CardHeader>
        <div>
          <CardTitle>Severity Distribution</CardTitle>
          <CardDescription>Active cases split by urgency level.</CardDescription>
        </div>
        <ShieldHalf className="h-5 w-5 text-signal" />
      </CardHeader>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={buckets}>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis
              dataKey="level"
              stroke="rgba(226,232,240,0.65)"
              tick={{ fill: "rgba(226,232,240,0.65)", fontSize: 12 }}
            />
            <YAxis allowDecimals={false} stroke="rgba(226,232,240,0.65)" tick={{ fill: "rgba(226,232,240,0.65)", fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
              contentStyle={{
                backgroundColor: "rgba(7,17,27,0.92)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "20px"
              }}
            />
            <Bar dataKey="count" fill="rgba(78,232,255,0.75)" radius={[18, 18, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

