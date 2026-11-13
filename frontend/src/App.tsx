import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import Vendors from "./pages/Vendors";
import Risk from "./pages/Risk";
import Documents from "./pages/Documents";
import Investigate from "./pages/Investigate";
import Evidence from "./pages/Evidence";

const links = [
  ["/", "Dashboard"],
  ["/orders", "Orders"],
  ["/vendors", "Vendors"],
  ["/risk", "Risk"],
  ["/documents", "Documents"],
  ["/investigate", "Investigate"],
  ["/evidence", "Evidence"],
] as const;

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-ink/10 bg-ink text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-6 py-5">
          <div>
            <p className="font-display text-3xl tracking-tight">SCOPE</p>
            <p className="text-sm text-white/70">
              Supply Chain Operations and Predictive Evidence
            </p>
          </div>
          <nav className="flex flex-wrap gap-2">
            {links.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm ${
                    isActive ? "bg-sea text-white" : "bg-white/10 hover:bg-white/20"
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/investigate" element={<Investigate />} />
          <Route path="/evidence" element={<Evidence />} />
        </Routes>
      </main>
    </div>
  );
}
