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

test("catture su tre formati, con il confronto", async ({ page }) => {
  test.setTimeout(240_000);
  fs.rmSync(ORA, { recursive: true, force: true });
  fs.mkdirSync(ORA, { recursive: true });
  await entraInDemo(page);

  const esito: { pagina: string; formato: string; file: string; stato: string; quota: number | null; scorre: boolean }[] = [];
  for (const formato of FORMATI) {
    await page.setViewportSize({ width: formato.width, height: formato.height });
    for (const pagina of PAGINE) {
      await page.goto(pagina);
      await pronta(page);
      const file = nomeFile(pagina, formato.nome);
      await page.screenshot({ path: path.join(ORA, file), animations: "disabled" });
      const scorre = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
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
  fs.writeFileSync(path.join(RADICE, "esito.json"), JSON.stringify(esito, null, 2));
});
