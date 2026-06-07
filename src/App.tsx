export default function App() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-zinc-100 p-8">
      <div className="max-w-4xl space-y-6 text-center">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-indigo-200">
          <svg
            className="h-8 w-8 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="2" y="4" width="20" height="16" rx="2" />
            <path d="M10 4v4" />
            <path d="M2 8h20" />
            <path d="M6 4v4" />
          </svg>
        </div>
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">BMW Automotive AI Assistant</h1>
          <p className="text-slate-500">Multimodal Agentic AI System for In-Vehicle Assistance</p>
        </div>
        
        <div className="text-left bg-white rounded-lg p-6 shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">System Architecture</h2>
          <pre className="text-sm bg-slate-100 p-4 rounded overflow-x-auto">
{`
User speaks/types/shows camera
        ↓
Streamlit UI captures input
        ↓
FastAPI Backend receives and routes
        ↓
Whisper (speech) / OpenCV (vision) processes input
        ↓
LangGraph Agent orchestrates reasoning
   → Intent Classification
   → Tool Calling via MCP Protocol  
   → Safety Validation
   → Response Generation
   → Memory Storage
        ↓
MCP Servers execute simulated vehicle commands
        ↓
FastAPI streams response back
        ↓
Streamlit shows response + updates dashboard
pyttsx3 speaks the response aloud
`}
          </pre>
        </div>
        
        <div className="text-left bg-white rounded-lg p-6 shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">How to Run</h2>
          <ol className="list-decimal list-inside space-y-2 text-slate-600">
            <li>Install Python dependencies: <code className="bg-slate-200 px-2 py-1 rounded">pip install -r requirements.txt</code></li>
            <li>Start FastAPI backend: <code className="bg-slate-200 px-2 py-1 rounded">python main.py</code> (port 8000)</li>
            <li>Start Streamlit UI: <code className="bg-slate-200 px-2 py-1 rounded">streamlit run frontend/streamlit_app.py</code> (port 8501)</li>
            <li>Or run both: <code className="bg-slate-200 px-2 py-1 rounded">python run_all.py</code></li>
          </ol>
        </div>
        
        <div className="text-left bg-white rounded-lg p-6 shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-slate-800">Key Features</h2>
          <ul className="list-disc list-inside space-y-1 text-slate-600">
            <li>Voice input via Whisper speech-to-text</li>
            <li>Vision analysis via OpenCV for dashboard warnings</li>
            <li>LangGraph agent with 6 reasoning nodes</li>
            <li>4 MCP servers for vehicle controls</li>
            <li>Safety validation for automotive commands</li>
            <li>SQLite-backed conversation memory</li>
            <li>Real-time streaming responses</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
