// Dati "A Lezione con Gigi" (megaprompt #8, FASE 2). FONTE DI VERITÀ dei testi:
// docs/A_Lezione_con_Gigi_ContentPack_v1.md — le correzioni si applicano QUI (o nel
// content pack), mai nei componenti. File NON protetto, read-only per la UI: nessuno
// stato, nessun quiz, nessuno storage.
// `videoId === "TODO"` finché Edoardo non conferma gli URL: la UI mostra "video in arrivo".

export type Lesson = {
  slug: string;
  number: number;
  title: string;
  summary: string; // una riga (card indice)
  whyItMatters: string;
  whenToUse?: string; // la Lezione 7 non lo definisce nel content pack
  howTo: string[];
  commonMistakes: string[];
  pitwallLink?: {
    // SOLO Gomme (→ Telemetria) e LiCo (→ strategia carburante)
    label: string;
    href: string;
  };
  video: {
    channel: string;
    title: string;
    videoId: string; // "TODO" finché non confermato
  };
};

export const LESSONS: Lesson[] = [
  {
    slug: "linea-ideale",
    number: 1,
    title: "La linea ideale (Racing Line)",
    summary: "Il percorso che minimizza il tempo sul giro, non quello che massimizza la velocità in curva.",
    whyItMatters:
      "Gran parte del tempo si guadagna in uscita. Una linea che apre l'uscita ti fa aprire il gas prima e ti porti quella velocità per tutto il rettilineo successivo — dove il vantaggio si moltiplica.",
    whenToUse: "Sempre. Ma la scelta dell'apex dipende dalla curva.",
    howTo: [
      "Schema base: out-in-out (largo in ingresso, stringi all'apex, largo in uscita).",
      "Apex geometrico (metà curva) → curve veloci senza un lungo rettilineo dopo.",
      "Apex tardivo (oltre metà) → curve lente seguite da rettilineo: sacrifichi l'ingresso per raddrizzare prima l'uscita → \"slow in, fast out\".",
      "Regola pratica (Ross Bentley): più la curva è veloce, più ti avvicini alla linea geometrica; più è lenta, più ritardi l'apex.",
    ],
    commonMistakes: [
      "Apex anticipato (early apex) → uscita larga, devi richiudere lo sterzo e perdi trazione; è l'errore classico del principiante.",
      "Guardare la curva invece del punto di uscita.",
    ],
    video: { channel: "Driver61", title: "How to Drive the Perfect Racing Line", videoId: "TODO" },
  },
  {
    slug: "punti-di-riferimento",
    number: 2,
    title: "Punti di riferimento (Reference Points)",
    summary: "Riferimenti fissi a bordo pista per frenare, girare e aprire il gas sempre nello stesso punto.",
    whyItMatters:
      "La consistenza nasce dai riferimenti. Senza, ogni giro è diverso e non puoi migliorare in modo misurabile: sono la base di tutto il resto.",
    whenToUse: "Quando impari un tracciato nuovo, e per ripetere il giro veloce.",
    howTo: [
      "Fissa 3 riferimenti per curva: punto di frenata, punto di corda (turn-in/apex), punto di uscita.",
      "Usa i cartelli dei 100/50 m dove ci sono; altrimenti un riferimento visivo fisso (un cordolo, un cambio d'asfalto, un cartello pubblicitario).",
      "Inizia a frenare prima, poi anticipa progressivamente man mano che prendi confidenza.",
    ],
    commonMistakes: [
      "Usare riferimenti mobili (altre auto).",
      "Riferimenti troppo vicini alla curva.",
      "Non avere un riferimento di uscita.",
    ],
    video: { channel: "Driver61", title: "Guida: imparare un tracciato nuovo", videoId: "TODO" },
  },
  {
    slug: "frenata-soglia",
    number: 3,
    title: "Frenata: soglia e anti-bloccaggio (Threshold Braking)",
    summary: "Frenare alla massima decelerazione possibile senza bloccare, con l'auto in rettilineo.",
    whyItMatters:
      "Buona parte del tempo di una staccata si gioca qui. Una frenata al limite ti fa staccare più tardi e arrivare all'ingresso curva più veloce ma controllato.",
    whenToUse: "In ogni staccata; è la fase \"in rettilineo\" prima dell'eventuale trail braking.",
    howTo: [
      "Picco di pressione subito, con l'auto dritta: dritto usi il 100% del grip per decelerare (appena giri, ne \"spendi\" una parte per la curva).",
      "Modula per stare appena sotto il bloccaggio.",
      "In ACC l'ABS interviene, ma spingere oltre la soglia con l'ABS attivo allunga comunque lo spazio e scalda i freni: l'ABS è una rete, non un muro.",
      "Rilascio progressivo avvicinandoti alla curva.",
    ],
    commonMistakes: [
      "Frenare mentre giri (blocchi o vai lungo).",
      "Rilascio \"a gradino\" invece che liscio.",
      "Usare l'ABS come muro.",
    ],
    video: { channel: "Driver61", title: "Maximising the Braking Phase", videoId: "TODO" },
  },
  {
    slug: "trail-braking",
    number: 4,
    title: "Trail braking",
    summary: "Continuare a frenare leggermente mentre giri in ingresso, per far ruotare l'auto.",
    whyItMatters:
      "Sposta carico sull'avantreno → più grip davanti in ingresso, l'auto ruota e apri l'uscita; puoi anche staccare un filo più tardi.",
    whenToUse:
      "Soprattutto curve lente/medie dove serve rotazione. NON in curve veloci (carichi troppo l'anteriore → instabilità, sovrasterzo improvviso).",
    howTo: [
      "Massima frenata dritto, poi al turn-in rilascia il freno progressivamente (spesso fino a un ~30–40% e giù) mentre aumenti lo sterzo.",
      "Rilascio liscio, \"come burro sul pane\"; freno a zero quando l'auto è girata e pronta ad accelerare.",
      "In telemetria: la traccia freno scende dolce sovrapposta allo sterzo che sale — è la firma del trail braking fatto bene.",
    ],
    commonMistakes: [
      "Tenere il freno troppo a lungo → sovrasterzo in ingresso.",
      "Rilascio a scatti.",
      "Farlo in curve veloci.",
      "Brake bias troppo arretrato (l'anteriore deve lavorare — se giri troppo, sposta il bias 1–2 click avanti).",
    ],
    video: { channel: "Driver61", title: "How to Trail Brake", videoId: "TODO" },
  },
  {
    slug: "trazione-in-uscita",
    number: 5,
    title: "Trazione in uscita (Throttle Application)",
    summary: "Aprire il gas in modo progressivo dall'apex all'uscita, srotolando lo sterzo.",
    whyItMatters:
      "La velocità di uscita si moltiplica su tutto il rettilineo. Pattinare = perdere trazione, scaldare le gomme e perdere tempo.",
    whenToUse: "Dall'apex in poi, in ogni curva.",
    howTo: [
      "All'apex ri-ingaggia il gas dolcemente per mantenere la velocità (non stai ancora accelerando).",
      "Man mano che raddrizzi lo sterzo, aumenta il gas fino al 100% quando l'auto è dritta.",
      "Più lunga l'uscita/il rettilineo, più questa fase pesa sul tempo.",
      "Gestisci il TC: se interviene di continuo, sei stato troppo brusco col gas.",
    ],
    commonMistakes: [
      "Gas troppo presto/troppo pieno con sterzo ancora girato → pattinamento e taglio del TC.",
      "\"Kick\" del gas invece di un'apertura liscia.",
    ],
    video: { channel: "Driver61", title: "The 6 Phases of a Corner (fasi 4–6)", videoId: "TODO" },
  },
  {
    slug: "gomme-finestra",
    number: 6,
    title: "Gomme: finestra pressioni e temperature",
    summary: "La gomma rende al massimo dentro una finestra di temperatura e pressione; fuori, perdi grip e consistenza.",
    whyItMatters:
      "È esattamente ciò che PitWall monitora. Pressione e temperatura giuste = grip e stint costante; fuori finestra = degrado e tempo perso.",
    whenToUse: "Sempre; leggere i dati a fine giro/stint.",
    howTo: [
      "Finestra pressioni operative (a CALDO): ~26.0–27.0 psi per tutte le classi GT (ACC v1.9, mescola dry DHF).",
      "Le pressioni che imposti in garage sono a FREDDO e più basse: salgono nei primi giri fino a entrare nella finestra a caldo. Regola le pressioni a freddo così che a caldo caschino in finestra.",
      "Temperatura di lavoro 70–100°C, ottimale 80–90°C. Tieni <15°C di spread tra interno ed esterno del battistrada (si gestisce con camber/toe e brake ducts).",
      "Regola pratica: ±0.1 psi ogni ±1°C di temperatura ambiente.",
    ],
    commonMistakes: [
      "Leggere le pressioni a freddo come se fossero operative.",
      "Gonfiare troppo (contatto ridotto, meno grip) o troppo poco (gomma fiacca, si scalda male).",
      "Ignorare lo spread di temperatura.",
    ],
    pitwallLink: {
      label: "Questa lezione è il \"perché\" dietro il cross-check gomme dell'app: guardala in Telemetria",
      href: "/telemetry",
    },
    video: { channel: "Coach Dave Academy", title: "How to Set the Correct Tyre Pressures in ACC", videoId: "TODO" },
  },
  {
    slug: "quali-vs-race",
    number: 7,
    title: "Quali vs Race",
    summary: "In qualifica cerchi il giro secco perfetto; in gara cerchi consistenza e gestione (gomme, carburante, traffico).",
    whyItMatters:
      "Sono due mentalità diverse. Guidare la gara come una qualifica distrugge gomme e carburante e ti fa sbagliare.",
    howTo: [
      "Qualifica: poco carburante (auto leggera), gomme portate in finestra sull'out-lap, massimo attacco per 1–2 giri, zero errori. Apex tardivo e trail braking rendono di più.",
      "Gara: guida a pochi decimi dal limite ma pulita e ripetibile; proteggi le gomme (meno scivolate, cordoli meno aggressivi); gestisci il carburante (→ LiCo); occhio a traffico e prima curva.",
      "La consistenza batte il singolo giro veloce.",
    ],
    commonMistakes: [
      "Attaccare al 100% ogni giro di gara (degrado + errori).",
      "In quali non scaldare le gomme sull'out-lap.",
      "Non ritarare i riferimenti col diverso carico di carburante (auto piena = frena prima).",
    ],
    video: { channel: "Coach Dave / Driver61", title: "Race pace e consistenza", videoId: "TODO" },
  },
  {
    slug: "lift-and-coast",
    number: 8,
    title: "LiCo (Lift & Coast)",
    summary: "Alzare il gas prima del punto di frenata e procedere in coasting per risparmiare carburante.",
    whyItMatters:
      "È il modo più efficiente di risparmiare carburante per tempo perso. Ti fa allungare lo stint di un giro o saltare un pit stop. Come effetto collaterale abbassa temperature freni e usura gomme.",
    whenToUse:
      "In gara/endurance quando devi centrare un target carburante; meglio nelle staccate pesanti a fine rettilineo verso curve lente. Mai in qualifica.",
    howTo: [
      "Invece di stare a gas pieno fino alla staccata, solleva il piede prima (da decine a centinaia di metri, in base a quanto devi risparmiare) e lascia rallentare l'auto; poi frena (più tardi/più leggero).",
      "Combinabile con lo short-shifting (cambiare marcia prima del solito).",
      "Riferimento reale (Coach Dave, LMU a Spa): ~1.5 L risparmiati/giro per ~0.7 s persi → su uno stint può valere un giro intero o un pit in meno.",
    ],
    commonMistakes: [
      "Sbagliare i riferimenti di frenata (arrivi più lento e vai lungo → vanno ritarati).",
      "Tenere il gas fino alla staccata (nessun risparmio).",
      "Usarlo in una zona di sorpasso con un avversario dietro.",
    ],
    pitwallLink: {
      label: "Si lega al calcolo strategia carburante dell'app: se il target dice \"−X L\", il LiCo è come lo ottieni in pista",
      href: "/console",
    },
    video: { channel: "Coach Dave Academy", title: "Mastering Lift and Coast", videoId: "TODO" },
  },
];

export function lessonBySlug(slug: string): Lesson | undefined {
  return LESSONS.find((l) => l.slug === slug);
}
