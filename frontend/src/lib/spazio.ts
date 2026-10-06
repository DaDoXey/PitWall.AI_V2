// Uno spazio per ogni pilota, senza registrarsi (tabella di marcia, 2.2).
//
// Dove il servizio è di più persone (online) il browser genera un codice lungo e casuale,
// lo conserva e lo manda a ogni richiesta: il backend tiene le sessioni di quel codice in
// una cartella sua. Chi ha il codice ha lo spazio, quindi:
//   * non finisce mai in un indirizzo (solo in un'intestazione della richiesta);
//   * sta in localStorage sotto una chiave che NON comincia per `pw_`: l'ingresso in
//     modalità demo cancella tutte le chiavi `pw_*`, e il codice non deve sparire con loro.
// In locale gli spazi sono spenti: nessun codice, nessuna intestazione, tutto come prima.

const CHIAVE = "pitwall_spazio";
export const INTESTAZIONE_SPAZIO = "X-PitWall-Spazio";
const VALIDO = /^[A-Za-z0-9_-]{32,64}$/;

/** Il codice di questo browser, se ne ha uno. */
export function codiceSpazio(): string | null {
  try {
    const c = localStorage.getItem(CHIAVE);
    return c && VALIDO.test(c) ? c : null;
  } catch {
    return null;
  }
}

/** Il codice di questo browser; se manca lo crea (48 caratteri esadecimali, 192 bit casuali). */
export function assicuraCodiceSpazio(): string {
  const presente = codiceSpazio();
  if (presente) return presente;
  const byte = crypto.getRandomValues(new Uint8Array(24));
  const nuovo = Array.from(byte, (b) => b.toString(16).padStart(2, "0")).join("");
  localStorage.setItem(CHIAVE, nuovo);
  return nuovo;
}

/** Usa un codice ricevuto da un altro browser. Torna false se non ha la forma di un codice. */
export function usaCodiceSpazio(grezzo: string): boolean {
  const codice = grezzo.trim();
  if (!VALIDO.test(codice)) return false;
  localStorage.setItem(CHIAVE, codice);
  return true;
}

/** Le intestazioni di una richiesta al backend, con il codice dello spazio se c'è. */
export function conSpazio(intestazioni?: Record<string, string>): Record<string, string> | undefined {
  const codice = typeof window === "undefined" ? null : codiceSpazio();
  if (!codice) return intestazioni;
  return { ...(intestazioni ?? {}), [INTESTAZIONE_SPAZIO]: codice };
}
