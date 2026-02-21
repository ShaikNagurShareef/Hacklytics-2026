import { Link } from "react-router-dom";
import {
  Heart,
  Stethoscope,
  UtensilsCrossed,
  MessageCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const flows = [
  {
    to: "/wellbeing",
    title: "Wellbeing",
    description: "Personal wellbeing and mental health support.",
    icon: Heart,
    color: "from-rose-500/10 to-rose-600/5 border-rose-200/60 hover:border-rose-300 dark:border-rose-800/60 dark:hover:border-rose-700/60",
    iconClass: "text-rose-600 dark:text-rose-400",
  },
  {
    to: "/virtual-doctor",
    title: "Virtual Doctor",
    description: "Medical Q&A and image-based analysis.",
    icon: Stethoscope,
    color: "from-primary/10 to-primary/5 border-primary/20 hover:border-primary/40 dark:border-primary/30 dark:hover:border-primary/50",
    iconClass: "text-primary",
  },
  {
    to: "/dietary",
    title: "Dietary",
    description: "Meal plans, nutrition, BMR and TDEE.",
    icon: UtensilsCrossed,
    color: "from-amber-500/10 to-amber-600/5 border-amber-200/60 hover:border-amber-300 dark:border-amber-800/60 dark:hover:border-amber-700/60",
    iconClass: "text-amber-600 dark:text-amber-400",
  },
  {
    to: "/ask",
    title: "Ask MEDORA",
    description: "One place to ask—we route to the right agent.",
    icon: MessageCircle,
    color: "from-emerald-500/10 to-emerald-600/5 border-emerald-200/60 hover:border-emerald-300 dark:border-emerald-800/60 dark:hover:border-emerald-700/60",
    iconClass: "text-emerald-600 dark:text-emerald-400",
  },
];

export function Home() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-2xl border border-border/60 bg-gradient-to-br from-primary/5 via-background to-accent/30 px-6 py-10 sm:px-10 sm:py-14">
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-primary mb-3">
            <Sparkles className="h-5 w-5" />
            <span className="text-sm font-medium">Multi-agent healthcare</span>
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl md:text-5xl">
            Welcome to{" "}
            <span className="bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
              MEDORA
            </span>
          </h1>
          <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
            Choose a flow below to get started. Each agent is here to help—wellbeing, medical guidance, or nutrition.
          </p>
        </div>
      </section>

      {/* Flow cards */}
      <section>
        <h2 className="font-display text-xl font-semibold text-foreground mb-6">
          What do you need?
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {flows.map(({ to, title, description, icon: Icon, color, iconClass }, i) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "group block opacity-0 animate-fade-in-up",
                i === 0 && "animate-stagger-1",
                i === 1 && "animate-stagger-2",
                i === 2 && "animate-stagger-3",
                i === 3 && "animate-stagger-4"
              )}
            >
              <Card
                className={cn(
                  "h-full border-2 bg-card transition-all duration-300 ease-out",
                  "hover:shadow-card-hover hover:-translate-y-1 active:translate-y-0 active:shadow-card",
                  color
                )}
              >
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl bg-background/80 transition-transform duration-300 group-hover:scale-110",
                      iconClass
                    )}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground opacity-0 -translate-x-1 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0" />
                </CardHeader>
                <CardTitle className="text-lg font-display font-semibold text-foreground">
                  {title}
                </CardTitle>
                <CardContent className="pt-1">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {description}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
