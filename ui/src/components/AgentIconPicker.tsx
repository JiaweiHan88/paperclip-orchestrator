import { useState, useMemo } from "react";
import {
  Bot,
  Cpu,
  Brain,
  BrainCircuit,
  Zap,
  Rocket,
  Users,
  Earth,
  Waypoints,
  Code,
  Terminal,
  Laptop,
  Server,
  Network,
  HardHat,
  Construction,
  Blocks,
  Component,
  Boxes,
  Palette,
  Pen,
  Layers,
  Shapes,
  MousePointer2,
  Frame,
  LayoutTemplate,
  Crown,
  Briefcase,
  Building2,
  Landmark,
  Megaphone,
  TrendingUp,
  PieChart,
  Presentation,
  Coins,
  Wallet,
  Calculator,
  PiggyBank,
  CreditCard,
  Kanban,
  Clipboard,
  ListTodo,
  Milestone,
  Workflow,
  Gauge,
  Settings,
  GanttChart,
  Timer,
  Repeat,
  LineChart,
  BarChart3,
  Activity,
  Shield,
  ShieldCheck,
  TestTube,
  FlaskConical,
  Scan,
  Bug,
  Telescope,
  Microscope,
  BookOpen,
  ScrollText,
  Compass,
  NotebookPen,
  FileText,
  BookText,
  Cloud,
  FastForward,
  Bolt,
  Rabbit,
  Eye,
  Search,
  Wrench,
  Hammer,
  Lightbulb,
  Sparkles,
  Star,
  Heart,
  Flame,
  Cog,
  Database,
  Globe,
  Lock,
  Mail,
  MessageSquare,
  FileCode,
  GitBranch,
  Package,
  Puzzle,
  Target,
  Wand2,
  Atom,
  CircuitBoard,
  Radar,
  Swords,
  Gem,
  Hexagon,
  Pentagon,
  Fingerprint,
  type LucideIcon,
} from "lucide-react";
import { AGENT_ICON_NAMES, type AgentIconName } from "@paperclipai/shared";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const AGENT_ICONS: Record<AgentIconName, LucideIcon> = {
  // General / identity
  bot: Bot,
  cpu: Cpu,
  brain: Brain,
  "brain-circuit": BrainCircuit,
  zap: Zap,
  rocket: Rocket,
  users: Users,
  earth: Earth,
  waypoints: Waypoints,
  // Engineering
  code: Code,
  terminal: Terminal,
  laptop: Laptop,
  server: Server,
  network: Network,
  "hard-hat": HardHat,
  construction: Construction,
  // Architecture / systems
  blocks: Blocks,
  component: Component,
  boxes: Boxes,
  // Design / UX
  palette: Palette,
  pen: Pen,
  layers: Layers,
  shapes: Shapes,
  "mouse-pointer-2": MousePointer2,
  frame: Frame,
  "layout-template": LayoutTemplate,
  // Leadership / executive
  crown: Crown,
  briefcase: Briefcase,
  "building-2": Building2,
  landmark: Landmark,
  // Marketing
  megaphone: Megaphone,
  "trending-up": TrendingUp,
  "pie-chart": PieChart,
  presentation: Presentation,
  // Finance
  coins: Coins,
  wallet: Wallet,
  calculator: Calculator,
  "piggy-bank": PiggyBank,
  "credit-card": CreditCard,
  // PM / scrum / ops
  kanban: Kanban,
  clipboard: Clipboard,
  "list-todo": ListTodo,
  milestone: Milestone,
  workflow: Workflow,
  gauge: Gauge,
  settings: Settings,
  "gantt-chart": GanttChart,
  timer: Timer,
  repeat: Repeat,
  // Analytics
  "line-chart": LineChart,
  "bar-chart-3": BarChart3,
  activity: Activity,
  // QA / testing
  shield: Shield,
  "shield-check": ShieldCheck,
  "test-tube": TestTube,
  "flask-conical": FlaskConical,
  scan: Scan,
  bug: Bug,
  // Research / science
  telescope: Telescope,
  microscope: Microscope,
  "book-open": BookOpen,
  "scroll-text": ScrollText,
  compass: Compass,
  // Tech writing / docs
  "notebook-pen": NotebookPen,
  "file-text": FileText,
  "book-text": BookText,
  // DevOps / infra
  cloud: Cloud,
  // Speed / automation
  "fast-forward": FastForward,
  bolt: Bolt,
  rabbit: Rabbit,
  // Misc / personality
  eye: Eye,
  search: Search,
  wrench: Wrench,
  hammer: Hammer,
  lightbulb: Lightbulb,
  sparkles: Sparkles,
  star: Star,
  heart: Heart,
  flame: Flame,
  cog: Cog,
  database: Database,
  globe: Globe,
  lock: Lock,
  mail: Mail,
  "message-square": MessageSquare,
  "file-code": FileCode,
  "git-branch": GitBranch,
  package: Package,
  puzzle: Puzzle,
  target: Target,
  wand: Wand2,
  atom: Atom,
  "circuit-board": CircuitBoard,
  radar: Radar,
  swords: Swords,
  gem: Gem,
  hexagon: Hexagon,
  pentagon: Pentagon,
  fingerprint: Fingerprint,
};

const DEFAULT_ICON: AgentIconName = "bot";

export function getAgentIcon(iconName: string | null | undefined): LucideIcon {
  if (iconName && AGENT_ICON_NAMES.includes(iconName as AgentIconName)) {
    return AGENT_ICONS[iconName as AgentIconName];
  }
  return AGENT_ICONS[DEFAULT_ICON];
}

interface AgentIconProps {
  icon: string | null | undefined;
  className?: string;
}

export function AgentIcon({ icon, className }: AgentIconProps) {
  const Icon = getAgentIcon(icon);
  return <Icon className={className} />;
}

interface AgentIconPickerProps {
  value: string | null | undefined;
  onChange: (icon: string) => void;
  children: React.ReactNode;
}

export function AgentIconPicker({ value, onChange, children }: AgentIconPickerProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const entries = AGENT_ICON_NAMES.map((name) => [name, AGENT_ICONS[name]] as const);
    if (!search) return entries;
    const q = search.toLowerCase();
    return entries.filter(([name]) => name.includes(q));
  }, [search]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent className="w-72 p-3" align="start">
        <Input
          placeholder="Search icons..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-2 h-8 text-sm"
          autoFocus
        />
        <div className="grid grid-cols-7 gap-1 max-h-48 overflow-y-auto">
          {filtered.map(([name, Icon]) => (
            <button
              key={name}
              onClick={() => {
                onChange(name);
                setOpen(false);
                setSearch("");
              }}
              className={cn(
                "flex items-center justify-center h-8 w-8 rounded hover:bg-accent transition-colors",
                (value ?? DEFAULT_ICON) === name && "bg-accent ring-1 ring-primary"
              )}
              title={name}
            >
              <Icon className="h-4 w-4" />
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="col-span-7 text-xs text-muted-foreground text-center py-2">No icons match</p>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
