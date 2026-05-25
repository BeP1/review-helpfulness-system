import { useEffect, useState } from "react";

type StatusPanelProps = {
  isLoading: boolean;
  hasResult: boolean;
};

const STEPS = [
  { label: "Парсинг відгуків", sub: "Завантаження сторінок з Rozetka" },
  { label: "Препроцесинг", sub: "Очистка та нормалізація тексту" },
  { label: "LLM-аналіз", sub: "Оцінка корисності кожного відгуку" },
  { label: "Evaluation", sub: "Підрахунок фінального score" },
  { label: "Збереження", sub: "Запис результатів у базу даних" },
];

export function StatusPanel({ isLoading, hasResult }: StatusPanelProps) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setActiveStep(0);
      return;
    }
    setActiveStep(0);
    const interval = setInterval(() => {
      setActiveStep((s) => Math.min(s + 1, STEPS.length - 1));
    }, 1800);
    return () => clearInterval(interval);
  }, [isLoading]);

  const status = isLoading ? "running" : hasResult ? "done" : "idle";

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span
            className={[
              "size-2 rounded-full",
              status === "running"
                ? "bg-amber-400 animate-pulse"
                : status === "done"
                  ? "bg-green-400"
                  : "bg-stone-300",
            ].join(" ")}
          />
          <p className="text-xs font-semibold tracking-widest uppercase text-stone-400">
            Pipeline
          </p>
        </div>
        <span
          className={[
            "text-xs font-medium px-2.5 py-1 rounded-full",
            status === "running"
              ? "bg-amber-50 text-amber-600"
              : status === "done"
                ? "bg-green-50 text-green-600"
                : "bg-stone-100 text-stone-400",
          ].join(" ")}
        >
          {status === "running" ? "Running" : status === "done" ? "Done" : "Idle"}
        </span>
      </div>
      <h2 className="mt-2 text-xl font-bold text-stone-800">Статус виконання</h2>

      {isLoading && (
        <div className="mt-4 mb-5 h-1 w-full rounded-full bg-stone-100 overflow-hidden">
          <div
            className="h-full bg-amber-400 rounded-full transition-all duration-500"
            style={{ width: `${((activeStep + 1) / STEPS.length) * 100}%` }}
          />
        </div>
      )}

      <div className="mt-5 space-y-2">
        {STEPS.map((step, i) => {
          const isDone = hasResult || (isLoading && i < activeStep);
          const isActive = isLoading && i === activeStep;

          return (
            <div
              key={step.label}
              className={[
                "flex items-center gap-4 rounded-xl p-3 transition-all",
                isActive ? "bg-amber-50" : isDone ? "bg-stone-50" : "bg-transparent",
              ].join(" ")}
            >
              <div
                className={[
                  "flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all",
                  isDone
                    ? "bg-green-100 text-green-600"
                    : isActive
                      ? "bg-amber-100 text-amber-600"
                      : "bg-stone-100 text-stone-400",
                ].join(" ")}
              >
                {isDone ? "✓" : i + 1}
              </div>
              <div>
                <p
                  className={[
                    "text-sm font-semibold",
                    isActive ? "text-stone-800" : isDone ? "text-stone-600" : "text-stone-400",
                  ].join(" ")}
                >
                  {step.label}
                </p>
                <p className="text-xs text-stone-400 mt-0.5">{step.sub}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
