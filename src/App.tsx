import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Overview } from './components/Overview';
import { Architecture } from './components/Architecture';
import { FileViewer } from './components/FileViewer';
import { ProjectStructure } from './components/ProjectStructure';
import { projectFiles } from './data/files';

export type Section =
  | 'overview'
  | 'architecture'
  | 'structure'
  | 'files';

function App() {
  const [section, setSection] = useState<Section>('overview');
  const [selectedFile, setSelectedFile] = useState<string>(projectFiles[0].path);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <Sidebar
        section={section}
        onSectionChange={setSection}
        selectedFile={selectedFile}
        onFileSelect={(p) => {
          setSelectedFile(p);
          setSection('files');
        }}
      />
      <main className="flex-1 ml-72 min-h-screen">
        {section === 'overview' && <Overview onNavigate={setSection} />}
        {section === 'architecture' && <Architecture />}
        {section === 'structure' && <ProjectStructure onFileSelect={(p) => { setSelectedFile(p); setSection('files'); }} />}
        {section === 'files' && <FileViewer filePath={selectedFile} />}
      </main>
    </div>
  );
}

export default App;
