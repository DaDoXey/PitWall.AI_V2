"use client";

// Il rapporto completo (#060): le 5 sezioni di sempre (Diagnosi, Causa meccanica,
// Correzione setup, Correzione di guida, Note) per chi le vuole tutte insieme. Si apre
// da un pulsante della Console; il testo è quello di /api/analysis (cache sulla demo,
// motore sulle altre sessioni, modello quando Gigi dal vivo è acceso).
import { Fragment, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { postAnalysis } from "@/lib/api";
import { DEMO_QUESTION, DOMANDA_SESSIONE, parseSections, SETUP_SECTION_INDEX, SOURCE_LABELS } from "@/lib/console";
import { profileContextLine, useProfile } from "@/lib/profile";
import { useSessione } from "@/lib/sessione";

export default function RapportoCompleto({ aperto, onChiudi }: { aperto: boolean; onChiudi: () => void }) {
  const { idSessione, sessione } = useSessione();
  const { profile } = useProfile();
  const [testo, setTesto] = useState<{ text: string; source: string; per: string } | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    if (!aperto || !idSessione || testo?.per === idSessione) return;
    let vivo = true;
    setErrore(null);
    postAnalysis(sessione?.demo ? DEMO_QUESTION : DOMANDA_SESSIONE, profile ? profileContextLine(profile) : undefined, idSessione)
      .then((r) => vivo && setTesto({ text: r.text, source: r.source, per: idSessione }))
      .catch(() => vivo && setErrore("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
    return () => {
      vivo = false;
    };
  }, [aperto, idSessione, sessione?.demo, profile, testo?.per]);

  useEffect(() => {
    if (!aperto) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onChiudi();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [aperto, onChiudi]);

  if (!aperto || typeof document === "undefined") return null;
  const sezioni = testo && testo.per === idSessione ? parseSections(testo.text) : [];

  return createPortal(
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={onChiudi}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Rapporto completo di Gigi"
        onClick={(e) => e.stopPropagation()}
        className="pw-scroll flex h-full w-full max-w-2xl flex-col gap-3 overflow-y-auto border-l border-line bg-bg p-6"
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-display text-lg font-bold">Rapporto completo</div>
            <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">
              le 5 sezioni di Gigi{testo ? ` · ${SOURCE_LABELS[testo.source] ?? testo.source}` : ""}
            </div>
          </div>
          <button type="button" onClick={onChiudi} className="rounded-md border border-line-strong px-3 py-1.5 font-mono text-[0.62rem] uppercase tracking-widest text-subtle transition hover:border-accent hover:text-white">
            Chiudi
          </button>
        </div>
        {errore && <p className="text-sm text-warn">{errore}</p>}
        {!testo && !errore && <p className="text-sm text-subtle">Gigi sta scrivendo il rapporto…</p>}
        {sezioni.map((s, i) => (
          <div key={s.title} className={`rounded-xl border p-4 ${i === SETUP_SECTION_INDEX ? "border-accent bg-accent/[0.06]" : "border-line bg-surface"}`}>
            <div className="mb-2 flex items-center gap-2.5 border-b border-line pb-2">
              <span className="font-mono text-[0.85rem] text-accent">{String(i + 1).padStart(2, "0")}</span>
              <span className="font-display text-[0.75rem] font-bold uppercase tracking-wide text-white">{s.title}</span>
            </div>
            <div className="text-[0.85rem] leading-relaxed text-[#bbbbbb]">
              <SectionBody body={s.body} />
            </div>
            {i === SETUP_SECTION_INDEX && (
              <Link href="/setup" className="mt-3 inline-flex font-mono text-[0.6rem] uppercase tracking-widest text-accent hover:underline">
                I parametri nel Setup →
              </Link>
            )}
          </div>
        ))}
      </aside>
    </div>,
    document.body,
  );
}

// ─────────────────────────────────────────────
// Markdown-lite → React: grassetto **…**, `code`, liste, paragrafi.
// Porta _md_lite della v1; nessuna libreria esterna.
// ─────────────────────────────────────────────
function SectionBody({ body }: { body: string }) {
  if (!body.trim()) {
    return <span className="italic text-muted">— sezione non disponibile</span>;
  }

  const blocks: React.ReactNode[] = [];
  let para: string[] = [];
  let items: string[] = [];
  let key = 0;

  const flushPara = () => {
    if (para.length) {
      blocks.push(
        <p key={key++} className="mb-2 last:mb-0">
          {para.map((line, i) => (
            <Fragment key={i}>
              {i > 0 && <br />}
              {renderInline(line)}
            </Fragment>
          ))}
        </p>
      );
      para = [];
    }
  };
  const flushList = () => {
    if (items.length) {
      blocks.push(
        <ul key={key++} className="mb-2 list-disc pl-5 last:mb-0">
          {items.map((it, i) => (
            <li key={i} className="my-0.5">
              {renderInline(it)}
            </li>
          ))}
        </ul>
      );
      items = [];
    }
  };

  for (const raw of body.split("\n")) {
    const s = raw.trim();
    if (!s) {
      flushPara();
      flushList();
      continue;
    }
    if (/^(?:[-*]|\d+\.)\s+/.test(s)) {
      flushPara();
      items.push(s.replace(/^(?:[-*]|\d+\.)\s+/, ""));
    } else {
      flushList();
      para.push(s);
    }
  }
  flushPara();
  flushList();

  return <>{blocks}</>;
}

// Inline: **grassetto** e `code`. Tokenizza senza HTML grezzo (sicuro by-default in React).
function renderInline(text: string): React.ReactNode {
  const nodes: React.ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|`(.+?)`/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    if (m[1] !== undefined) {
      nodes.push(
        <strong key={key++} className="font-semibold text-white">
          {m[1]}
        </strong>
      );
    } else {
      nodes.push(
        <code key={key++} className="rounded bg-raised px-1 py-0.5 font-mono text-[0.8em] text-accent">
          {m[2]}
        </code>
      );
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}
