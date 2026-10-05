// Le catture delle pagine su tre formati di schermo, con il confronto rispetto alla volta
// prima. Non fa fallire niente: scrive `e2e/catture/esito.json` con le pagine cambiate,
// così a schermo si guardano solo quelle. La verifica a occhio resta di Edoardo.
//
//   e2e/catture/ora/     le catture di questo giro
//   e2e/catture/prima/   quelle del giro precedente (il termine di paragone)
//   e2e/catture/esito.json
//
// «Accetta» = le catture di ora diventano il termine di paragone: lo fa
// `strumenti/verifica.py --accetta-catture`.
import fs from "node:fs";
import path from "node:path";
import { test } from "@playwright/test";
import sharp from "sharp";
import { entraInDemo, pronta } from "./aiuti";

const PAGINE = ["/", "/console", "/telemetry", "/setup", "/sessioni", "/tracciati", "/lezioni", "/crediti", "/login"];
// Il primo è lo schermo di Edoardo (1920×1080 al 125%); gli altri due sono i più comuni.
const FORMATI = [
  { nome: "1536x695", width: 1536, height: 695 },
  { nome: "1920x1080", width: 1920, height: 1080 },
  { nome: "1366x768", width: 1366, height: 768 },
];
// Sotto questa quota di pixel diversi la pagina è «uguale» (bordi sfumati, arrotondamenti).
const SOGLIA = 0.001;

const RADICE = path.join(__dirname, "catture");
const ORA = path.join(RADICE, "ora");
const PRIMA = path.join(RADICE, "prima");

const nomeFile = (pagina: string, formato: string) => `${pagina === "/" ? "dashboard" : pagina.slice(1)}_${formato}.png`;

async function quotaDiversa(a: string, b: string): Promise<number | null> {
  const [x, y] = await Promise.all([a, b].map((f) => sharp(f).raw().ensureAlpha().toBuffer({ resolveWithObject: true })));
  if (x.info.width !== y.info.width || x.info.height !== y.info.height) return 1;
  let diversi = 0;
  for (let i = 0; i < x.data.length; i += 4) {
    if (Math.abs(x.data[i] - y.data[i]) + Math.abs(x.data[i + 1] - y.data[i + 1]) + Math.abs(x.data[i + 2] - y.data[i + 2]) > 30) diversi++;
  }
  return diversi / (x.data.length / 4);
}

test("catture su tre formati, con il confronto", async ({ page, browser }) => {
  test.setTimeout(240_000);
  fs.rmSync(ORA, { recursive: true, force: true });
  fs.mkdirSync(ORA, { recursive: true });
  await entraInDemo(page);
  // La pagina di login si fotografa da fuori: con l'utente demo già dentro l'app rimanda
  // alla Dashboard, e la cattura «login» era una seconda Dashboard.
  const fuori = await browser.newContext({ locale: "it-IT", reducedMotion: "reduce" });
  const ospite = await fuori.newPage();

  // Un giro a vuoto prima di fotografare: la prima pagina dopo un riavvio dei server arriva
  // a pezzi (dati e immagini in ritardo) e risultava «cambiata» senza esserlo.
  await page.goto("/");
  await pronta(page);
  await page.goto("/console");
  await pronta(page);

  const esito: { pagina: string; formato: string; file: string; stato: string; quota: number | null; scorre: boolean }[] = [];
  for (const formato of FORMATI) {
    await page.setViewportSize({ width: formato.width, height: formato.height });
    await ospite.setViewportSize({ width: formato.width, height: formato.height });
    for (const pagina of PAGINE) {
      const scheda = pagina === "/login" ? ospite : page;
      await scheda.goto(pagina);
      await pronta(scheda);
      const file = nomeFile(pagina, formato.nome);
      await scheda.screenshot({ path: path.join(ORA, file), animations: "disabled" });
      const scorre = await scheda.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
      const precedente = path.join(PRIMA, file);
      let stato = "nuova";
      let quota: number | null = null;
      if (fs.existsSync(precedente)) {
        quota = await quotaDiversa(path.join(ORA, file), precedente);
        stato = quota !== null && quota > SOGLIA ? "cambiata" : "uguale";
      }
      esito.push({ pagina, formato: formato.nome, file, stato, quota, scorre });
    }
  }
  await fuori.close();
  fs.writeFileSync(path.join(RADICE, "esito.json"), JSON.stringify(esito, null, 2));
});
