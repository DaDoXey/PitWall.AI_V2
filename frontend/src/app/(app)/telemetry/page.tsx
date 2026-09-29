"use client";

// Telemetria (L4): tre viste sulla sessione aperta, tutte dal report del motore.
// Via le viste della v1 costruite su numeri scritti a mano e su conti fatti nel browser
// (corsie, scatter, radar «bilanciamento», confronto metà stint): nessuna poggiava su
// una misura dimostrata.
import { useState } from "react";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import Tabs from "@/components/ui/Tabs";
import { StatoSessione } from "@/components/ui/Verdetto";
import GiriSessione from "@/components/charts/GiriSessione";
import AnalisiCurve from "@/components/charts/AnalisiCurve";
import GommeFreni from "@/components/charts/GommeFreni";
import { fadeInUp } from "@/lib/motion";
import { useSessione } from "@/lib/sessione";
import { ETICHETTA_TIPO, giri } from "@/lib/formato";

export default function TelemetryPage() {
  const { report, idSessione, caricamento, errore, nomi } = useSessione();
  // Il tab scelto vive qui, non dentro i Tabs: mentre una sessione nuova carica i Tabs
  // spariscono, e al ritorno ripartirebbero da «Giri».
  const [tab, setTab] = useState("giri");

  if (!report || !idSessione)
    return (
      <div>
        <PageHeader title="Telemetria" />
        <StatoSessione errore={errore} caricamento={caricamento || !report} />
      </div>
    );

  return (
    <div>
      <PageHeader
        title="Telemetria"
        subtitle={`${nomi.pista(report.track)} · ${nomi.vettura(report.car)} · ${ETICHETTA_TIPO[report.tipo_sessione] ?? "sessione"} · ${giri(report.giri_totali)}`}
      />
      {!report.ha_canali && (
        <motion.div variants={fadeInUp} initial="hidden" animate="visible" className="mb-4 rounded-xl border border-line bg-surface p-3 text-[0.8rem] text-subtle">
          Questa sessione non ha la telemetria registrata: ci sono i tempi, non curve, gomme e freni. Su PC il
          registratore di PitWall la cattura da solo mentre giri.
        </motion.div>
      )}
      <motion.div variants={fadeInUp} initial="hidden" animate="visible">
        {/* Il tab scelto resta quando cambi sessione (es. dall'invito della demo verso la
            sessione con la guida); i contenuti invece ripartono da zero, con la chiave. */}
        <Tabs
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "giri", label: "Giri", content: <GiriSessione key={idSessione} report={report} /> },
            { id: "curve", label: "Curve", content: <AnalisiCurve key={idSessione} report={report} idSessione={idSessione} /> },
            { id: "gomme", label: "Gomme e freni", content: <GommeFreni key={idSessione} report={report} /> },
          ]}
        />
      </motion.div>
    </div>
  );
}
