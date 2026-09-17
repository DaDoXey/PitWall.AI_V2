import Sidebar from "@/components/ui/Sidebar";
import MotionProvider from "@/components/ui/MotionProvider";
import AuthGate from "@/components/ui/AuthGate";
import OnboardingFlow from "@/components/ui/OnboardingFlow";
import GigiTour from "@/components/ui/GigiTour";
import { SessioneProvider } from "@/lib/sessione";

// Layout dell'app "loggata" (megaprompt #6, FASE 8): Sidebar + area contenuti.
// Vive nel route group (app) — /login (gruppo (auth)) resta fuori e non eredita
// la Sidebar (fix INC-V2-004). AuthGate (FASE 9): senza accesso → /login.
// OnboardingFlow (megaprompt #9): wizard "Conosci il pilota" al primo accesso.
// SessioneProvider (L4): la sessione aperta, la stessa per tutte le schermate.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <SessioneProvider>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="max-w-6xl flex-1 px-6 py-6">
            <MotionProvider>{children}</MotionProvider>
          </main>
        </div>
        <OnboardingFlow />
        <GigiTour />
      </SessioneProvider>
    </AuthGate>
  );
}
