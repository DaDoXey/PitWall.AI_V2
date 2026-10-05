// Quello che serve a percorsi e catture per entrare nell'app senza passare dal login.
import type { Page } from "@playwright/test";

/** L'utente demo già dentro, il wizard del profilo saltato: come dopo «Entra in modalità demo». */
export async function entraInDemo(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.setItem("pw_user", JSON.stringify({ kind: "demo", name: "Pilota demo" }));
    localStorage.setItem("pw_onboarding_skipped", "1");
  });
}

/** La pagina ha finito di chiedere dati al backend e i caratteri sono caricati. */
export async function pronta(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(async () => {
    await document.fonts.ready;
    // Le immagini (la mappa del circuito, le foto) arrivano dopo i dati: senza aspettarle
    // la stessa pagina veniva fotografata una volta con la mappa e una senza.
    await Promise.all(
      Array.from(document.images, (img) => (img.complete ? null : new Promise((fatto) => { img.onload = img.onerror = fatto; }))),
    );
  });
  // I pannelli che si adattano all'altezza si assestano un attimo dopo.
  await page.waitForTimeout(400);
}
