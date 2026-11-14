import { ReactNode, useEffect, useRef, useState } from "react";
import { animate, motion, useInView, type Variants } from "framer-motion";
import { AlertTriangle, Loader2 } from "lucide-react";

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
};

export const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
};

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="mb-8 flex flex-wrap items-end justify-between gap-4"
    >
      <div className="max-w-2xl">
        <motion.p variants={fadeUp} className="eyebrow">
          {eyebrow}
        </motion.p>
        <motion.h1
          variants={fadeUp}
          className="mt-2 font-display text-3xl font-semibold tracking-tight sm:text-4xl"
        >
          {title}
        </motion.h1>
        {description && (
          <motion.p variants={fadeUp} className="mt-3 text-[15px] leading-relaxed text-muted">
            {description}
          </motion.p>
        )}
      </div>
      {actions && <motion.div variants={fadeUp}>{actions}</motion.div>}
    </motion.div>
  );
}

export function Panel({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`panel ${className}`}
    >
      {children}
    </motion.div>
  );
}

export function CountUp({
  value,
  decimals = 0,
  suffix = "",
}: {
  value: number | null | undefined;
  decimals?: number;
  suffix?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView || value == null || Number.isNaN(value)) return;
    const controls = animate(0, value, {
      duration: 1.4,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: setDisplay,
    });
    return () => controls.stop();
  }, [inView, value]);

  if (value == null || Number.isNaN(value)) return <span ref={ref}>—</span>;
  return (
    <span ref={ref} className="tabular-nums">
      {display.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}

export function StatCard({
  label,
  value,
  decimals,
  suffix,
  icon,
  tone = "cyan",
  hint,
  index = 0,
}: {
  label: string;
  value: number | null | undefined;
  decimals?: number;
  suffix?: string;
  icon: ReactNode;
  tone?: "cyan" | "violet" | "ok" | "warn" | "risk";
  hint?: string;
  index?: number;
}) {
  const tones = {
    cyan: "text-cyan bg-cyan/10 ring-cyan/20",
    violet: "text-violet-soft bg-violet/10 ring-violet/20",
    ok: "text-ok bg-ok/10 ring-ok/20",
    warn: "text-warn bg-warn/10 ring-warn/20",
    risk: "text-risk bg-risk/10 ring-risk/20",
  };
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.06 * index, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
      className="panel group overflow-hidden"
    >
      <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-cyan/10 opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100" />
      <div className="flex items-start justify-between">
        <p className="text-sm text-muted">{label}</p>
        <span className={`grid h-9 w-9 place-items-center rounded-lg ring-1 ${tones[tone]}`}>
          {icon}
        </span>
      </div>
      <p className="mt-4 font-display text-3xl font-semibold tracking-tight">
        <CountUp value={value} decimals={decimals} suffix={suffix} />
      </p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </motion.div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "cyan" | "ok" | "warn" | "risk" | "violet";
}) {
  const tones = {
    neutral: "bg-white/5 text-muted ring-line",
    cyan: "bg-cyan/10 text-cyan ring-cyan/25",
    ok: "bg-ok/10 text-ok ring-ok/25",
    warn: "bg-warn/10 text-warn ring-warn/25",
    risk: "bg-risk/10 text-risk ring-risk/25",
    violet: "bg-violet/10 text-violet-soft ring-violet/25",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-xl bg-white/[0.04] ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="panel flex items-start gap-4 border-risk/30"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-risk/10 text-risk">
        <AlertTriangle size={18} />
      </span>
      <div>
        <p className="font-semibold">Couldn’t reach the SCOPE API</p>
        <p className="mt-1 text-sm text-muted">
          {message}. Make sure FastAPI is running on <code className="font-mono text-cyan">:8000</code>.
        </p>
      </div>
    </motion.div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Loader2 size={16} className="animate-spin" />
      {label}
    </span>
  );
}

export function EmptyState({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="relative mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-cyan/10 text-cyan ring-1 ring-cyan/20">
        <span className="absolute inset-0 animate-pulse-ring rounded-2xl ring-1 ring-cyan/30" />
        {icon}
      </div>
      <p className="font-display font-semibold">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-muted">{text}</p>
    </div>
  );
}

export const chartTheme = {
  grid: "rgba(148,163,184,0.10)",
  axis: "#8A9AB5",
  tooltip: {
    contentStyle: {
      background: "rgba(15,23,41,0.95)",
      border: "1px solid rgba(148,163,184,0.18)",
      borderRadius: 12,
      color: "#E6EDF7",
      fontSize: 12,
    },
    itemStyle: { color: "#E6EDF7" },
    labelStyle: { color: "#8A9AB5" },
  },
};
