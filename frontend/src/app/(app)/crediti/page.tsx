// Pagina crediti — obbligo di licenza, non un vezzo.
// Gli asset visivi vengono da Wikimedia Commons: CC BY e CC BY-SA richiedono
// che autore e licenza siano visibili ALL'UTENTE FINALE, non solo nel repo.
// La tabella è generata da backend/scripts/fetch_assets.py in
// public/assets/ATTRIBUTIONS.md: qui viene letta a build-time (Server
// Component, niente fetch dal client) e resa in pagina.
import fs from "node:fs";
import path from "node:path";
import PageHeader from "@/components/ui/PageHeader";

// ATTRIBUTIONS.md viene riscritto ogni volta che si rilanciano gli asset:
// senza questo, Next serve il render fatto la prima volta che la rotta è stata
// compilata e la tabella resta ferma a com'era (o vuota).
export const dynamic = "force-dynamic";

type Row ={ file: string; entita: string; ruolo: string; autore: string; licenza: string; pagina: string };

/** Estrae le righe dalla tabella markdown di ATTRIBUTIONS.md. */
function readAttributions(): { rows: Row[]; missing: boolean } {
  const file = path.join(process.cwd(), "public", "assets", "ATTRIBUTIONS.md");
  let raw: string;
  try {
    raw = fs.readFileSync(file, "utf-8");
  } catch {
    // Asset non ancora scaricati: la pagina lo dice invece di rompersi.
    return { rows: [], missing: true };
  }

  const rows: Row[] = [];
  // split su /\r?\n/: il file è scritto da Python su Windows, quindi ha
  // terminatori CRLF. Con split("\n") ogni riga conserva un "\r" finale e
  // l'ancora `$` della regex non aggancia mai (tabella vuota, senza errori).
  for (const line of raw.split(/\r?\n/)) {
    // Righe dati della tabella: | `file` | entità | ruolo | autore | licenza | [link](url) |
    const m = line.match(
      /^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|$/,
    );
    if (m) {
      rows.push({ file: m[1], entita: m[2], ruolo: m[3], autore: m[4], licenza: m[5], pagina: m[6] });
    }
  }
  return { rows, missing: false };
}

export default function CreditiPage() {
  const { rows, missing } = readAttributions();

  return (
    <div>
      <PageHeader title="Crediti" subtitle="attribuzioni degli asset visivi" />

      <div className="mb-6 rounded-xl border border-line bg-surface p-5">
        <p className="text-sm leading-relaxed text-subtle">
          Le immagini di vetture e circuiti provengono da{" "}
          <a
            href="https://commons.wikimedia.org"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent underline-offset-2 hover:underline"
          >
            Wikimedia Commons
          </a>
          . Le licenze Creative Commons BY e BY-SA richiedono che autore e licenza siano
          indicati: questa pagina assolve a quell&apos;obbligo.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-subtle">
          I <span className="text-white">loghi dei costruttori</span> restano marchi registrati
          dei rispettivi titolari anche quando il file immagine è di pubblico dominio:
          l&apos;uso qui è puramente identificativo della vettura.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-subtle">
          I dati tecnici di vetture e circuiti provengono dal catalogo del progetto; dove non
          sono confermati su fonte primaria, le schede lo dichiarano.
        </p>
      </div>

      {missing ? (
        <div className="rounded-xl border border-line bg-surface p-5 text-sm text-subtle">
          Nessun asset scaricato: esegui{" "}
          <code className="font-mono text-xs text-white">
            python backend/scripts/fetch_assets.py --auto
          </code>{" "}
          per popolare la galleria e generare le attribuzioni.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead>
              <tr className="border-b border-line font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                <th className="px-4 py-3">Soggetto</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Autore</th>
                <th className="px-4 py-3">Licenza</th>
                <th className="px-4 py-3">Fonte</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.file} className="border-b border-line/60 last:border-0">
                  <td className="px-4 py-2.5 font-mono text-xs text-white">{r.entita}</td>
                  <td className="px-4 py-2.5 text-xs text-muted">{r.ruolo}</td>
                  <td className="px-4 py-2.5 text-subtle">{r.autore}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-subtle">{r.licenza}</td>
                  <td className="px-4 py-2.5">
                    <a
                      href={r.pagina}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-xs text-accent underline-offset-2 hover:underline"
                    >
                      Commons ↗
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {rows.length > 0 && (
        <p className="mt-3 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
          {rows.length} asset · generato da fetch_assets.py
        </p>
      )}
    </div>
  );
}
