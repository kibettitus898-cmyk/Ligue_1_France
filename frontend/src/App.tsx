import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Pricing from "./pages/Pricing";
import Dashboard from "./pages/Dashboard";
import Predictions from "./pages/Predictions";
import Fixtures from "./pages/Fixtures";
import Subscription from "./pages/Subscription";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/predictions" element={<Predictions />} />
      <Route path="/fixtures" element={<Fixtures />} />
      <Route path="/subscription" element={<Subscription />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}