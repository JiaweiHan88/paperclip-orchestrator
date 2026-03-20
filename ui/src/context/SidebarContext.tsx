import { createContext, useCallback, useContext, useState, useEffect, type ReactNode } from "react";

export const SIDEBAR_DEFAULT_WIDTH = 240; // px — w-60
export const SIDEBAR_MIN_WIDTH = 48;      // px — icon-only rail
export const SIDEBAR_COLLAPSE_THRESHOLD = 120; // px — snap to icon-only below this
export const SIDEBAR_ICON_WIDTH = 48;     // px — collapsed icon rail width

const STORAGE_KEY = "paperclip.sidebarWidth";

function readStoredWidth(): number {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const n = parseInt(raw, 10);
      if (!isNaN(n) && n >= SIDEBAR_MIN_WIDTH) return n;
    }
  } catch { /* ignore */ }
  return SIDEBAR_DEFAULT_WIDTH;
}

interface SidebarContextValue {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  isMobile: boolean;
  /** Current sidebar width in px (desktop only). */
  sidebarWidth: number;
  setSidebarWidth: (width: number) => void;
  /** True when sidebar is in icon-only collapsed mode. */
  isCollapsed: boolean;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

const MOBILE_BREAKPOINT = 768;

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < MOBILE_BREAKPOINT);
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= MOBILE_BREAKPOINT);
  const [sidebarWidth, setSidebarWidthRaw] = useState<number>(() => readStoredWidth());

  const isCollapsed = sidebarWidth <= SIDEBAR_COLLAPSE_THRESHOLD;

  const setSidebarWidth = useCallback((width: number) => {
    const clamped = Math.max(SIDEBAR_MIN_WIDTH, width);
    setSidebarWidthRaw(clamped);
    try { window.localStorage.setItem(STORAGE_KEY, String(clamped)); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
      setSidebarOpen(!e.matches);
    };
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  const toggleSidebar = useCallback(() => setSidebarOpen((v) => !v), []);

  return (
    <SidebarContext.Provider value={{ sidebarOpen, setSidebarOpen, toggleSidebar, isMobile, sidebarWidth, setSidebarWidth, isCollapsed }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    throw new Error("useSidebar must be used within SidebarProvider");
  }
  return ctx;
}
