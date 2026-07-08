import PageHeader from "@/components/ui/PageHeader";

export default function ConsolePage() {
  return (
    <div>
      <PageHeader title="Engineer Console" subtitle="Gigi · Race Engineer" />
      <p className="text-sm text-subtle">
        In costruzione — <span className="text-accent">Fase 4</span>: analisi a 4 sezioni
        (chip + input) cablata a <code>POST /api/analysis</code> (demo-cache / LLM gated).
      </p>
    </div>
  );
}
