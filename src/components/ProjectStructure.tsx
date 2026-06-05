import { projectFiles, categoryColors, categoryLabels } from '../data/files';

interface ProjectStructureProps {
  onFileSelect: (path: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  isFile: boolean;
  children: Record<string, TreeNode>;
  fileEntry?: typeof projectFiles[number];
}

function buildTree(): TreeNode {
  const root: TreeNode = { name: 'bmw-ai-assistant', path: '', isFile: false, children: {} };
  for (const f of projectFiles) {
    const parts = f.path.split('/');
    let node = root;
    parts.forEach((part, idx) => {
      const isLast = idx === parts.length - 1;
      if (!node.children[part]) {
        node.children[part] = {
          name: part,
          path: parts.slice(0, idx + 1).join('/'),
          isFile: isLast,
          children: {},
          fileEntry: isLast ? f : undefined,
        };
      }
      node = node.children[part];
    });
  }
  return root;
}

function TreeView({ node, depth, onFileSelect }: { node: TreeNode; depth: number; onFileSelect: (p: string) => void }) {
  const entries = Object.values(node.children).sort((a, b) => {
    if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
    return a.name.localeCompare(b.name);
  });

  return (
    <div className={depth === 0 ? '' : 'border-l border-slate-800 ml-2'}>
      {entries.map((child) => (
        <div key={child.path}>
          {child.isFile ? (
            <button
              onClick={() => onFileSelect(child.path)}
              className="flex items-center gap-2 pl-4 pr-3 py-1.5 text-sm font-mono hover:bg-slate-800/50 rounded transition-colors w-full text-left group"
            >
              <span className="text-slate-500 text-xs">📄</span>
              <span className="text-slate-300 group-hover:text-blue-300">{child.name}</span>
              {child.fileEntry && (
                <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-gradient-to-r ${categoryColors[child.fileEntry.category]} bg-opacity-20 text-white/90`}>
                  {categoryLabels[child.fileEntry.category]}
                </span>
              )}
            </button>
          ) : (
            <div>
              <div className="flex items-center gap-2 pl-4 pr-3 py-1.5 text-sm font-mono">
                <span className="text-amber-400">📁</span>
                <span className="text-amber-300 font-semibold">{child.name}/</span>
              </div>
              <div className="ml-3">
                <TreeView node={child} depth={depth + 1} onFileSelect={onFileSelect} />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function ProjectStructure({ onFileSelect }: ProjectStructureProps) {
  const tree = buildTree();

  const byCategory = projectFiles.reduce<Record<string, typeof projectFiles>>((acc, f) => {
    (acc[f.category] = acc[f.category] || []).push(f);
    return acc;
  }, {});

  return (
    <div className="min-h-screen py-12 px-8 max-w-6xl mx-auto">
      <div className="mb-10">
        <div className="text-xs uppercase tracking-wider text-blue-400 font-semibold mb-2">File System</div>
        <h1 className="text-4xl font-bold mb-3">Project Structure</h1>
        <p className="text-slate-400">All files organized by layer and responsibility. Click any file to view its full source.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Tree */}
        <div className="lg:col-span-3">
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">File Tree</h2>
              <span className="text-xs text-slate-500">{projectFiles.length} files</span>
            </div>
            <div className="font-mono">
              <div className="flex items-center gap-2 py-1.5 text-sm">
                <span className="text-amber-400">📁</span>
                <span className="text-amber-300 font-semibold">{tree.name}/</span>
              </div>
              <TreeView node={tree} depth={0} onFileSelect={onFileSelect} />
            </div>
          </div>
        </div>

        {/* Category summary */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">By Category</h2>
          {Object.entries(byCategory).map(([cat, files]) => (
            <div key={cat} className="rounded-xl bg-slate-900/60 border border-slate-800 p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full bg-gradient-to-br ${categoryColors[cat]}`} />
                <span className="font-semibold text-sm text-slate-200">{categoryLabels[cat]}</span>
                <span className="text-xs text-slate-500 ml-auto">{files.length} files</span>
              </div>
              <div className="space-y-1">
                {files.map((f) => (
                  <button
                    key={f.path}
                    onClick={() => onFileSelect(f.path)}
                    className="block w-full text-left text-xs font-mono text-slate-400 hover:text-blue-300 truncate"
                    title={f.path}
                  >
                    {f.path}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
