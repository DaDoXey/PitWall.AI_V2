"use client";

// La vetrina online vive su un servizio che si addormenta dopo un quarto d'ora senza
// visite: il primo che arriva aspetta fino a un minuto che si riaccenda (pacchetto 1.3).
// In quel minuto non si mostra un errore: si dice che cosa sta succedendo, e la pagina
// riparte da sola. Finita l'attesa le pagine vengono rimontate, così anche quelle che
// avevano già chiesto dati a vuoto (Tracciati, Lezioni) li richiedono.
import Onda from "@/components/console/Onda";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";

export default function Accensione({ children }: { children: React.ReactNode }) {
  const { accensione, risvegli } = useSessione();
  return (
    <>
      {accensione && (
        <div
          role="status"
          aria-live="polite"
          className="fixed inset-0 z-[55] flex flex-col items-center justify-center gap-4 bg-bg px-8 text-center"
        >
          <Onda seme="accensione" barre={24} colore={COLORS.accent} viva />
          <p className="text-[1.15rem] font-medium text-white">Il muretto si sta accendendo.</p>
          <p className="max-w-sm text-sm leading-relaxed text-subtle">
            Dopo un po&apos; senza visite PitWall si spegne. Ci vuole fino a un minuto: la pagina parte da sola.
          </p>
        </div>
      )}
      <div key={risvegli}>{children}</div>
    </>
  );
}
