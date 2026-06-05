const layers = [
  {
    num: '1',
    title: 'User Input Layer',
    desc: 'Voice, text, and dashboard camera input from the driver.',
    items: ['Microphone capture', 'Text input', 'Dashboard camera feed'],
    color: 'border-blue-500/40 bg-blue-500/10',
    accent: 'text-blue-300',
  },
  {
    num: '2',
    title: 'Perception Layer',
    desc: 'Convert raw input into structured, machine-readable signals.',
    items: ['Whisper (speech-to-text)', 'OpenCV (HSV warning light detection)', 'Multipart upload handling'],
    color: 'border-purple-500/40 bg-purple-500/10',
    accent: 'text-purple-300',
  },
  {
    num: '3',
    title: 'Agent Layer (LangGraph)',
    desc: '6-node deterministic reasoning graph orchestrating the response.',
    items: ['Input Processor', 'Intent Classifier', 'Tool Caller', 'Safety Validator', 'Response Generator', 'Memory Update'],
    color: 'border-amber-500/40 bg-amber-500/10',
    accent: 'text-amber-300',
  },
  {
    num: '4',
    title: 'MCP Server Layer',
    desc: 'Modular tool servers exposing vehicle capabilities via MCP protocol.',
    items: ['vehicle_state_mcp (read-only)', 'climate_mcp', 'navigation_mcp', 'media_mcp'],
    color: 'border-emerald-500/40 bg-emerald-500/10',
    accent: 'text-emerald-300',
  },
  {
    num: '5',
    title: 'Persistence Layer',
    desc: 'SQLite-backed conversation memory with intent and tool logs.',
    items: ['conversations table', 'sessions table', 'safety audit log'],
    color: 'border-rose-500/40 bg-rose-500/10',
    accent: 'text-rose-300',
  },
  {
    num: '6',
    title: 'Presentation Layer',
    desc: 'Streamlit UI with live dashboard, chat panel, and system logs.',
    items: ['Vehicle dashboard widget', 'Conversation feed', 'Color-coded log stream', 'pyttsx3 voice output'],
    color: 'border-indigo-500/40 bg-indigo-500/10',
    accent: 'text-indigo-300',
  },
];

const agentNodes = [
  { name: 'Input Processor', desc: 'Enriches user message with vehicle state context (speed, fuel, location, media).' },
  { name: 'Intent Classifier', desc: 'Maps message to one of: navigation, climate, media, vehicle_info, general.' },
  { name: 'Tool Caller', desc: 'Selects and invokes the correct MCP tool(s) with extracted parameters.' },
  { name: 'Safety Validator', desc: 'Blocks unsafe actions (door unlock at speed, complex search while driving fast).' },
  { name: 'Response Generator', desc: 'Produces natural language reply via Groq Llama3, with template fallback.' },
  { name: 'Memory Update', desc: 'Persists message, intent, tools, response and safety status to SQLite.' },
];

export function Architecture() {
  return (
    <div className="min-h-screen py-12 px-8 max-w-6xl mx-auto">
      <div className="mb-12">
        <div className="text-xs uppercase tracking-wider text-blue-400 font-semibold mb-2">System Design</div>
        <h1 className="text-4xl font-bold mb-3">Architecture</h1>
        <p className="text-slate-400 max-w-2xl">
          Six-layer architecture from raw user input through perception, reasoning,
          tool execution and persistence — all surfaced via a live Streamlit dashboard.
        </p>
      </div>

      {/* Flow diagram */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold mb-5 text-slate-200">End-to-End Request Flow</h2>
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6 overflow-x-auto">
          <pre className="text-xs md:text-sm leading-relaxed text-slate-300 font-mono whitespace-pre">
{`User speaks / types / shows camera
        │
        ▼
Streamlit UI captures input
        │
        ▼
FastAPI Backend receives and routes
        │
        ▼
Whisper (speech)  /  OpenCV (vision)  ─── processes raw input
        │
        ▼
LangGraph Agent orchestrates reasoning
   ├─ Intent Classification
   ├─ Tool Calling via MCP Protocol
   ├─ Safety Validation
   ├─ Response Generation
   └─ Memory Storage
        │
        ▼
MCP Servers execute simulated vehicle commands
        │
        ▼
FastAPI streams response back
        │
        ▼
Streamlit shows response + updates dashboard
pyttsx3 speaks the response aloud`}
          </pre>
        </div>
      </section>

      {/* Layers */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold mb-5 text-slate-200">System Layers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {layers.map((l) => (
            <div key={l.num} className={`p-5 rounded-xl border ${l.color}`}>
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg bg-slate-950 border border-slate-700 flex items-center justify-center font-bold ${l.accent} flex-shrink-0`}>
                  {l.num}
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold ${l.accent} mb-1`}>{l.title}</h3>
                  <p className="text-xs text-slate-400 mb-3">{l.desc}</p>
                  <ul className="space-y-1">
                    {l.items.map((it) => (
                      <li key={it} className="text-xs text-slate-300 flex items-center gap-2">
                        <span className={`w-1 h-1 rounded-full ${l.accent} bg-current`} />
                        {it}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Agent Graph */}
      <section className="mb-16">
        <h2 className="text-xl font-semibold mb-1 text-slate-200">LangGraph Agent: 6 Nodes</h2>
        <p className="text-sm text-slate-400 mb-5">Each chat invocation walks the full graph in deterministic order.</p>

        <div className="space-y-3">
          {agentNodes.map((n, i) => (
            <div key={n.name} className="flex items-stretch gap-4">
              <div className="flex flex-col items-center">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center font-bold text-sm text-white shadow-lg shadow-amber-500/30">
                  {i + 1}
                </div>
                {i < agentNodes.length - 1 && (
                  <div className="w-px flex-1 bg-gradient-to-b from-amber-500/50 to-transparent mt-1" />
                )}
              </div>
              <div className="flex-1 pb-3 pt-1">
                <div className="rounded-lg bg-slate-900/60 border border-slate-800 p-4">
                  <div className="font-semibold text-amber-300 mb-1">{n.name}</div>
                  <div className="text-xs text-slate-400">{n.desc}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Safety section */}
      <section className="mb-12">
        <div className="rounded-2xl bg-gradient-to-br from-rose-500/10 to-red-500/5 border border-rose-500/30 p-6">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">🛡️</span>
            <h2 className="text-xl font-semibold text-rose-300">Safety Validator Rules</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-rose-400 font-semibold mb-1">SPEED-LOCK</div>
              <div className="text-sm text-slate-300">Blocks engine-off / unlock-doors commands when speed &gt; 0</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-rose-400 font-semibold mb-1">RANGE-LIMIT</div>
              <div className="text-sm text-slate-300">Rejects temperatures outside 16–30°C comfort range</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-rose-400 font-semibold mb-1">FOCUS-GUARD</div>
              <div className="text-sm text-slate-300">No complex navigation search when speed &gt; 80 km/h</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
