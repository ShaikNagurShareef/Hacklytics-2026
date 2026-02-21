import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, useInView, useReducedMotion } from "framer-motion";
import {
  ChevronDown,
  Clock,
  AlertCircle,
  Heart,
  Check,
  MessageCircle,
  Sparkles,
  Shield,
  FlaskConical,
  Globe,
  Lock,
  Sun,
  Moon,
  ArrowRight,
  Stethoscope,
  UtensilsCrossed,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

// --- Hooks ---

// --- Components ---

function FadeInUp({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const shouldReduceMotion = useReducedMotion();
  
  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// --- Main Page ---

export function About() {
  const [isDark, setIsDark] = useState(true);
  const shouldReduceMotion = useReducedMotion();

  // Toggle dark mode
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  return (
    <div className="min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      
      {/* Navigation */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/ask" className="flex items-center gap-2 font-bold text-xl tracking-tight hover:opacity-80 transition-opacity">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-violet-500 flex items-center justify-center text-white">
                <Heart className="h-4 w-4 fill-current" />
              </div>
              MEDORA
            </Link>
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
              <Link to="/about" className="text-foreground transition-colors">About</Link>
              <Link to="/ask" className="hover:text-foreground transition-colors">Product</Link>
              <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsDark(!isDark)}
              className="rounded-full w-9 h-9"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button asChild className="hidden sm:flex rounded-full px-6">
              <Link to="/ask">Get Started</Link>
            </Button>
          </div>
        </div>
      </nav>

      <main className="pt-16">
        {/* Hero Section */}
        <section className="relative min-h-[90vh] flex flex-col items-center justify-center overflow-hidden px-6 py-20">
          
          {/* Background Effects */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-primary/20 rounded-full blur-[120px] opacity-20 animate-pulse" />
            <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-violet-500/10 rounded-full blur-[100px] opacity-20" />
            <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-[80px] opacity-20" />
            <div 
              className="absolute inset-0 bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" 
              style={{
                backgroundImage: "linear-gradient(rgba(150, 150, 150, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(150, 150, 150, 0.1) 1px, transparent 1px)",
                backgroundSize: "24px 24px"
              }}
            />
          </div>

          <div className="relative z-10 max-w-4xl mx-auto text-center space-y-8">
            <FadeInUp>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold uppercase tracking-wider mb-6">
                <Sparkles className="h-3 w-3" />
                AI-Powered Health Companion
              </div>
            </FadeInUp>
            
            <FadeInUp delay={0.1}>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight leading-[1.1] mb-6 bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/50">
                Healthcare,<br /> Reimagined.
              </h1>
            </FadeInUp>

            <FadeInUp delay={0.2}>
              <p className="text-lg sm:text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                We're building the future of AI-powered health — accessible, personal, and always there when you need it.
              </p>
            </FadeInUp>

            <FadeInUp delay={0.3}>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
                <Button size="lg" className="rounded-full h-12 px-8 text-base shadow-lg shadow-primary/20" asChild>
                  <Link to="/ask">
                    Start Your Journey
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" className="rounded-full h-12 px-8 text-base bg-background/50 backdrop-blur-sm" asChild>
                  <Link to="#mission">Learn More</Link>
                </Button>
              </div>
            </FadeInUp>
          </div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity, delay: 1 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2 text-muted-foreground/50"
          >
            <ChevronDown className="h-8 w-8" />
          </motion.div>
        </section>

        {/* Mission Statement */}
        <section id="mission" className="py-24 md:py-32 px-6 relative overflow-hidden">
          <div className="max-w-4xl mx-auto text-center relative z-10">
            <FadeInUp>
              <blockquote className="text-2xl md:text-4xl lg:text-5xl font-serif font-medium leading-tight text-foreground/90">
                "We believe everyone deserves a health companion that listens, understands, and guides — without judgment, without wait times, without barriers."
              </blockquote>
            </FadeInUp>
          </div>
        </section>

        {/* The Problem */}
        <section className="py-24 px-6 bg-muted/30">
          <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <FadeInUp>
                <div className="inline-flex items-center gap-2 text-primary font-semibold uppercase tracking-wider text-sm">
                  <AlertCircle className="h-4 w-4" />
                  The Problem
                </div>
                <h2 className="text-3xl md:text-5xl font-bold tracking-tight mt-4">
                  Healthcare is broken.
                </h2>
              </FadeInUp>
              
              <div className="space-y-4">
                {[
                  { icon: Clock, text: "8 weeks average wait for a specialist", delay: 0.1 },
                  { icon: AlertCircle, text: "30% of symptoms are misdiagnosed online", delay: 0.2 },
                  { icon: Heart, text: "Mental health support is inaccessible for millions", delay: 0.3 },
                ].map((item, i) => (
                  <FadeInUp key={i} delay={item.delay}>
                    <div className="flex items-center gap-4 p-4 rounded-xl bg-background border shadow-sm">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                        <item.icon className="h-5 w-5" />
                      </div>
                      <span className="font-medium text-lg">{item.text}</span>
                    </div>
                  </FadeInUp>
                ))}
              </div>
            </div>
            
            <FadeInUp delay={0.2} className="relative">
              <div className="relative aspect-square rounded-3xl overflow-hidden border bg-gradient-to-br from-background to-muted shadow-2xl">
                <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(68,68,68,.2)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] animate-[shimmer_3s_infinite]" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="grid grid-cols-2 gap-4 opacity-50">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="w-32 h-32 rounded-2xl bg-foreground/5 animate-pulse" style={{ animationDelay: `${i * 0.2}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            </FadeInUp>
          </div>
        </section>

        {/* The Solution */}
        <section className="py-24 px-6">
          <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
            <FadeInUp className="order-2 lg:order-1 relative">
              <div className="relative aspect-[4/3] rounded-3xl overflow-hidden border bg-gradient-to-br from-primary/5 to-violet-500/5 shadow-2xl flex items-center justify-center">
                <div className="text-center p-8 space-y-4">
                  <div className="h-24 w-24 mx-auto rounded-3xl bg-primary/10 flex items-center justify-center text-primary">
                    <MessageCircle className="h-12 w-12" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">MEDORA</h3>
                    <p className="text-muted-foreground">Always here for you.</p>
                  </div>
                </div>
              </div>
            </FadeInUp>
            
            <div className="order-1 lg:order-2 space-y-8">
              <FadeInUp>
                <div className="inline-flex items-center gap-2 text-primary font-semibold uppercase tracking-wider text-sm">
                  <Check className="h-4 w-4" />
                  Our Solution
                </div>
                <h2 className="text-3xl md:text-5xl font-bold tracking-tight mt-4">
                  AI that actually cares.
                </h2>
              </FadeInUp>

              <div className="space-y-6">
                {[
                  "Instant answers, 24/7",
                  "Clinically-informed guidance",
                  "Judgment-free mental health support",
                ].map((text, i) => (
                  <FadeInUp key={i} delay={0.1 * (i + 1)}>
                    <div className="flex items-center gap-4">
                      <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground shrink-0">
                        <Check className="h-4 w-4" />
                      </div>
                      <span className="text-xl font-medium">{text}</span>
                    </div>
                  </FadeInUp>
                ))}
              </div>
              
              <FadeInUp delay={0.4}>
                <Button size="lg" className="mt-4 rounded-full" asChild>
                  <Link to="/ask">Try it now</Link>
                </Button>
              </FadeInUp>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-24 px-6 bg-muted/30">
          <div className="max-w-7xl mx-auto">
            <FadeInUp className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Three steps to better health</h2>
              <p className="text-xl text-muted-foreground">Simple, secure, and smart.</p>
            </FadeInUp>
            
            <div className="grid md:grid-cols-3 gap-8 relative">
              <div className="hidden md:block absolute top-12 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-transparent via-border to-transparent" />
              
              {[
                { title: "Tell us how you feel", desc: "Start a conversation anytime.", icon: MessageCircle, color: "text-blue-500" },
                { title: "Get personalized guidance", desc: "AI tailored to your needs.", icon: Sparkles, color: "text-violet-500" },
                { title: "Take action with confidence", desc: "Clear next steps.", icon: Heart, color: "text-primary" },
              ].map((step, i) => (
                <FadeInUp key={i} delay={0.1 * i} className="relative z-10">
                  <div className="bg-background rounded-2xl p-8 border shadow-sm hover:shadow-lg transition-all h-full text-center group">
                    <div className={cn("h-16 w-16 mx-auto rounded-2xl bg-muted flex items-center justify-center mb-6 transition-transform group-hover:scale-110", step.color)}>
                      <step.icon className="h-8 w-8" />
                    </div>
                    <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                    <p className="text-muted-foreground">{step.desc}</p>
                  </div>
                </FadeInUp>
              ))}
            </div>
          </div>
        </section>

        {/* Features / Values Bento Grid */}
        <section className="py-24 px-6">
          <div className="max-w-7xl mx-auto">
            <FadeInUp className="text-center mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">What we stand for</h2>
              <p className="text-xl text-muted-foreground">Core values that drive our mission.</p>
            </FadeInUp>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { icon: Heart, title: "Empathy First", desc: "We design for humans, not numbers." },
                { icon: Shield, title: "Privacy Always", desc: "Your data stays yours, always." },
                { icon: FlaskConical, title: "Science-Backed", desc: "Evidence guides every recommendation." },
                { icon: Globe, title: "Accessible to All", desc: "Quality care for everyone." },
              ].map((item, i) => (
                <FadeInUp key={i} delay={0.1 * i}>
                  <div className="p-8 rounded-2xl border bg-card hover:bg-muted/50 transition-colors h-full">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6">
                      <item.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">{item.desc}</p>
                  </div>
                </FadeInUp>
              ))}
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="py-24 px-6 bg-muted/30">
          <div className="max-w-7xl mx-auto">
             <FadeInUp className="text-center mb-16">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">Meet the team</h2>
              <p className="text-xl text-muted-foreground">The minds behind Medora.</p>
            </FadeInUp>
            <div className="grid md:grid-cols-4 gap-6">
              {[
                { name: "Nagur Shareef shaik", role: "Founder", image: "/Users/nagasaikakani/Documents/Projects/HACKGT/bhai.jpeg" },
                { name: "Sri Kakani", role: "Founder", image: "/Users/nagasaikakani/Documents/Projects/HACKGT/kakani.jpeg" },
                { name: "Aasrith Mandava", role: "Founder", image: "/Users/nagasaikakani/Documents/Projects/HACKGT/mandava.jpeg" },
                { name: "Asish Gogineni", role: "Founder", image: "/Users/nagasaikakani/Documents/Projects/HACKGT/asish.jpeg" },
              ].map((member, i) => (
                <FadeInUp key={i} delay={0.1 * i}>
                  <Card className="text-center hover:shadow-lg transition-all duration-300 border-none shadow-md bg-background">
                    <CardHeader>
                      <img
                        src={member.image}
                        alt={member.name}
                        className="w-24 h-24 mx-auto rounded-full object-cover border-2 border-primary/20 mb-4"
                        onError={(e) => {
                          const target = e.currentTarget;
                          target.onerror = null;
                          target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(member.name)}&size=96&background=6366f1&color=fff`;
                        }}
                      />
                      <CardTitle>{member.name}</CardTitle>
                      <p className="text-sm text-primary font-medium">{member.role}</p>
                    </CardHeader>
                  </Card>
                </FadeInUp>
              ))}
            </div>
          </div>
        </section>

        {/* Trust & Security */}
        <section className="py-24 px-6 bg-muted/30">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <FadeInUp>
              <div className="h-20 w-20 mx-auto rounded-3xl bg-primary/10 flex items-center justify-center text-primary mb-8">
                <Lock className="h-10 w-10" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Your health data is sacred.</h2>
              <p className="text-xl text-muted-foreground">
                We're committed to the highest standards of privacy and security. Your conversations are encrypted, never sold, and you control your data.
              </p>
            </FadeInUp>
            
            <FadeInUp delay={0.2} className="flex flex-wrap justify-center gap-4 pt-8">
              {["HIPAA Compliant", "SOC 2 Type II", "End-to-End Encrypted", "GDPR Ready"].map((badge) => (
                <span key={badge} className="px-4 py-2 rounded-full border bg-background font-medium text-sm shadow-sm">
                  {badge}
                </span>
              ))}
            </FadeInUp>
          </div>
        </section>

        {/* CTA */}
        <section className="py-32 px-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary via-violet-600 to-blue-600" />
          <div 
            className="absolute inset-0 opacity-20 mix-blend-overlay" 
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}
          />
          
          <div className="relative z-10 max-w-4xl mx-auto text-center text-white space-y-8">
            <FadeInUp>
              <h2 className="text-4xl md:text-6xl font-bold tracking-tight">Ready to take control?</h2>
              <p className="text-xl md:text-2xl text-white/80 max-w-2xl mx-auto">
                Join thousands who've found a better way to care for themselves.
              </p>
            </FadeInUp>
            
            <FadeInUp delay={0.2} className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
              <Button size="lg" className="h-14 px-8 text-lg rounded-full bg-white text-primary hover:bg-white/90 shadow-xl" asChild>
                <Link to="/ask">Get Started For Free</Link>
              </Button>
              <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-white text-white hover:bg-white/10 bg-transparent" asChild>
                <Link to="/login">Sign In</Link>
              </Button>
            </FadeInUp>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-16 px-6 border-t bg-background">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-12 mb-16">
              <div className="md:col-span-2 space-y-6">
                <div className="flex items-center gap-2 font-bold text-2xl">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-violet-500 flex items-center justify-center text-white shadow-lg shadow-primary/20">
                    <Heart className="h-5 w-5 fill-current" />
                  </div>
                  MEDORA
                </div>
                <p className="text-muted-foreground text-lg max-w-sm leading-relaxed">
                  Healthcare reimagined for the modern world. AI-powered, human-centric, and accessible to everyone.
                </p>
                <div className="flex gap-4">
                  {/* Social placeholders */}
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-10 w-10 rounded-full bg-muted flex items-center justify-center hover:bg-primary/10 hover:text-primary transition-colors cursor-pointer">
                      <Globe className="h-5 w-5" />
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-bold mb-6">Product</h4>
                <ul className="space-y-4 text-muted-foreground">
                  <li><Link to="/ask" className="hover:text-primary transition-colors">Virtual Doctor</Link></li>
                  <li><Link to="/dietary" className="hover:text-primary transition-colors">Dietary Assistant</Link></li>
                  <li><Link to="/wellbeing" className="hover:text-primary transition-colors">Mental Wellbeing</Link></li>
                  <li><Link to="/diagnostic" className="hover:text-primary transition-colors">Diagnostic Tool</Link></li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-bold mb-6">Company</h4>
                <ul className="space-y-4 text-muted-foreground">
                  <li><Link to="/about" className="hover:text-primary transition-colors">About Us</Link></li>
                  <li><Link to="#" className="hover:text-primary transition-colors">Careers</Link></li>
                  <li><Link to="#" className="hover:text-primary transition-colors">Blog</Link></li>
                  <li><Link to="#" className="hover:text-primary transition-colors">Contact</Link></li>
                </ul>
              </div>
            </div>
            
            <div className="pt-8 border-t flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
              <p>&copy; {new Date().getFullYear()} Medora AI. All rights reserved.</p>
              <div className="flex gap-8">
                <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-foreground transition-colors">Cookie Policy</a>
              </div>
            </div>
            
            <div className="mt-8 text-center">
               <p className="text-xs text-muted-foreground/60 max-w-2xl mx-auto">
                MEDORA provides information for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. If you think you may have a medical emergency, call your doctor or 911 immediately.
              </p>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
}
