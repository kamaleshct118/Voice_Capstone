import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Mic, Pill, Activity, ArrowRight, Database,
  MessageSquare, Volume2, HeartPulse, Newspaper, ClipboardList,
} from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";

const features = [
  {
    icon: Mic,
    title: "Voice & Text Input",
    description:
      "Speak or type your healthcare queries. Faster-Whisper STT converts voice to text instantly with high accuracy.",
  },
  {
    icon: Pill,
    title: "Medicine Classifier",
    description:
      "Ask about any medicine by name or upload an image. Gemini Vision extracts composition, category, and safety notes.",
  },
  {
    icon: Newspaper,
    title: "Medical News",
    description:
      "Get the latest developments in healthcare, pharmaceutical industry, and medical research — summarized by AI.",
  },
  {
    icon: ClipboardList,
    title: "Medical Report Generator",
    description:
      "Generate a structured health summary from your stored session data, health logs, and previous interactions.",
  },
  {
    icon: HeartPulse,
    title: "Health Monitor Dashboard",
    description:
      "Track BP, blood sugar, weight, and mood daily. Get AI trend analysis, diet suggestions, and a personalized daily checklist.",
  },
  {
    icon: Volume2,
    title: "Expressive Voice Responses",
    description:
      "Receive natural TTS audio responses with SSML-tuned prosody — different speech styles per tool output.",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5 },
  }),
};

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-sm">
        <div className="container max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-foreground">
            <Activity className="w-5 h-5 text-primary" />
            Voice Healthcare AI
          </Link>
          <div className="flex items-center gap-3">
            <Link
              to="/health-monitor"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <HeartPulse className="w-4 h-4" />
              Health Monitor
            </Link>
            <Link
              to="/data"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <Database className="w-4 h-4" />
              Data Explorer
            </Link>
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:brightness-110 transition"
            >
              Open Assistant
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img src={heroBg} alt="" className="w-full h-full object-cover opacity-30" />
          <div className="absolute inset-0 bg-gradient-to-b from-background/60 via-background/80 to-background" />
        </div>
        <div className="relative container max-w-4xl mx-auto px-4 py-24 md:py-36 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary mb-6">
              <Activity className="w-3.5 h-3.5" />
              AI-Powered Healthcare Assistant
            </span>
            <h1 className="text-4xl md:text-6xl font-bold text-foreground tracking-tight leading-tight">
              Voice-Driven
              <br />
              <span className="text-primary">Healthcare AI Assistant</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Ask about medicines, get medical news, generate health reports, and monitor
              your daily vitals — all through voice or text with natural TTS responses.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/assistant"
                className="inline-flex items-center gap-2 px-6 py-3 text-base font-semibold rounded-xl bg-primary text-primary-foreground hover:brightness-110 transition shadow-lg shadow-primary/25"
              >
                <MessageSquare className="w-5 h-5" />
                Start Consultation
              </Link>
              <Link
                to="/health-monitor"
                className="inline-flex items-center gap-2 px-6 py-3 text-base font-medium rounded-xl bg-card text-foreground border border-border hover:bg-muted transition"
              >
                <HeartPulse className="w-5 h-5" />
                Health Dashboard
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* System Flow */}
      <section className="py-14 border-y border-border bg-muted/20">
        <div className="container max-w-5xl mx-auto px-4 text-center">
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-widest mb-6">
            System Pipeline
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
            {[
              "Voice / Text Input",
              "Whisper STT",
              "LLM Intent Analysis",
              "MCP Tool Orchestration",
              "Redis Cache",
              "LLM Response",
              "SSML Formatting",
              "TTS Audio Output",
            ].map((step, i, arr) => (
              <span key={step} className="flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-full bg-primary/10 text-primary font-medium text-xs">
                  {step}
                </span>
                {i < arr.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                )}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-muted/30">
        <div className="container max-w-6xl mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-foreground">Key Features</h2>
            <p className="mt-3 text-muted-foreground">
              Everything you need for intelligent, voice-enabled healthcare assistance
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                className="clinical-card-elevated p-6 hover:shadow-lg transition-shadow"
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                  <f.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {f.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container max-w-6xl mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2026 Voice Healthcare AI · Capstone Project ·{" "}
          <span className="text-primary">Whisper + Groq/Gemini + Kokoro TTS + Redis</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
