import { Route, Routes, useLocation } from "react-router-dom";

import { Sidebar } from "./components/Sidebar";
import AlertDetail from "./pages/AlertDetail";
import Alerts from "./pages/Alerts";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/alerts": "Alerts",
  "/reports": "Reports",
  "/chat": "Investigation Chat",
};

function pageTitle(pathname: string): string {
  if (pathname.startsWith("/alerts/")) return "Alert Detail";
  return PAGE_TITLES[pathname] ?? "Dazai Detector";
}

export default function App() {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center border-b border-white/[0.06] px-8">
          <h1 className="text-sm font-medium text-slate-300">{pageTitle(location.pathname)}</h1>
        </header>
        <main className="flex-1 overflow-y-auto p-8">
          <div className="mx-auto max-w-5xl">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/alerts/:id" element={<AlertDetail />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
}
