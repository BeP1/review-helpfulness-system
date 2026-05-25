import { isValidRozetkaUrl } from "../utils/reviewHelpers";

const EXAMPLE_URLS = [
  "https://rozetka.com.ua/ua/572786335/p572786335/comments/",
  "https://rozetka.com.ua/ua/samsung-sm-r630nzaasek/p440057501/",
];

type ControlPanelProps = {
  url: string;
  maxPages: number;
  isLoading: boolean;
  error: string | null;
  onUrlChange: (value: string) => void;
  onMaxPagesChange: (value: number) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function ControlPanel({
  url,
  maxPages,
  isLoading,
  error,
  onUrlChange,
  onMaxPagesChange,
  onSubmit,
}: ControlPanelProps) {
  const urlTouched = url.trim().length > 0;
  const urlValid = urlTouched ? isValidRozetkaUrl(url) : null;

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-1">
        <span className="size-2 rounded-full bg-orange-400" />
        <p className="text-xs font-semibold tracking-widest uppercase text-stone-400">
          Input
        </p>
      </div>
      <h2 className="mt-2 text-xl font-bold text-stone-800">Запустити аналіз</h2>
      <p className="mt-1 text-sm text-stone-400 leading-relaxed">
        Підтримуються тільки товари з{" "}
        <span className="font-medium text-stone-500">rozetka.com.ua</span>
      </p>

      <form onSubmit={onSubmit} className="mt-5 space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
            URL товару
          </label>
          <textarea
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            rows={3}
            required
            placeholder="https://rozetka.com.ua/ua/…/p123456/"
            className={[
              "w-full resize-none rounded-xl border bg-stone-50 px-4 py-3 text-sm text-stone-800 outline-none transition",
              "placeholder:text-stone-300",
              "focus:bg-white focus:ring-2 focus:ring-orange-200",
              urlValid === false
                ? "border-red-300 focus:border-red-300 focus:ring-red-100"
                : urlValid === true
                  ? "border-green-300 focus:border-green-300 focus:ring-green-100"
                  : "border-stone-200 focus:border-orange-300",
            ].join(" ")}
          />
          {urlValid === false && (
            <p className="mt-1.5 text-xs text-red-500">
              Тільки посилання на товар з rozetka.com.ua
            </p>
          )}
          {urlValid === true && (
            <p className="mt-1.5 text-xs text-green-600">Посилання валідне ✓</p>
          )}

          <div className="mt-2 space-y-1">
            {EXAMPLE_URLS.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => onUrlChange(ex)}
                className="block w-full truncate text-left text-xs text-stone-300 hover:text-orange-400 transition"
              >
                → {ex}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-stone-400">
              Сторінок відгуків
            </label>
            <span className="text-sm font-bold text-stone-700 tabular-nums">
              {maxPages}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            value={maxPages}
            onChange={(e) => onMaxPagesChange(Number(e.target.value))}
            className="w-full accent-orange-400"
          />
          <div className="flex justify-between text-xs text-stone-300 mt-0.5">
            <span>1</span>
            <span>5</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || urlValid !== true}
          className="w-full rounded-xl bg-stone-800 px-5 py-3 text-sm font-bold text-white transition hover:bg-stone-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isLoading ? "Обробка…" : "Аналізувати відгуки →"}
        </button>
      </form>

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600 leading-relaxed">
          {error}
        </div>
      )}
    </section>
  );
}
