import type { ProductContext } from "../types/reviews";

type ProductPanelProps = {
  product?: ProductContext;
  fallbackStore?: string;
  fallbackUrl?: string;
};

export function ProductPanel({ product, fallbackStore, fallbackUrl }: ProductPanelProps) {
  const productUrl = product?.product_url ?? product?.source_url ?? fallbackUrl;
  const store = product?.store ?? fallbackStore;

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
            Товар
          </p>
          <h2 className="text-lg font-bold text-stone-800 leading-snug">
            {product?.product_name ?? "Analyzed product"}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              ["Магазин", store],
              ["Продавець", product?.seller],
              ["ID", product?.product_id],
            ]
              .filter(([, v]) => v)
              .map(([k, v]) => (
                <span
                  key={k}
                  className="rounded-lg bg-stone-100 px-3 py-1 text-xs text-stone-500"
                >
                  <span className="font-medium text-stone-600">{k}:</span>{" "}
                  {String(v).slice(0, 60)}
                </span>
              ))}
          </div>
        </div>

        {productUrl && (
          <a
            href={productUrl}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 self-start rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm font-medium text-stone-600 transition hover:border-stone-300 hover:bg-white"
          >
            Відкрити ↗
          </a>
        )}
      </div>
    </section>
  );
}
