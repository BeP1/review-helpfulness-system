type MetricCardProps = {
  label: string;
  value: number | string;
  helper?: string;
  accent?: boolean;
};

export function MetricCard({ label, value, helper, accent }: MetricCardProps) {
  return (
    <article
      className={[
        "rounded-2xl border p-5",
        accent
          ? "border-orange-200 bg-orange-50"
          : "border-stone-200 bg-white",
      ].join(" ")}
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-stone-400">
        {label}
      </p>
      <p
        className={[
          "mt-2 text-4xl font-extrabold tabular-nums",
          accent ? "text-orange-500" : "text-stone-800",
        ].join(" ")}
      >
        {value}
      </p>
      {helper && (
        <p className="mt-1 text-xs text-stone-400 leading-snug">{helper}</p>
      )}
    </article>
  );
}
