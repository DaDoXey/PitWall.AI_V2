// I cinque percorsi principali di PitWall, sulla sessione demo (Monza · BMW M4 GT3).
// Non controllano l'aspetto (quello lo fanno le catture): controllano che il percorso
// arrivi in fondo e che i numeri della demo siano quelli del motore.
import { expect, test } from "@playwright/test";
import { entraInDemo, pronta } from "./aiuti";

test("1 · dal login si entra in demo e si arriva alla Dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /Entra in modalità demo/ }).click();
  await expect(page).not.toHaveURL(/\/login/);
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

test("5 · il Setup e la Telemetria si aprono sui dati della demo", async ({ page }) => {
  await entraInDemo(page);
  await page.goto("/setup");
  await pronta(page);
  await expect(page.getByText(/Pressione/).first()).toBeVisible();
  await page.goto("/telemetry");
  await pronta(page);
  await expect(page.getByText("1:47.820").first()).toBeVisible();
});
