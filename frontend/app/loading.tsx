export default function Loading() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.25fr_0.85fr]">
      <div className="h-[460px] animate-pulse rounded-[32px] border border-white/10 bg-white/5" />
      <div className="space-y-6">
        <div className="h-[220px] animate-pulse rounded-[32px] border border-white/10 bg-white/5" />
        <div className="h-[220px] animate-pulse rounded-[32px] border border-white/10 bg-white/5" />
      </div>
    </div>
  );
}

