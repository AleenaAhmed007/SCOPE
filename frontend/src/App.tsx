import { useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useScroll, useSpring } from "framer-motion";
import {
  BrainCircuit,
  FileSearch,
  Gauge,
  Home,
  Package,
  ShieldCheck,
  Sparkles,
  Truck,
} from "lucide-react";
import api from "./api";
import Overview from "./pages/Overview";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import Vendors from "./pages/Vendors";
import Risk from "./pages/Risk";
import Documents from "./pages/Documents";
import Investigate from "./pages/Investigate";
import Evidence from "./pages/Evidence";

const links = [
  { to: "/", label: "Overview", icon: Home },
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/orders", label: "Orders", icon: Package },
  { to: "/vendors", label: "Vendors", icon: Truck },
  { to: "/risk", label: "Risk", icon: BrainCircuit },
  { to: "/documents", label: "Documents", icon: FileSearch },
  { to: "/investigate", label: "Investigate", icon: Sparkles },
  { to: "/evidence", label: "Evidence", icon: ShieldCheck },
] as const;

function Logo() {
  return (
    <NavLink to="/" className="group flex items-center gap-2.5">
      <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-cyan to-violet">
        <motion.span
          className="absolute inset-[3px] rounded-[9px] bg-void"
          initial={false}
        />
        <motion.svg
          viewBox="0 0 24 24"
          className="relative h-5 w-5"
          animate={{ rotate: 360 }}
          transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
        >
          <circle cx="12" cy="12" r="8" fill="none" stroke="#22D3EE" strokeWidth="1.6" strokeDasharray="3 3" />
          <circle cx="12" cy="12" r="3" fill="#A78BFA" />
        </motion.svg>
      </span>
      <span className="leading-none">
        <span className="block font-display text-lg font-bold tracking-tight">SCOPE</span>
        <span className="hidden font-mono text-[10px] uppercase tracking-widest text-muted sm:block">
          Predictive Evidence
        </span>
      </span>
    </NavLink>
  );
}

function ApiStatus() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    const check = () =>
      api
        .get("/health", { timeout: 4000 })
        .then(() => alive && setOk(true))
        .catch(() => alive && setOk(false));
    check();
    const t = setInterval(check, 20000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);
  const color = ok == null ? "bg-muted" : ok ? "bg-ok" : "bg-risk";
  return (
    <span className="hidden items-center gap-2 rounded-full border border-line bg-white/[0.03] px-3 py-1.5 font-mono text-[11px] text-muted lg:inline-flex">
      <span className="relative flex h-2 w-2">
        {ok && <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${color} opacity-60`} />}
        <span className={`relative inline-flex h-2 w-2 rounded-full ${color}`} />
      </span>
      {ok == null ? "checking" : ok ? "API online" : "API offline"}
    </span>
  );
}

export default function App() {
  const location = useLocation();
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 24 });
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      {/* ambient background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="bg-grid mask-fade absolute inset-0 animate-grid-pan opacity-60" />
        <motion.div
          className="absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-cyan/20 blur-[120px]"
          animate={{ x: [0, 60, 0], y: [0, 40, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute -right-40 top-1/3 h-[520px] w-[520px] rounded-full bg-violet/20 blur-[120px]"
          animate={{ x: [0, -50, 0], y: [0, -60, 0] }}
          transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      <motion.div
        className="fixed inset-x-0 top-0 z-50 h-[2px] origin-left bg-gradient-to-r from-cyan to-violet"
        style={{ scaleX: progress }}
      />

      <header
        className={`sticky top-0 z-40 transition-all duration-300 ${
          scrolled ? "border-b border-line bg-void/75 backdrop-blur-xl" : "border-b border-transparent"
        }`}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-3 sm:px-6">
          <Logo />
          <nav className="no-scrollbar -mr-4 flex flex-1 justify-end overflow-x-auto pr-4 lg:mr-0 lg:pr-0">
            <ul className="flex items-center gap-1 rounded-full border border-line bg-surface/60 p-1 backdrop-blur">
              {links.map(({ to, label, icon: Icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={to === "/"}
                    className={({ isActive }) =>
                      `relative flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${
                        isActive ? "text-void" : "text-muted hover:text-fg"
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <motion.span
                            layoutId="nav-pill"
                            className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan to-violet-soft"
                            transition={{ type: "spring", stiffness: 420, damping: 34 }}
                          />
                        )}
                        <Icon size={14} className="relative" />
                        <span className="relative hidden md:inline">{label}</span>
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <ApiStatus />
        </div>
      </header>

      <AnimatePresence mode="wait">
        <motion.main
          key={location.pathname}
          initial={{ opacity: 0, y: 12, filter: "blur(4px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: -8, filter: "blur(4px)" }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto max-w-7xl px-4 pb-20 pt-8 sm:px-6"
        >
          <Routes location={location}>
            <Route path="/" element={<Overview />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/vendors" element={<Vendors />} />
            <Route path="/risk" element={<Risk />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/investigate" element={<Investigate />} />
            <Route path="/evidence" element={<Evidence />} />
          </Routes>
        </motion.main>
      </AnimatePresence>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-muted sm:px-6">
          <span>SCOPE — Supply Chain Operations and Predictive Evidence System</span>
          <span>Institute of Data Sciences · UET Lahore</span>
        </div>
      </footer>
    </div>
  );
}
