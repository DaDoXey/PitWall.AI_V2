"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { postAnalysis } from "@/lib/api";
import {
  CHIPS,
  DEMO_QUESTION,
  parseSections,
  SETUP_SECTION_INDEX,
  SOURCE_LABELS,
  type Section,
} from "@/lib/console";

type Analysis = { question: string; text: string; source: string };

export default function ConsolePage() {
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [typed, setTyped] = useState("");
  const busy = useRef(false); // evita fetch sovrapposte (chip cliccati in serie)

  // Analizza un prompt via backend (demo-cache / LLM gated: la logica sta lì).
  async function analyze(prompt: string) {
    const p = prompt.trim();
    if (!p || busy.current) return;
    busy.current = true;
    setLoading(true);
    setErr(null);
    try {
      const res = await postAnalysis(p);
      setData(res);
    } catch {
      setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README).");
    } finally {
      setLoading(false);
      busy.current = false;
    }
  }

  // Stato iniziale: console SEMPRE popolata con lo scenario demo (mai vuota).
  useEffect(() => {
    analyze(DEMO_QUESTION);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (typed.trim()) {
      analyze(typed);
      setTyped("");
    }
  }

  const sections = data ? parseSections(data.text) : [];

  return (
    <div>
      <PageHeader title="Engineer Console" subtitle="Gigi · Race Engineer" />

      {/* Header Gigi */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="mb-5 flex items-center gap-3 rounded-xl border border-line border-l-[3px] border-l-accent bg-gradient-to-br from-surface to-raised px-4 py-3"
      >
        <GigiAvatar size={44} />
        <div className="flex-1">
          <div className="font-display text-sm font-bold tracking-wide">Gigi</div>
          <div className="mt-0.5 font-mono text-[0.62rem] uppercase tracking-widest text-muted">
            Race Engineer
          </div>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[0.6rem] uppercase tracking-widest text-ok">
          <span className="h-1.5 w-1.5 rounded-full bg-ok shadow-[0_0_6px_#00C853]" />
          online
        </div>
      </motion.div>

      {/* Scenari rapidi */}
      <div className="mb-2 font-mono text-[0.62rem] uppercase tracking-widest text-muted">
        Scenari rapidi
      </div>
      <div className="mb-4 grid grid-cols-2 gap-2 md:grid-cols-4">
        {CHIPS.map((chip) => (
          <motion.button
            key={chip}
            onClick={() => analyze(chip)}
            disabled={loading}
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.97 }}
            className="rounded-md border border-line bg-surface px-3 py-2 text-sm text-subtle transition hover:border-line-strong hover:bg-raised disabled:cursor-not-allowed disabled:opacity-50"
          >
            {chip}
          </motion.button>
        ))}
      </div>

      {/* Input + ANALIZZA */}
      <form onSubmit={onSubmit} className="mb-4 flex gap-2">
        <input
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          placeholder="Descrivi il problema in pista… (es. «L'auto scivola dietro in accelerazione»)"
          className="flex-1 rounded-md border border-line bg-inset px-3 py-2 text-sm text-white placeholder:text-muted focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !typed.trim()}
          className="shrink-0 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          ⚙ ANALIZZA
        </button>
      </form>

      {err && <p className="mb-4 text-sm text-warn">{err}</p>}

      {/* Barra "Analisi richiesta" + sorgente */}
      {data && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">
            Analisi richiesta
          </span>
          <span className="rounded-md border border-accent/25 bg-accent/10 px-2.5 py-1 text-[0.82rem] text-white">
            {data.question}
          </span>
          <span className="ml-auto font-mono text-[0.56rem] uppercase tracking-widest text-ok">
            ● {SOURCE_LABELS[data.source] ?? data.source}
          </span>
        </div>
      )}

      {/* Spinner / 4 card */}
      {loading && !data ? (
        <p className="text-sm text-subtle">Gigi sta analizzando…</p>
      ) : (
        <motion.div
          key={data?.question} // nuova analisi → remount → l'ingresso a cascata ri-scatta
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className={loading ? "opacity-50 transition" : "transition"}
        >
          {sections.map((s, i) => (
            <motion.div key={s.title} variants={fadeInUp}>
              <AnalysisCard index={i} section={s} isSetup={i === SETUP_SECTION_INDEX} />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Card analisi (una delle 4 sezioni)
// ─────────────────────────────────────────────
function AnalysisCard({
  index,
  section,
  isSetup,
}: {
  index: number;
  section: Section;
  isSetup: boolean;
}) {
  const num = String(index + 1).padStart(2, "0");
  return (
    <div
      className={`mb-3 rounded-xl border p-4 ${
        isSetup ? "border-accent bg-accent/[0.06]" : "border-line bg-surface"
      }`}
    >
      <div className="mb-2.5 flex items-center gap-2.5 border-b border-line pb-2.5">
        <span className="font-mono text-[0.95rem] text-accent">{num}</span>
        <span className="text-base">{section.icon}</span>
        <span className="font-display text-[0.8rem] font-bold uppercase tracking-wide text-white">
          {section.title}
        </span>
        {isSetup && (
          <span className="ml-auto rounded border border-accent px-1.5 py-0.5 font-mono text-[0.56rem] uppercase tracking-widest text-accent">
            Scheda Setup
          </span>
        )}
      </div>
      <div
        className={`text-[0.86rem] leading-relaxed text-[#bbbbbb] ${
          isSetup ? "rounded-lg border border-accent bg-inset p-3.5" : ""
        }`}
      >
        <SectionBody body={section.body} />
      </div>
      {isSetup && (
        <Link
          href="/setup"
          className="mt-3 inline-flex items-center gap-1 font-mono text-[0.62rem] uppercase tracking-widest text-accent transition hover:underline"
        >
          Vedi i parametri evidenziati in Setup →
        </Link>
      )}
    </div>
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

// Avatar Gigi (SVG inline, casco stilizzato con visiera accent).
function GigiAvatar({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="23" fill="#1a1a1a" stroke="#333333" />
      <path d="M12 26a12 12 0 0 1 24 0v4H12v-4Z" fill="#E8002D" />
      <path d="M14 25a10 10 0 0 1 20 0v2H14v-2Z" fill="#0a0a0a" />
      <rect x="15" y="27" width="18" height="7" rx="2" fill="#141414" stroke="#333333" />
      <rect x="18" y="29" width="12" height="3" rx="1.5" fill="#E8002D" opacity="0.85" />
    </svg>
  );
}
