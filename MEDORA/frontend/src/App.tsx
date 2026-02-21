import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { VoiceCommandBar } from "@/components/VoiceCommandBar";
import { Wellbeing } from "@/pages/Wellbeing";
import { WellbeingVoice } from "@/pages/WellbeingVoice";
import { VirtualDoctor } from "@/pages/VirtualDoctor";
import { Dietary } from "@/pages/Dietary";
import { Ask } from "@/pages/Ask";
import { Diagnostic } from "@/pages/Diagnostic";
import { Login } from "@/pages/Login";
import { Signup } from "@/pages/Signup";
import { Profile } from "@/pages/Profile";
import { About } from "@/pages/About";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 0 },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/ask" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route path="/ask" element={<Ask />} />
            <Route path="/virtual-doctor" element={<VirtualDoctor />} />
            <Route path="/dietary" element={<Dietary />} />
            <Route path="/wellbeing/voice" element={<WellbeingVoice />} />
            <Route path="/wellbeing" element={<Wellbeing />} />
            <Route path="/diagnostic" element={<Diagnostic />} />
            <Route path="/about" element={<About />} />
          </Routes>
          <VoiceCommandBar />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;

