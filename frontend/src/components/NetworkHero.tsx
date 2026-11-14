import { motion } from "framer-motion";

/**
 * Animated supply-chain network: suppliers → hubs → SCOPE core → customers.
 * Packets travel along the edges; one supplier edge is flagged as a disruption.
 */
const nodes = {
  s1: [70, 70], s2: [50, 190], s3: [80, 310], s4: [60, 420],
  h1: [230, 130], h2: [220, 290], h3: [250, 400],
  core: [400, 250],
  c1: [560, 110], c2: [590, 230], c3: [570, 350], c4: [540, 440],
} as const;

type K = keyof typeof nodes;

const edges: [K, K, boolean?][] = [
  ["s1", "h1"], ["s2", "h1"], ["s2", "h2", true], ["s3", "h2"], ["s4", "h3"], ["s3", "h3"],
  ["h1", "core"], ["h2", "core"], ["h3", "core"],
  ["core", "c1"], ["core", "c2"], ["core", "c3"], ["core", "c4"],
];

function path(a: K, b: K) {
  const [x1, y1] = nodes[a];
  const [x2, y2] = nodes[b];
  const mx = (x1 + x2) / 2;
  return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
}

export default function NetworkHero() {
  return (
    <div className="relative aspect-[640/500] w-full">
      <div className="absolute inset-0 rounded-full bg-cyan/10 blur-3xl" />
      <svg viewBox="0 0 640 500" className="relative h-full w-full" role="img" aria-label="Animated supply chain network">
        <defs>
          <linearGradient id="edge" x1="0" x2="1">
            <stop offset="0" stopColor="#22D3EE" stopOpacity="0.15" />
            <stop offset="1" stopColor="#8B5CF6" stopOpacity="0.5" />
          </linearGradient>
          <radialGradient id="coreGlow">
            <stop offset="0" stopColor="#22D3EE" stopOpacity="0.55" />
            <stop offset="1" stopColor="#22D3EE" stopOpacity="0" />
          </radialGradient>
        </defs>

        {edges.map(([a, b, bad], i) => {
          const d = path(a, b);
          return (
            <g key={`${a}-${b}`}>
              <motion.path
                d={d}
                fill="none"
                stroke={bad ? "#F87171" : "url(#edge)"}
                strokeWidth={bad ? 1.6 : 1.3}
                strokeDasharray={bad ? "4 5" : undefined}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 1.2, delay: 0.3 + i * 0.07, ease: "easeInOut" }}
              />
              <circle r={bad ? 3.2 : 2.6} fill={bad ? "#F87171" : "#67E8F9"}>
                <animateMotion
                  dur={`${bad ? 4.5 : 2.6 + (i % 4) * 0.5}s`}
                  begin={`${1.4 + i * 0.25}s`}
                  repeatCount="indefinite"
                  path={d}
                />
                <animate
                  attributeName="opacity"
                  values="0;1;1;0"
                  dur={`${bad ? 4.5 : 2.6 + (i % 4) * 0.5}s`}
                  begin={`${1.4 + i * 0.25}s`}
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          );
        })}

        {/* core */}
        <circle cx={400} cy={250} r={90} fill="url(#coreGlow)" />
        <motion.circle
          cx={400}
          cy={250}
          r={44}
          fill="none"
          stroke="#22D3EE"
          strokeOpacity={0.35}
          strokeDasharray="2 6"
          animate={{ rotate: 360 }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: "400px 250px" }}
        />
        <motion.circle
          cx={400}
          cy={250}
          r={58}
          fill="none"
          stroke="#8B5CF6"
          strokeOpacity={0.25}
          strokeDasharray="30 14"
          animate={{ rotate: -360 }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
          style={{ transformOrigin: "400px 250px" }}
        />
        <motion.g
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.9, type: "spring", stiffness: 140, damping: 14 }}
          style={{ transformOrigin: "400px 250px" }}
        >
          <circle cx={400} cy={250} r={30} fill="#0F1729" stroke="#22D3EE" strokeWidth={1.5} />
          <text x={400} y={254} textAnchor="middle" fontFamily="Space Grotesk" fontWeight={700} fontSize={11} fill="#E6EDF7" letterSpacing="1.5">
            SCOPE
          </text>
        </motion.g>

        {(Object.keys(nodes) as K[])
          .filter((k) => k !== "core")
          .map((k, i) => {
            const [x, y] = nodes[k];
            const isSupplier = k.startsWith("s");
            const isHub = k.startsWith("h");
            const flagged = k === "s2";
            const color = flagged ? "#F87171" : isSupplier ? "#22D3EE" : isHub ? "#A78BFA" : "#34D399";
            return (
              <motion.g
                key={k}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 + i * 0.06, type: "spring", stiffness: 200, damping: 15 }}
                style={{ transformOrigin: `${x}px ${y}px` }}
              >
                {flagged && (
                  <circle cx={x} cy={y} r={10} fill="none" stroke="#F87171">
                    <animate attributeName="r" values="9;24" dur="1.8s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.8;0" dur="1.8s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle cx={x} cy={y} r={isHub ? 9 : 7} fill="#0A1020" stroke={color} strokeWidth={1.6} />
                <circle cx={x} cy={y} r={2.6} fill={color} />
              </motion.g>
            );
          })}

        {/* floating labels */}
        <motion.g initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 2 }}>
          <rect x={-2} y={160} width={118} height={22} rx={6} fill="#1a0f14" stroke="#F87171" strokeOpacity={0.5} />
          <text x={8} y={175} fontFamily="JetBrains Mono" fontSize={9.5} fill="#F87171">
            ▲ disruption flag
          </text>
        </motion.g>
        <motion.g initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2.3 }}>
          <rect x={448} y={290} width={132} height={22} rx={6} fill="#0b1a17" stroke="#34D399" strokeOpacity={0.5} />
          <text x={458} y={305} fontFamily="JetBrains Mono" fontSize={9.5} fill="#34D399">
            ✓ claim verified
          </text>
        </motion.g>
      </svg>
    </div>
  );
}
