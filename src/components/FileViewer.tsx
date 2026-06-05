import { useState } from 'react';
import { projectFiles, categoryColors, categoryLabels } from '../data/files';

interface FileViewerProps {
  filePath: string;
}

export function FileViewer({ filePath }: FileViewerProps) {
  const file = projectFiles.find((f) => f.path === filePath) ?? projectFiles[0];
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  const lines = file.content.split('\n');
  const lineCount = lines.length;
  const charCount = file.content.length;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-slate-950/95 backdrop-blur border-b border-slate-800">
        <div className="px-8 py-5">
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-gradient-to-r ${categoryColors[file.category]} text-white`}>
              {categoryLabels[file.category]}
            </span>
            <h1 className="font-mono text-lg text-slate-100">{file.path}</h1>
            <div className="ml-auto flex items-center gap-4 text-xs text-slate-500">
              <span>{lineCount} lines</span>
              <span>{(charCount / 1024).toFixed(1)} KB</span>
              <span className="uppercase">{file.language}</span>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium transition-colors"
              >
                {copied ? '✓ Copied' : '📋 Copy'}
              </button>
            </div>
          </div>
          <p className="text-sm text-slate-400 mt-2">{file.description}</p>
        </div>
      </div>

      {/* Code */}
      <div className="px-8 py-6">
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-[#0a0f1c]">
          <div className="flex items-center gap-2 px-4 py-2 bg-slate-900/80 border-b border-slate-800">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/70" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
              <div className="w-3 h-3 rounded-full bg-green-500/70" />
            </div>
            <span className="ml-3 text-xs font-mono text-slate-400">{file.path}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    <td className="select-none text-right pr-4 pl-4 py-0.5 text-xs text-slate-600 font-mono w-14 align-top border-r border-slate-900">
                      {idx + 1}
                    </td>
                    <td className="pl-4 pr-4 py-0.5 text-sm font-mono text-slate-200 whitespace-pre">
                      {highlightLine(line, file.language) || '\u00A0'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// Very lightweight syntax coloring
function highlightLine(line: string, language: string): React.ReactNode {
  if (language === 'text') return line;

  // Comments
  if (language === 'python' && line.trim().startsWith('#')) {
    return <span className="text-slate-500 italic">{line}</span>;
  }
  if (language === 'markdown' && line.startsWith('#')) {
    return <span className="text-blue-300 font-semibold">{line}</span>;
  }

  // Triple-quoted docstrings
  if (language === 'python' && (line.trim().startsWith('"""') || line.trim().endsWith('"""'))) {
    return <span className="text-emerald-400/80 italic">{line}</span>;
  }

  const parts: React.ReactNode[] = [];
  const tokenRegex =
    /(\bdef\b|\bclass\b|\breturn\b|\bif\b|\belif\b|\belse\b|\bfor\b|\bwhile\b|\bimport\b|\bfrom\b|\bas\b|\btry\b|\bexcept\b|\bwith\b|\bpass\b|\braise\b|\bin\b|\bnot\b|\band\b|\bor\b|\bis\b|\bNone\b|\bTrue\b|\bFalse\b|\basync\b|\bawait\b|\byield\b|\bglobal\b|\blambda\b|\bself\b)|("(?:[^"\\]|\\.)*")|('(?:[^'\\]|\\.)*')|(\b\d+\b)|(@\w+(?:\.\w+)*)/g;

  let lastIdx = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = tokenRegex.exec(line)) !== null) {
    if (match.index > lastIdx) {
      parts.push(line.slice(lastIdx, match.index));
    }
    const [tok, kw, dstr, sstr, num, dec] = match;
    if (kw) parts.push(<span key={key++} className="text-pink-400">{tok}</span>);
    else if (dstr || sstr) parts.push(<span key={key++} className="text-emerald-300">{tok}</span>);
    else if (num) parts.push(<span key={key++} className="text-amber-300">{tok}</span>);
    else if (dec) parts.push(<span key={key++} className="text-cyan-300">{tok}</span>);
    else parts.push(tok);
    lastIdx = match.index + tok.length;
  }
  if (lastIdx < line.length) parts.push(line.slice(lastIdx));
  return <>{parts}</>;
}
