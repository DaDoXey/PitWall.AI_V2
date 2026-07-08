"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/ui/PageHeader";
import { getSession } from "@/lib/api";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getSession()
      .then(setData)
      .catch(() => setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
  }, []);

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Riepilogo ultima sessione" />

      {err && <p className="text-sm text-warn">{err}</p>}
      {!data && !err && <p className="text-sm text-subtle">Caricamento…</p>}

      {data && (
        <>
          <div className="mb-4 rounded-xl border border-l-4 border-line border-l-accent bg-surface p-5">
            <div className="font-mono text-[0.6rem] uppercase tracking-widest text-accent">
              Ultima sessione
            </div>
            <div className="mt-1 font-display text-2xl font-bold">{data.session.track}</div>
            <div className="text-sm text-subtle">
              {data.session.car} · {data.session.car_year}
            </div>
            <div className="mt-4 flex gap-8 border-t border-line pt-3 text-sm">
              <Stat label="Giri" value={`${data.session.laps} · Best ${data.session.best_lap}`} />
              <Stat
                label="Consumo"
                value={`${data.session.fuel_avg_per_lap} L/giro · ${data.session.fuel_total} L`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <MetricCard label="Temperatura gomme" value={`${data.temp.max.rr}°C`} note="Post.DX sopra finestra (95°C)" accent />
            <MetricCard label="Pressione media" value={`${data.pressure.avg_hot} psi`} note="Retrotreno sotto finestra" accent />
            <MetricCard label="Consumo medio" value={`${data.session.fuel_avg_per_lap} L/giro`} note={`Stabile · ${data.session.fuel_total} L totali`} />
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[0.6rem] uppercase text-muted">{label}</div>
      <div className="font-mono">{value}</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  note,
  accent,
}: {
  label: string;
  value: string;
  note: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-2 font-mono text-3xl">{value}</div>
      <div className={`mt-2 text-xs ${accent ? "text-accent" : "text-ok"}`}>{note}</div>
    </div>
  );
}
