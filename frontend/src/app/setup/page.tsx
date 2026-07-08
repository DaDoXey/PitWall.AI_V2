import PageHeader from "@/components/ui/PageHeader";

export default function SetupPage() {
  return (
    <div>
      <PageHeader title="Setup" subtitle="range ACC" />
      <p className="text-sm text-subtle">
        In costruzione — <span className="text-accent">Fase 5</span>: 5 tab, 49 slider,
        colore pressioni vs finestra. Dati da <code>GET /api/setup-params?car&amp;track</code>.
      </p>
    </div>
  );
}
