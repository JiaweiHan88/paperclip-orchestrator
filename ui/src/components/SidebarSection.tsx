import type { ReactNode } from "react";
import { useSidebar } from "../context/SidebarContext";

interface SidebarSectionProps {
  label: string;
  children: ReactNode;
}

export function SidebarSection({ label, children }: SidebarSectionProps) {
  const { isCollapsed } = useSidebar();
  return (
    <div className="w-full">
      {!isCollapsed && (
        <div className="px-3 py-1.5 text-[10px] font-medium uppercase tracking-widest font-mono text-muted-foreground/60">
          {label}
        </div>
      )}
      {isCollapsed && <div className="border-t border-border/50 mx-2 my-1" />}
      <div className="flex flex-col gap-0.5 mt-0.5 w-full">{children}</div>
    </div>
  );
}
