import { useMemo, useState } from "react";

import { analyzeProductReviews } from "../api/reviewsApi";
import { ControlPanel } from "../components/ControlPanel";
import { MetricCard } from "../components/MetricCard";
import { ProductPanel } from "../components/ProductPanel";
import { ReviewCard } from "../components/ReviewCard";
import { ScoreOverview } from "../components/ScoreOverview";
import { StatusPanel } from "../components/StatusPanel";
import type {
  FilterMode,
  ReviewAnalysisResponse,
  ReviewItem,
  SortMode,
} from "../types/reviews";
import { getReviewScore } from "../utils/reviewHelpers";

export function ReviewAnalysisPage() {
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(1);
  const [result, setResult] = useState<ReviewAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<FilterMode>("all");
  const [sortMode, setSortMode] = useState<SortMode>("score_desc");
  const [search, setSearch] = useState("");

  const reviews: ReviewItem[] = result?.reviews ?? [];

  const filteredReviews = useMemo(() => {
    const q = search.trim().toLowerCase();

    return reviews
      .filter((review) => {
        const score = getReviewScore(review);
        if (filter === "high" && score < 60) return false;
        if (filter === "medium" && (score < 30 || score >= 60)) return false;
        if (filter === "low" && score >= 30) return false;

        if (!q) return true;

        const searchable = [
          review.author,
          review.text,
          review.summary,
          review.explanation,
          review.review_text_for_llm,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchable.includes(q);
      })
      .sort((a, b) => {
        if (sortMode === "score_desc") return getReviewScore(b) - getReviewScore(a);
        if (sortMode === "score_asc") return getReviewScore(a) - getReviewScore(b);
        if (sortMode === "rating_desc") return Number(b.rating ?? 0) - Number(a.rating ?? 0);
        if (sortMode === "rating_asc") return Number(a.rating ?? 0) - Number(b.rating ?? 0);
        return 0;
      });
  }, [reviews, filter, sortMode, search]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeProductReviews({ url, max_pages: maxPages });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Невідома помилка");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 text-stone-800">
      {/* Top bar */}
      <header className="sticky top-0 z-10 border-b border-stone-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <span className="size-2 rounded-full bg-orange-400" />
            <span className="text-sm font-bold tracking-wide text-stone-700">
              ReviewIntel
            </span>
            <span className="text-stone-300">/</span>
            <span className="text-xs text-stone-400">rozetka.com.ua</span>
          </div>
          <span
            className={[
              "rounded-full px-3 py-1 text-xs font-medium",
              isLoading
                ? "bg-amber-100 text-amber-700"
                : result
                  ? "bg-green-100 text-green-700"
                  : "bg-stone-100 text-stone-400",
            ].join(" ")}
          >
            {isLoading ? "Running…" : result ? "Done" : "Idle"}
          </span>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-8 space-y-6">
        {/* Hero */}
        <div className="rounded-2xl border border-stone-200 bg-white px-8 py-10 shadow-sm overflow-hidden relative">
          <div className="absolute right-0 top-0 w-64 h-64 rounded-full bg-orange-100/60 blur-3xl translate-x-1/3 -translate-y-1/3 pointer-events-none" />
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">
            LLM-powered · тільки Rozetka
          </p>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-800 leading-tight max-w-xl">
            Аналіз відгуків<br />
            <span className="text-stone-400 font-medium">без зайвого шуму</span>
          </h1>
          <p className="mt-3 text-stone-400 text-sm leading-relaxed max-w-lg">
            Вставте посилання на товар — система запустить парсинг, препроцесинг,
            LLM-аналіз та оцінку корисності кожного відгуку.
          </p>
        </div>

        {/* Input + Status */}
        <div className="grid gap-5 lg:grid-cols-2">
          <ControlPanel
            url={url}
            maxPages={maxPages}
            isLoading={isLoading}
            error={error}
            onUrlChange={setUrl}
            onMaxPagesChange={setMaxPages}
            onSubmit={handleSubmit}
          />
          <StatusPanel isLoading={isLoading} hasResult={Boolean(result)} />
        </div>

        {result && (
          <>
            {/* Product */}
            <ProductPanel
              product={result.product}
              fallbackStore={result.store}
              fallbackUrl={result.url}
            />

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <MetricCard
                label="Parsed"
                value={result.raw_reviews_count ?? 0}
                helper="Отримано з Rozetka"
              />
              <MetricCard
                label="Prepared"
                value={result.prepared_reviews_count ?? 0}
                helper="Після очистки"
              />
              <MetricCard
                label="Analyzed"
                value={result.analyzed_reviews_count ?? 0}
                helper="LLM-аналіз"
              />
              <MetricCard
                label="Saved"
                value={result.saved_reviews_count ?? 0}
                helper="Записано в БД"
                accent
              />
            </div>

            {/* Score overview + DB info */}
            <div className="grid gap-5 lg:grid-cols-3">
              <ScoreOverview reviews={reviews} />

              <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
                  База даних
                </p>
                <h2 className="text-xl font-bold text-stone-800 mb-5">Результат збереження</h2>
                <div className="space-y-2">
                  {[
                    ["Evaluated", result.evaluated_reviews_count],
                    ["Saved reviews", result.saved_reviews_count],
                    ["Saved analyses", result.saved_analyses_count],
                    ["Product DB ID", result.product_id ?? "—"],
                  ].map(([label, value]) => (
                    <div
                      key={String(label)}
                      className="flex justify-between items-center rounded-xl bg-stone-50 px-4 py-2.5 text-sm"
                    >
                      <span className="text-stone-400">{label}</span>
                      <span className="font-semibold text-stone-700 tabular-nums">
                        {value ?? 0}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            {/* Reviews list */}
            <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between mb-5">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
                    Відгуки
                  </p>
                  <h2 className="text-xl font-bold text-stone-800">
                    Оброблені відгуки
                  </h2>
                  <p className="mt-1 text-sm text-stone-400">
                    {filteredReviews.length} з {reviews.length}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2.5">
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Пошук…"
                    className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm outline-none transition w-48 focus:border-stone-300 focus:bg-white focus:ring-2 focus:ring-stone-100 placeholder:text-stone-300"
                  />
                  <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value as FilterMode)}
                    className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm text-stone-600 outline-none transition focus:border-stone-300 focus:bg-white"
                  >
                    <option value="all">Всі відгуки</option>
                    <option value="high">Корисні (≥60)</option>
                    <option value="medium">Середні (30–59)</option>
                    <option value="low">Некорисні (&lt;30)</option>
                  </select>
                  <select
                    value={sortMode}
                    onChange={(e) => setSortMode(e.target.value as SortMode)}
                    className="rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm text-stone-600 outline-none transition focus:border-stone-300 focus:bg-white"
                  >
                    <option value="score_desc">Score: від більшого</option>
                    <option value="score_asc">Score: від меншого</option>
                    <option value="rating_desc">Rating: від більшого</option>
                    <option value="rating_asc">Rating: від меншого</option>
                    <option value="original">Оригінальний порядок</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3">
                {filteredReviews.map((review, i) => (
                  <ReviewCard
                    key={review.review_id ?? i}
                    review={review}
                    index={i}
                  />
                ))}
                {filteredReviews.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-stone-200 p-12 text-center text-sm text-stone-300">
                    Нічого не знайдено
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
