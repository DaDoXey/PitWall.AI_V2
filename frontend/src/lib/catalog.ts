// Cataloghi UI per i selettori, portati da v1 (ui/catalog.py).
// Liste di presentazione: i range setup reali arrivano comunque da
// /api/setup-params (override per vettura nel DB JSON, fallback ai generici).
//
// ⚠️ NON sono la fonte: dal Lotto 1 il catalogo completo (31 vetture GT3,
// 25 circuiti) arriva da `GET /api/catalog` (backend `core/catalog.py`) via
// `getCatalog()`. Queste liste restano come **fallback** se il backend non
// risponde, così i selettori non si svuotano mai. Il backend risolve
// indifferentemente slug o nomi di display.

export const CAR_LIST_FALLBACK = [
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

export const TRACK_LIST_FALLBACK = [
  "Monza", "Spa-Francorchamps", "Nürburgring GP", "Silverstone",
  "Misano", "Barcelona", "Hungaroring", "Zandvoort", "Imola",
  "Kyalami", "Mount Panorama", "Suzuka", "Zolder",
  "Paul Ricard", "Brands Hatch",
];

// Default dei selettori quando non c'è una sessione da cui leggerli: la vettura e la
// pista della sessione DEMO.
export const DEFAULT_CAR = "BMW M4 GT3";
export const DEFAULT_TRACK = "Monza";
