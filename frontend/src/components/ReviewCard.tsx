import { useState } from "react";
import type { ReviewItem } from "../types/reviews";
import { getReviewScore, getScoreTier } from "../utils/reviewHelpers";

type ReviewCardProps = {
  review: ReviewItem;
  index: number;
};

export function ReviewCard({ review, index }: ReviewCardProps) {
  const [expanded, setExpanded] = useState(false);

  const score = getReviewScore(review);
  const tier = getScoreTier(score);
  const text = review.text ?? review.review_text_for_llm ?? "";
  const isLong = text.length > 240;
  const features = review.usefulness?.features ?? {};
  const hasFeatures = Object.keys(features).length > 0;

  const tierStyles = {
    high: { badge: "bg-green-100 text-green-700", score: "text-green-700", label: "Корисний" },
    medium: { badge: "bg-amber-100 text-amber-700", score: "text-amber-700", label: "Середній" },
    low: { badge: "bg-red-100 text-red-600", score: "text-red-600", label: "Некорисний" },
  };
  const ts = tierStyles[tier];

  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-5 transition hover:border-stone-300 hover:shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="text-xs font-mono text-stone-300">
              #{String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-sm font-semibold text-stone-800">
              {review.author ?? "Анонім"}
            </span>
            <span className="text-xs text-stone-400">
              {review.created_at ?? review.date ?? ""}
            </span>
            {review.rating != null && (
              <StarRating rating={review.rating} />
            )}
            {review.usefulness?.is_helpful === false && (
              <Tag color="red">not helpful</Tag>
            )}
            {review.classification?.topic_category === "low_information" && (
              <Tag color="stone">low info</Tag>
            )}
            {review.classification?.sentiment && (
              <Tag color="stone">{review.classification.sentiment}</Tag>
            )}
          </div>

          <p
            className={[
              "text-sm text-stone-600 leading-relaxed",
              !expanded && isLong ? "line-clamp-3" : "",
            ].join(" ")}
          >
            {text || <span className="text-stone-300 italic">Текст відсутній</span>}
          </p>

          {isLong && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="mt-1.5 text-xs text-stone-400 hover:text-stone-600 transition"
            >
              {expanded ? "Згорнути ↑" : "Читати далі ↓"}
            </button>
          )}
        </div>

        {/* Score pill */}
        <div className="shrink-0 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-center min-w-[76px]">
          <p className={`text-2xl font-extrabold tabular-nums ${ts.score}`}>
            {score}
          </p>
          <p className="text-xs text-stone-400 mt-0.5">score</p>
          <span className={`mt-1.5 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${ts.badge}`}>
            {ts.label}
          </span>
        </div>
      </div>

      {/* Summary / Explanation */}
      {(review.summary || review.explanation) && (
        <div className="mt-4 rounded-xl bg-stone-50 border border-stone-100 p-4 space-y-1.5">
          {review.summary && (
            <p className="text-xs font-medium text-stone-600 leading-relaxed">
              {review.summary}
            </p>
          )}
          {review.explanation && (
            <p className="text-xs text-stone-400 leading-relaxed">
              {review.explanation}
            </p>
          )}
        </div>
      )}

      {/* Feature breakdown */}
      {hasFeatures && (
        <div className="mt-4 pt-4 border-t border-stone-100">
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-300 mb-3">
            Breakdown
          </p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-3">
            {Object.entries(features).map(([key, val]) => (
              <FeatureRow key={key} label={key} value={val ?? 0} />
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

function FeatureRow({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, (value / 10) * 100));
  const color =
    value >= 6 ? "bg-green-400" : value >= 3 ? "bg-amber-400" : "bg-red-400";

  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-[11px] text-stone-400 capitalize">
          {label.replace(/_/g, " ")}
        </span>
        <span className="text-[11px] font-semibold tabular-nums text-stone-600">
          {value}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-stone-100">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.round(rating);
  return (
    <span className="text-xs tracking-tight" aria-label={`${rating} зірок`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < full ? "text-amber-400" : "text-stone-200"}>
          ★
        </span>
      ))}
    </span>
  );
}

function Tag({ children, color }: { children: React.ReactNode; color: "red" | "stone" }) {
  const cls =
    color === "red"
      ? "bg-red-50 text-red-500 border border-red-100"
      : "bg-stone-100 text-stone-400 border border-stone-200";

  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${cls}`}>
      {children}
    </span>
  );
}
