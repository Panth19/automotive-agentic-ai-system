import type { Section } from '../App';

interface OverviewProps {
  onNavigate: (s: Section) => void;
}

const features = [
  {
    icon: '🎤',
    title: 'Voice Input',
    desc: 'OpenAI Whisper for accurate speech-to-text transcription with graceful fallback.',
    color: 'from-blue-500/20 to-cyan-500/10 border-blue-500/30',
  },
  {
    icon: '👁️',
    title: 'Vision Analysis',
    desc: 'OpenCV-powered dashboard warning light detection using HSV color thresholding.',
    color: 'from-purple-500/20 to-pink-500/10 border-purple-500/30',
  },
  {
    icon: '🧠',
    title: '6-Node LangGraph Agent',
    desc: 'Input → Intent → Tools → Safety → Response → Memory orchestration.',
    color: 'from-amber-500/20 to-orange-500/10 border-amber-500/30',
  },
  {
    icon: '🔌',
    title: 'MCP Servers',
    desc: 'Modular Model Context Protocol servers for vehicle, climate, navigation, media.',
    color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/30',
  },
  {
    icon: '🛡️',
    title: 'Safety Validation',
    desc: 'Blocks dangerous actions while driving — e.g. unlocking doors at speed.',
    color: 'from-rose-500/20 to-red-500/10 border-rose-500/30',
  },
  {
    icon: '💾',
    title: 'SQLite Memory',
    desc: 'Persistent conversation history with session tracking and intent logs.',
    color: 'from-indigo-500/20 to-violet-500/10 border-indigo-500/30',
  },
  {
    icon: '🖥️',
    title: 'Streamlit UI',
    desc: 'Live dashboard, conversation panel, and color-coded system logs.',
    color: 'from-fuchsia-500/20 to-pink-500/10 border-fuchsia-500/30',
  },
  {
    icon: '🔊',
    title: 'Text-to-Speech',
    desc: 'pyttsx3 reads AI responses aloud for hands-free interaction.',
    color: 'from-yellow-500/20 to-amber-500/10 border-yellow-500/30',
  },
];

const stats = [
  { label: 'Python Files', value: '12' },
  { label: 'MCP Servers', value: '4' },
  { label: 'Agent Nodes', value: '6' },
  { label: 'MCP Tools', value: '25+' },
];

export function Overview({ onNavigate }: OverviewProps) {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative overflow-hidden border-b border-slate-800">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-600/20 via-slate-900 to-slate-950" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:40px_40px] opacity-30" />

        <div className="relative max-w-6xl mx-auto px-8 py-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs text-blue-300 font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            FastAPI · LangGraph · MCP Protocol
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-5 bg-gradient-to-br from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            BMW Automotive
            <br />
            AI Assistant
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mb-8 leading-relaxed">
            A production-grade in-vehicle AI system combining voice recognition,
            computer vision, multi-agent reasoning and tool-calling via the Model
            Context Protocol — with built-in safety validation for real driving conditions.
          </p>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('architecture')}
              className="px-5 py-2.5 rounded-lg bg-blue-500 hover:bg-blue-400 text-white text-sm font-semibold transition-colors shadow-lg shadow-blue-500/30"
            >
              View Architecture →
            </button>
            <button
              onClick={() => onNavigate('files')}
              className="px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm font-semibold transition-colors"
            >
              Browse Source Code
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-14 max-w-3xl">
            {stats.map((s) => (
              <div key={s.label} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
                <div className="text-3xl font-bold text-white">{s.value}</div>
                <div className="text-xs text-slate-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-8 py-16">
        <div className="mb-10">
          <h2 className="text-3xl font-bold mb-2">Capabilities</h2>
          <p className="text-slate-400">Eight integrated systems working as one.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f) => (
            <div
              key={f.title}
              className={`p-5 rounded-xl bg-gradient-to-br ${f.color} border backdrop-blur hover:scale-[1.02] transition-transform`}
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Start */}
      <section className="max-w-6xl mx-auto px-8 py-10">
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-8">
          <h2 className="text-2xl font-bold mb-4">Quick Start</h2>
          <p className="text-slate-400 text-sm mb-6">
            Get the assistant running locally in under a minute.
          </p>

          <div className="bg-slate-950 rounded-lg border border-slate-800 p-5 font-mono text-sm space-y-2">
            <div><span className="text-slate-500"># Install dependencies</span></div>
            <div><span className="text-emerald-400">$</span> <span className="text-slate-200">pip install -r requirements.txt</span></div>
            <div className="pt-2"><span className="text-slate-500"># Configure environment</span></div>
            <div><span className="text-emerald-400">$</span> <span className="text-slate-200">cp .env.example .env</span></div>
            <div className="pt-2"><span className="text-slate-500"># Launch backend + frontend</span></div>
            <div><span className="text-emerald-400">$</span> <span className="text-slate-200">python run_all.py</span></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5">
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-slate-500 mb-1">FastAPI Backend</div>
              <div className="font-mono text-sm text-blue-300">http://localhost:8000</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-slate-500 mb-1">Streamlit UI</div>
              <div className="font-mono text-sm text-emerald-300">http://localhost:8501</div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="max-w-6xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold mb-2">Technology Stack</h2>
        <p className="text-slate-400 mb-8">Built on best-in-class open source.</p>
        <div className="flex flex-wrap gap-2">
          {['FastAPI', 'LangGraph', 'LangChain', 'Groq Llama3', 'FastMCP', 'OpenAI Whisper', 'OpenCV', 'Streamlit', 'SQLite', 'pyttsx3', 'NumPy', 'Pydantic', 'Uvicorn'].map((t) => (
            <span key={t} className="px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700 text-xs text-slate-300 font-medium">
              {t}
            </span>
          ))}
        </div>
      </section>

      <footer className="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
        BMW Automotive AI Assistant · Built with FastAPI + LangGraph + MCP
      </footer>
    </div>
  );
}
