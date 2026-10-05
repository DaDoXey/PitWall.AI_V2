// I cinque percorsi principali di PitWall, sulla sessione demo (Monza · BMW M4 GT3).
// Non controllano l'aspetto (quello lo fanno le catture): controllano che il percorso
// arrivi in fondo e che i numeri della demo siano quelli del motore.
import { expect, test } from "@playwright/test";
import { entraInDemo, pronta } from "./aiuti";

test("1 · dal login si entra in demo e si arriva alla Dashboard", async ({ page }) => {
  await page.goto("/login");
  // Si aspetta che la pagina sia viva: un clic arrivato prima non fa niente (era la causa
  // di un rosso saltuario, soprattutto al primo percorso del giro).
  await pronta(page);
  await expect(async () => {
    await page.getByRole("button", { name: /Entra in modalità demo/ }).click();
    await expect(page).not.toHaveURL(/\/login/, { timeout: 3000 });
  }).toPass({ timeout: 20_000 });
  // Al primo ingresso c'è il wizard del profilo: lo si salta come farebbe chi ha fretta.
  const salta = page.getByRole("button", { name: /Salta per ora/ });
  if (await salta.isVisible().catch(() => false)) await salta.click();
  await expect(page.getByRole("link", { name: "Engineer Console" })).toBeVisible();
  await expect(page.getByText("1:47.820").first()).toBeVisible();
});

test("2 · la Engineer Console apre il debrief della demo", async ({ page }) => {
  await entraInDemo(page);
  await page.goto("/console");
  await pronta(page);
  await expect(page.getByRole("heading", { name: /GIGI/ })).toBeVisible();
  await expect(page.getByText("La prima cosa da fare")).toBeVisible();
  await expect(page.getByRole("button", { name: "Dove perdo?" })).toBeVisible();
  // Le domande stanno su una riga sola (prima erano sei, su due).
  const righe = await page.evaluate(() => {
    const domande = Array.from(document.querySelectorAll("button")).filter((b) => /\?$/.test(b.textContent?.trim() ?? ""));
    return new Set(domande.map((b) => Math.round(b.getBoundingClientRect().top))).size;
  });
  expect(righe).toBe(1);
  await page.getByRole("button", { name: "La prossima fase" }).click();
  // La pagina non scorre: scorre solo la conversazione.
  const scorre = await page.evaluate(() => document.documentElement.scrollHeight > window.innerHeight + 1);
  expect(scorre).toBe(false);
});

test("3 · una domanda a Gigi riceve una risposta dal debrief", async ({ page }) => {
  await entraInDemo(page);
  await page.goto("/console");
  await pronta(page);
  await page.getByRole("button", { name: "Dove perdo?" }).click();
  await expect(page.getByText(/In curva \d+: \d\.\d\d s a giro/)).toBeVisible();
  await page.getByRole("button", { name: "Sono migliorato?" }).click();
  await expect(page.getByText(/Sì: il giro migliore è 0\.33 s più veloce della volta prima/)).toBeVisible();
});

test("4 · l'archivio delle sessioni mostra la demo", async ({ page }) => {
  await entraInDemo(page);
  await page.goto("/sessioni");
  await pronta(page);
  await expect(page.getByText("Demo", { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/Monza/).first()).toBeVisible();
});

test("6 · su uno schermo stretto dice di aprirlo da computer, e si può guardare lo stesso", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 780 });
  await entraInDemo(page);
  await page.goto("/");
  const avviso = page.getByRole("dialog", { name: "Schermo troppo stretto" });
  await expect(avviso).toBeVisible();
  await expect(avviso.getByText("Aprilo da computer.")).toBeVisible();
  await avviso.getByRole("button", { name: "Guarda lo stesso" }).click();
  await expect(avviso).toBeHidden();
});

test("7 · se il servizio non risponde lo dice senza nomi tecnici, e «Riprova» riparte", async ({ page }) => {
  await entraInDemo(page);
  // Niente attesa dell'accensione: online vale 90 secondi, e questo percorso parla di ciò che
  // si legge DOPO l'attesa (l'attesa stessa la prova il percorso 8).
  await page.addInitScript(() => sessionStorage.setItem("pw_prova_accensione_s", "0"));
  // Il servizio «cade» solo per questa pagina: le richieste all'API falliscono come a rete assente.
  let fermo = true;
  await page.route("**/api/**", (rotta) => (fermo ? rotta.abort() : rotta.continue()));
  await page.goto("/console");
  const avviso = page.getByRole("alert").filter({ hasText: "PitWall non risponde in questo momento" }).first();
  await expect(avviso).toBeVisible();
  await expect(page.getByText(/FastAPI|backend|README|:8000/i)).toHaveCount(0);
  fermo = false;
  await avviso.getByRole("button", { name: "Riprova" }).click();
  await expect(page.getByText("La prima cosa da fare")).toBeVisible();
});

test("8 · se il servizio si sta riaccendendo aspetta e poi parte da solo", async ({ page }) => {
  await entraInDemo(page);
  await page.addInitScript(() => sessionStorage.setItem("pw_prova_accensione_s", "30"));
  let addormentato = true;
  await page.route("**/api/**", (rotta) => (addormentato ? rotta.abort() : rotta.continue()));
  await page.goto("/console");
  await expect(page.getByText("Il muretto si sta accendendo.")).toBeVisible();
  await expect(page.getByText("PitWall non risponde in questo momento")).toHaveCount(0);
  addormentato = false;
  // Riprova ogni 4 secondi, poi carica la Console: su Firefox servono anche più di 15 secondi.
  await expect(page.getByText("La prima cosa da fare")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Il muretto si sta accendendo.")).toHaveCount(0);
});

test("5 · il Setup e la Telemetria si aprono sui dati della demo", async ({ page }) => {
  await entraInDemo(page);
  await page.goto("/setup");
  await pronta(page);
  await expect(page.getByText(/Pressione/).first()).toBeVisible();
  await page.goto("/telemetry");
  await pronta(page);
  await expect(page.getByText("1:47.820").first()).toBeVisible();
});
