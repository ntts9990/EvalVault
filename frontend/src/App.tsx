import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Dashboard } from './pages/Dashboard';
import { RunDetails } from './pages/RunDetails';
import { EvaluationStudio } from './pages/EvaluationStudio';
import { DomainMemory } from './pages/DomainMemory';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { AnalysisLab } from './pages/AnalysisLab';
import { AiSdkChat } from './pages/AiSdkChat';
import { AnalysisCompareView } from './pages/AnalysisCompareView';
import { AnalysisResultView } from './pages/AnalysisResultView';
import { CompareRuns } from './pages/CompareRuns';
import { Settings } from './pages/Settings';
import { CustomerReport } from './pages/CustomerReport';
import { Visualization } from './pages/Visualization';
import { VisualizationHome } from './pages/VisualizationHome';
import { JudgeCalibration } from './pages/JudgeCalibration';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/runs/:id" element={<RunDetails />} />
        <Route path="/compare" element={<CompareRuns />} />
        <Route path="/studio" element={<EvaluationStudio />} />
        <Route path="/domain" element={<DomainMemory />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/analysis" element={<AnalysisLab />} />
        <Route path="/analysis/compare" element={<AnalysisCompareView />} />
        <Route path="/chat" element={<AiSdkChat />} />
        <Route path="/analysis/results/:id" element={<AnalysisResultView />} />
        <Route path="/reports" element={<CustomerReport />} />
        <Route path="/visualization" element={<VisualizationHome />} />
        <Route path="/visualization/:id" element={<Visualization />} />
        <Route path="/calibration" element={<JudgeCalibration />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
