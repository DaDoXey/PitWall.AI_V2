"use client";

// Provider globali client-side (megaprompt #6, FASE 9): Google OAuth (popup
// Sign-In) + stato di accesso. Il Client ID è un identificatore PUBBLICO by
// design (env NEXT_PUBLIC_*); il client secret NON serve al flusso popup e non
// esiste da nessuna parte nel frontend.
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "@/lib/auth";

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <GoogleOAuthProvider clientId={CLIENT_ID}>
      <AuthProvider>{children}</AuthProvider>
    </GoogleOAuthProvider>
  );
}
