import MotionProvider from "@/components/ui/MotionProvider";

// Layout auth (megaprompt #6, FASE 8): nessuna Sidebar, card centrata a tutto
// schermo — la pagina di login è un ingresso, non una vista dell'app.
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-8">
      <MotionProvider>{children}</MotionProvider>
    </main>
  );
}
