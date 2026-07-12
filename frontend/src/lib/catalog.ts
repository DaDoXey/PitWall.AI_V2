// Cataloghi UI per i selettori di sessione (Fase 7), portati da v1 (ui/catalog.py).
// Liste di presentazione: i range setup reali arrivano comunque da
// /api/setup-params (override per vettura nel DB JSON, fallback ai generici).

export const CAR_LIST = [
  "BMW M4 GT3",
  "Ferrari 296 GT3",
  "Ferrari 488 GT3 Evo",
  "Porsche 992 GT3 R",
  "Porsche 991 II GT3 R",
  "Mercedes-AMG GT3 Evo",
  "Audi R8 LMS Evo II GT3",
  "Lamborghini Huracán GT3 EVO2",
  "McLaren 720S GT3 Evo",
  "Bentley Continental GT3",
  "Honda NSX GT3 Evo",
  "Nissan GT-R Nismo GT3",
  "Lexus RC F GT3",
  "Ford Mustang GT3",
  "Aston Martin V8 Vantage GT3",
];

export const TRACK_LIST = [
  "Monza", "Spa-Francorchamps", "Nürburgring GP", "Silverstone",
  "Misano", "Barcelona", "Hungaroring", "Zandvoort", "Imola",
  "Kyalami", "Mount Panorama", "Suzuka", "Zolder",
  "Paul Ricard", "Brands Hatch",
];

export const CONDITIONS = ["Asciutto", "Umido", "Bagnato"];

// Default demo (coerenti con demo_data.SESSION lato backend).
export const DEFAULT_CAR = "BMW M4 GT3";
export const DEFAULT_TRACK = "Monza";
export const DEFAULT_CONDITIONS = "Asciutto";

// Capacità serbatoio BMW M4 GT3 in ACC (megaprompt #7, FASE 9): costante DEMO
// lato frontend — /api/session non la espone e demo_data.py (protetto) resta
// intatto. Usata SOLO per il "residuo stimato" (assunzione dichiarata in UI:
// serbatoio pieno al via). Un punto solo da cui correggere il valore.
export const DEMO_TANK_CAPACITY_L = 125;
