import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { DocLayout } from "./components/DocLayout";
import { AnalysisReportPage } from "./pages/AnalysisReportPage";
import { DataMappingPage } from "./pages/DataMappingPage";
import { HomePage } from "./pages/HomePage";
import { IntegrationCapabilitiesPage } from "./pages/IntegrationCapabilitiesPage";
import { PipelineDemoPage } from "./pages/PipelineDemoPage";
import { TourPage } from "./pages/TourPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DocLayout />}>
          <Route index element={<HomePage />} />
          <Route path="analysis-report" element={<AnalysisReportPage />} />
          <Route path="data-mapping" element={<DataMappingPage />} />
          <Route path="integration-capabilities" element={<IntegrationCapabilitiesPage />} />
          <Route path="live-demo" element={<PipelineDemoPage />} />
          <Route path="tour" element={<Navigate to="/tour/pipeline-overview" replace />} />
          <Route path="tour/:stepId" element={<TourPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
