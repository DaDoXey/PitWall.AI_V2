"use client";

// A Lezione con Gigi (megaprompt #8, FASE 1): placeholder della sezione lezioni.
// L'indice a 8 card arriva in FASE 2 (dati da lib/lessons.ts, content pack in docs/).
import PageHeader from "@/components/ui/PageHeader";

export default function LezioniPage() {
  return (
    <div>
      <PageHeader
        title="A Lezione con Gigi"
        subtitle="Gigi · i fondamentali per andare più forte"
      />
      <p className="font-mono text-xs uppercase tracking-widest text-muted">
        Lezioni in preparazione · prossimamente
      </p>
    </div>
  );
}
