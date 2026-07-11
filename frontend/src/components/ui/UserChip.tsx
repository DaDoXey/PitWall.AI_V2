"use client";

// Chip profilo utente in Sidebar (megaprompt #6, FASE 9): foto/nome/email reali
// dopo il Google Sign-In (o "Pilota demo" in modalità demo) + bottone Esci che
// chiude la sessione client-side e riporta al login. Nessun placeholder "N":
// creato da zero (F0: quello nelle immagini era l'indicatore dev di Next.js).
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function UserChip() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  if (!user) return null;

  const logout = () => {
    signOut();
    router.replace("/login");
  };

  return (
    <div className="flex items-center gap-2 rounded-lg border border-line bg-inset p-2">
      {user.kind === "google" && user.picture ? (
        // Foto profilo Google: <img> semplice (dominio esterno lh3.googleusercontent.com,
        // niente next/image per non toccare la config); no-referrer per igiene privacy.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.picture} alt="" referrerPolicy="no-referrer" className="h-7 w-7 shrink-0 rounded-full" />
      ) : (
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-line bg-raised text-sm" aria-hidden>
          🏁
        </span>
      )}
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs text-white">{user.name}</div>
        <div className="truncate font-mono text-[0.55rem] text-muted">
          {user.kind === "google" ? user.email : "modalità demo"}
        </div>
      </div>
      <button
        type="button"
        onClick={logout}
        title="Esci e torna al login"
        aria-label="Esci e torna al login"
        className="shrink-0 rounded border border-line px-1.5 py-1 font-mono text-[0.62rem] text-subtle transition hover:border-accent hover:text-white"
      >
        ⏻
      </button>
    </div>
  );
}
