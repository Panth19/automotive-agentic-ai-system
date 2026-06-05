import { useState } from 'react';
import type { Section } from '../App';
import { projectFiles, categoryColors, categoryLabels } from '../data/files';

interface SidebarProps {
  section: Section;
  onSectionChange: (s: Section) => void;
  selectedFile: string;
  onFileSelect: (path: string) => void;
}

const navItems: { id: Section; label: string; icon: string }[] = [
  { id: 'overview', label: 'Overview', icon: '🏠' },
  { id: 'architecture', label: 'Architecture', icon: '🏗️' },
  { id: 'structure', label: 'Project Structure', icon: '📁' },
  { id: 'files', label: 'Browse Files', icon: '📄' },
];

export function Sidebar({ section, onSectionChange, selectedFile, onFileSelect }: SidebarProps) {
  const [openCats, setOpenCats] = useState<Record<string, boolean>>({
    backend: true,
    mcp: true,
    agent: true,
    database: true,
    frontend: true,
  });

  const grouped = projectFiles.reduce<Record<string, typeof projectFiles>>((acc, f) => {
    acc[f.category] = acc[f.category] || [];
    acc[f.category].push(f);
    return acc;
  }, {});

  return (
    <aside className="fixed top-0 left-0 w-72 h-screen bg-slate-900/95 backdrop-blur border-r border-slate-800 overflow-y-auto z-50">
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xl shadow-lg shadow-blue-500/30">
            🚗
          </div>
          <div>
            <h1 className="font-bold text-base leading-tight">BMW AI</h1>
            <p className="text-xs text-slate-400">Automotive Assistant</p>
          </div>
        </div>
      </div>

      <nav className="p-3 space-y-1">
        {navItems.map((it) => (
          <button
            key={it.id}
            onClick={() => onSectionChange(it.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
              section === it.id
                ? 'bg-blue-500/15 text-blue-300 ring-1 ring-blue-500/30'
                : 'text-slate-300 hover:bg-slate-800/60'
            }`}
          >
            <span>{it.icon}</span>
            {it.label}
          </button>
        ))}
      </nav>

      <div className="px-3 pb-6">
        <p className="text-[11px] uppercase tracking-wider text-slate-500 px-3 py-2 font-semibold">
          Files
        </p>
        <div className="space-y-1">
          {Object.entries(grouped).map(([cat, files]) => (
            <div key={cat}>
              <button
                onClick={() => setOpenCats((p) => ({ ...p, [cat]: !p[cat] }))}
                className="w-full flex items-center justify-between px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded"
              >
                <span className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full bg-gradient-to-br ${categoryColors[cat]}`} />
                  {categoryLabels[cat]}
                  <span className="text-slate-600">({files.length})</span>
                </span>
                <span className="text-slate-600">{openCats[cat] ? '−' : '+'}</span>
              </button>
              {openCats[cat] && (
                <div className="ml-3 space-y-0.5 mt-0.5">
                  {files.map((f) => (
                    <button
                      key={f.path}
                      onClick={() => onFileSelect(f.path)}
                      className={`w-full text-left px-3 py-1.5 text-xs rounded font-mono transition-colors truncate ${
                        section === 'files' && selectedFile === f.path
                          ? 'bg-slate-800 text-blue-300'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                      }`}
                      title={f.path}
                    >
                      {f.path.split('/').pop()}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="px-5 py-4 border-t border-slate-800 text-[11px] text-slate-500">
        v1.0.0 · FastAPI + LangGraph
      </div>
    </aside>
  );
}
