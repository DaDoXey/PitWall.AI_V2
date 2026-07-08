import PageHeader from "@/components/ui/PageHeader";

export default function TelemetryPage() {
  return (
    <div>
      <PageHeader title="Telemetria" subtitle="Monza · BMW M4 GT3 · 8 giri" />
      <p className="text-sm text-subtle">
        In costruzione — <span className="text-accent">Fase 3</span>: line chart (Recharts),
        gauge/heatmap/sparkline come componenti SVG, tabella giro-per-giro. Dati da{" "}
        <code>GET /api/session</code>.
      </p>
    </div>
  );
}
