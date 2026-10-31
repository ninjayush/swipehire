import { Navigate, Route, Routes } from "react-router-dom";
import { CandidateLayout, RecruiterLayout } from "./components/Layouts";
import Landing from "./pages/Landing";
import Dashboard from "./pages/recruiter/Dashboard";
import CompanyPage from "./pages/recruiter/Company";
import Jobs from "./pages/recruiter/Jobs";
import NewJob from "./pages/recruiter/NewJob";
import Requirements from "./pages/recruiter/Requirements";
import Discover from "./pages/recruiter/Discover";
import Deck from "./pages/recruiter/Deck";
import Shortlist from "./pages/recruiter/Shortlist";
import Saved from "./pages/recruiter/Saved";
import RInterests from "./pages/recruiter/Interests";
import RMatches from "./pages/recruiter/Matches";
import Settings from "./pages/recruiter/Settings";
import CHome from "./pages/candidate/Home";
import Onboarding from "./pages/candidate/Onboarding";
import CProfile from "./pages/candidate/Profile";
import CInterests from "./pages/candidate/Interests";
import CMatches from "./pages/candidate/Matches";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/recruiter" element={<RecruiterLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="company" element={<CompanyPage />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="jobs/new" element={<NewJob />} />
        <Route path="jobs/:jobId" element={<Navigate to="requirements" replace />} />
        <Route path="jobs/:jobId/requirements" element={<Requirements />} />
        <Route path="jobs/:jobId/discover" element={<Discover />} />
        <Route path="jobs/:jobId/deck" element={<Deck />} />
        <Route path="jobs/:jobId/shortlist" element={<Shortlist />} />
        <Route path="saved" element={<Saved />} />
        <Route path="interests" element={<RInterests />} />
        <Route path="matches" element={<RMatches />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="/candidate" element={<CandidateLayout />}>
        <Route index element={<CHome />} />
        <Route path="onboarding" element={<Onboarding />} />
        <Route path="enrich" element={<Navigate to="../onboarding" replace />} />
        <Route path="resume" element={<Navigate to="../onboarding" replace />} />
        <Route path="preferences" element={<Navigate to="../onboarding" replace />} />
        <Route path="profile" element={<CProfile />} />
        <Route path="interests" element={<CInterests />} />
        <Route path="matches" element={<CMatches />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
