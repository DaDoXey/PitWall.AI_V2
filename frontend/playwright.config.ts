// Percorsi automatici e catture di PitWall (tabella di marcia, pacchetto 1.0).
// Non avvia i server: li vuole già accesi (`strumenti/server.ps1 avvia`), frontend su
// :3000 e backend su :8000 in demo-mode. Si lancia da `strumenti/verifica.py`.
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e/.risultati",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PITWALL_URL ?? "http://localhost:3000",
    browserName: "chromium",
    locale: "it-IT",
    // Le animazioni ferme: una cattura a metà transizione sembrerebbe una pagina cambiata.
    reducedMotion: "reduce",
  },
});
