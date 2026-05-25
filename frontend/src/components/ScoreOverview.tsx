import type { ReviewItem } from "../types/reviews";
import { getReviewScore } from "../utils/reviewHelpers";

type ScoreOverviewProps = {
  reviews: ReviewItem[];
};

export function ScoreOverview({ reviews }: ScoreOverviewProps) {
  const scores = reviews.map(getReviewScore);
  const total = reviews.length;
  const avg = total > 0 ? scores.reduce((a, b) => a + b, 0) / total : 0;

  const high = scores.filter((s) => s >= 60).length;
  const medium = scores.filter((s) => s >= 30 && s < 60).length;
  const low = scores.filter((s) => s < 30).length;

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm lg:col-span-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
            Корисність відгуків
          </p>
          <h2 className="text-xl font-bold text-stone-800">Розподіл оцінок</h2>
          <p className="mt-1 text-sm text-stone-400">
            На основі LLM-оцінки корисності (0–100)
          </p>
        </div>
        <div className="rounded-2xl bg-stone-50 border border-stone-200 px-5 py-4 text-center shrink-0">
          <p className="text-xs text-stone-400 mb-1">Середній score</p>
          <p className="text-3xl font-extrabold text-stone-800 tabular-nums">
            {avg.toFixed(0)}
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <ScoreBar label="Корисні" sublabel="score ≥ 60" count={high} total={total} color="green" />
        <ScoreBar label="Середні" sublabel="30–59" count={medium} total={total} color="amber" />
        <ScoreBar label="Некорисні" sublabel="< 30" count={low} total={total} color="red" />
      </div>
    </section>
  );
}

function ScoreBar({
  label,
  sublabel,
  count,
  total,
  color,
}: {
  label: string;
  sublabel: string;
  count: number;
  total: number;
  color: "green" | "amber" | "red";
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;

  const barColors = {
    green: "bg-green-400",
    amber: "bg-amber-400",
    red: "bg-red-400",
  };
  const textColors = {
    green: "text-green-700",
    amber: "text-amber-700",
    red: "text-red-600",
  };
  const bgColors = {
    green: "bg-green-50",
    amber: "bg-amber-50",
    red: "bg-red-50",
  };

  return (
    <div className={`rounded-2xl ${bgColors[color]} p-4`}>
      <div className="flex justify-between items-baseline mb-3">
        <div>
          <p className={`text-sm font-semibold ${textColors[color]}`}>{label}</p>
          <p className="text-xs text-stone-400 mt-0.5">{sublabel}</p>
        </div>
        <p className={`text-2xl font-extrabold tabular-nums ${textColors[color]}`}>
          {count}
        </p>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/70">
        <div
          className={`h-full rounded-full ${barColors[color]} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-stone-400">{pct}%</p>
    </div>
  );
}
