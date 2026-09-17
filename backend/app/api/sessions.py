"""api/sessions.py — importare e consultare le sessioni (L1 · Fase 4, L4 · Fasi 1-2).

Rotte:
- `POST /api/sessions/import/setup`   — un setup di ACC diventa una sessione
- `POST /api/sessions/import/results` — un file di risultati diventa una sessione
- `POST /api/sessions/manuale`        — una sessione scritta dal pilota (console: setup,
                                        tempi se li ha, racconto della guida)
- `POST /api/sessions/import/motec`   — un export MoTeC di ACC (.ld + .ldx) diventa una
                                        sessione con i canali (L5)
- `GET  /api/sessions/{id}/export/motec` — la sessione come .ld + .ldx (zip) per MoTeC i2 (L5)
- `GET  /api/sessions`                — elenco, dalla più recente (la DEMO in fondo)
- `GET  /api/sessions/{id}`           — il bundle intero
- `GET  /api/sessions/{id}/analisi`   — il report del motore (L2, + curve e gomme se ci sono i canali)
- `GET  /api/sessions/{id}/tracce`    — canali di alcuni giri, sulla distanza (per i grafici)
- `GET  /api/riferimenti/fisica`      — le soglie di gomme e freni: Kunos e community, separate
- `DELETE /api/sessions/{id}`         — rimuove una sessione (la DEMO no)

**La sessione DEMO** (`bundle/demo.py`) vive nello stesso archivio con un id fisso. Si
crea all'avvio, si ricrea se manca, non si cancella: è la sessione di chi non ne ha
ancora una sua, e la vetrina pubblica mostra solo lei.

**Presidio.** Queste rotte scrivono su disco e non toccano né la chiave né la rete,
quindi NON passano dal presidio della demo-mode (che serve a proteggere la
ANTHROPIC_API_KEY): bloccarle in demo le renderebbe inutilizzabili proprio dove
servono, sul PC del pilota, dove il live è spento. Hanno un interruttore loro,
`PITWALL_ALLOW_IMPORT` (default **acceso**): sul deploy pubblico va messo a 0, così
la vetrina non accetta file da nessuno.

**Più vetture nel file.** Un file di risultati contiene tutti i partecipanti. Se non
si dice quale sia la propria, la rotta risponde **409** con l'elenco (`partecipanti`)
invece di sceglierne una a caso: è il frontend a far scegliere, poi richiama con
`car_id`.
"""

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.analisi import analizza
from app.bundle import demo, store
from app.bundle.adapters import (
    ResultsAccError,
    canali_del_bundle,
    SetupAccError,
    elenca_partecipanti,
    leggi_results_acc,
    leggi_setup_acc,
)
from app.bundle.schema import (
    Fonte,
    Giro,
    Mescola,
    Meta,
    Piattaforma,
    Racconto,
    SessionBundle,
    Setup,
    TipoSessione,
    ValoreSetup,
)
from app.core import riferimenti_fisica

router = APIRouter()
log = logging.getLogger("pitwall.sessions")

# Un file di ACC sta in pochi KB: il tetto serve solo a non farsi riempire il disco.
MAX_BYTE = 20 * 1024 * 1024
# Un .ld di ACC pesa 2-6 MB a giro (verificato il 17/09): 200 MB sono uno stint lungo.
MAX_BYTE_MOTEC = 200 * 1024 * 1024


def _import_consentito() -> bool:
    return os.getenv("PITWALL_ALLOW_IMPORT", "1").strip().lower() not in ("0", "false", "no", "off")


def _presidio() -> None:
    if not _import_consentito():
        log.warning("503: import richiesto ma PITWALL_ALLOW_IMPORT e' spento")
        raise HTTPException(status_code=503,
                            detail="Import delle sessioni disattivato su questa installazione")


async def _leggi_upload(file: UploadFile, massimo: int = MAX_BYTE) -> bytes:
    raw = await file.read(massimo + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(raw) > massimo:
        raise HTTPException(status_code=413,
                            detail=f"File troppo grande (massimo {massimo // (1024 * 1024)} MB)")
    return raw


@router.post("/sessions/import/setup")
async def importa_setup(
    file: UploadFile = File(...),
    track: str | None = Form(default=None),
    nome: str | None = Form(default=None),
):
    """Legge un setup salvato in ACC e lo archivia come sessione."""
    _presidio()
    raw = await _leggi_upload(file)
    try:
        setup = leggi_setup_acc(raw, nome=nome or (file.filename or "").removesuffix(".json") or None)
    except SetupAccError as e:
        log.warning("400: setup non importabile (%d byte): %s", len(raw), e)
        raise HTTPException(status_code=400, detail=str(e))

    bundle = SessionBundle(
        meta=Meta(fonte=Fonte.ACC_SETUP, car=setup.car, track=track,
                  file_origine=file.filename),
        setup=setup,
    )
    id_sessione = store.salva(bundle)
    reali, totali = setup.quanti_verificati()
    log.info("setup importato: %s (%s, %d parametri, %d in unità reali)",
             id_sessione, setup.car, totali, reali)
    return {
        "id": id_sessione,
        "riassunto": store.riassunto(id_sessione),
        "assunzioni": setup.assunzioni,
        "parametri": totali,
        "parametri_in_unita_reali": reali,
    }


@router.post("/sessions/import/results")
async def importa_risultati(
    file: UploadFile = File(...),
    car_id: int | None = Form(default=None),
    player_id: str | None = Form(default=None),
    track: str | None = Form(default=None),
):
    """Legge un file di risultati di ACC e lo archivia come sessione."""
    _presidio()
    raw = await _leggi_upload(file)

    if car_id is None and player_id is None:
        try:
            partecipanti = elenca_partecipanti(raw)
        except ResultsAccError as e:
            log.warning("400: risultati non importabili (%d byte): %s", len(raw), e)
            raise HTTPException(status_code=400, detail=str(e))
        if len(partecipanti) > 1:
            log.info("409: %d vetture nel file, serve scegliere", len(partecipanti))
            raise HTTPException(
                status_code=409,
                detail={
                    "messaggio": "Il file contiene più vetture: indica quale è la tua.",
                    "partecipanti": [p.__dict__ for p in partecipanti],
                },
            )

    try:
        bundle = leggi_results_acc(raw, car_id=car_id, player_id=player_id, track=track)
    except ResultsAccError as e:
        log.warning("400: risultati non importabili (%d byte): %s", len(raw), e)
        raise HTTPException(status_code=400, detail=str(e))

    bundle.meta.file_origine = file.filename
    id_sessione = store.salva(bundle)
    log.info("risultati importati: %s (%d giri, %d validi)",
             id_sessione, len(bundle.giri), len(bundle.giri_validi))
    return {
        "id": id_sessione,
        "riassunto": store.riassunto(id_sessione),
        "assunzioni": bundle.assunzioni,
    }


class GiroManuale(BaseModel):
    numero: int = Field(ge=1)
    tempo_ms: int | None = Field(default=None, gt=0)
    splits_ms: list[int] = Field(default_factory=list, max_length=3)
    valido: bool = True


class SessioneManuale(BaseModel):
    """Una sessione raccontata dal pilota: il percorso di chi gioca su console.

    Funziona esattamente come le altre (stesso bundle, stesso motore, stesse
    schermate): semplicemente contiene meno misure, e il report lo dice.
    """

    piattaforma: Piattaforma
    car: str | None = None
    track: str | None = None
    tipo_sessione: TipoSessione = TipoSessione.PROVE
    mescola: Mescola | None = None
    temp_aria_c: float | None = Field(default=None, ge=-20, le=60)
    temp_pista_c: float | None = Field(default=None, ge=-20, le=90)
    giri: list[GiroManuale] = Field(default_factory=list, max_length=200)
    setup: dict[str, float] = Field(default_factory=dict)
    racconto: Racconto | None = None


def _leggi_o_errore(id_sessione: str) -> SessionBundle:
    if demo.e_demo(id_sessione):
        demo.assicura_demo()
    try:
        return store.leggi(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/manuale")
async def crea_sessione_manuale(corpo: SessioneManuale):
    """Una sessione scritta a mano: setup, tempi (se ci sono) e racconto della guida."""
    _presidio()
    racconto = corpo.racconto if corpo.racconto and not corpo.racconto.vuoto() else None
    setup = None
    if corpo.setup:
        # Valori così come li ha scritti il pilota, dalla pagina Setup: si conservano
        # grezzi e non verificati (decisione 7 del rework), come quelli dei file.
        setup = Setup(car=corpo.car, nome="Setup inserito a mano",
                      valori={k: ValoreSetup(raw=v) for k, v in corpo.setup.items()},
                      raw=dict(corpo.setup),
                      assunzioni=["setup inserito a mano: valori non letti da un file di ACC"])
    bundle = SessionBundle(
        meta=Meta(
            fonte=Fonte.MANUALE, car=corpo.car, track=corpo.track,
            tipo_sessione=corpo.tipo_sessione, mescola=corpo.mescola,
            piattaforma=corpo.piattaforma,
            condizioni={"temp_aria_c": corpo.temp_aria_c, "temp_pista_c": corpo.temp_pista_c},
        ),
        giri=[Giro(**g.model_dump()) for g in corpo.giri],
        setup=setup,
        racconto=racconto,
        assunzioni=["sessione inserita a mano dal pilota: tempi e setup non letti dal gioco"],
    )
    if not bundle.ha_dati_utili():
        raise HTTPException(status_code=400,
                            detail="Servono almeno i tempi, il setup o il racconto della sessione")
    id_sessione = store.salva(bundle)
    log.info("sessione manuale creata: %s (%s, %d giri, setup %s, racconto %s)",
             id_sessione, corpo.piattaforma.value, len(bundle.giri),
             "sì" if setup else "no", "sì" if racconto else "no")
    return {"id": id_sessione, "riassunto": store.riassunto(id_sessione)}


@router.post("/sessions/import/motec")
async def importa_motec(
    ld: UploadFile = File(...),
    ldx: UploadFile | None = File(default=None),
    setup: UploadFile | None = File(default=None),
    carburante_inizio_l: float | None = Form(default=None, ge=0, le=150),
    carburante_fine_l: float | None = Form(default=None, ge=0, le=150),
    mescola: Mescola | None = Form(default=None),
    riferimento: bool = Form(default=True),
):
    """Un export MoTeC di ACC diventa una sessione con i canali (L5 · Fase 2).

    Il `.ldx` porta i passaggi sul traguardo: senza, i giri non si conoscono (salvo i
    file ritagliati in MoTeC i2, che valgono un giro se la distanza è quella della
    pista). Il setup, se c'è, porta mescola e consumo dichiarato; i litri a inizio e
    fine, se ci sono, valgono più del setup.
    """
    import shutil

    from app.bundle.adapters.motec import (
        CarburanteManuale,
        MotecNonConvertibile,
        bundle_da_motec,
        salva_registrazione,
    )
    from app.motec import FileMotecNonValido, LdxNonValido, registrazione_da_byte
    from app.telemetria import registratore

    _presidio()
    nome_ld = ld.filename or "sessione.ld"
    if not nome_ld.lower().endswith(".ld"):
        raise HTTPException(status_code=400, detail="Il primo file deve essere un .ld di MoTeC")
    if ldx is not None and not (ldx.filename or "").lower().endswith(".ldx"):
        raise HTTPException(status_code=400, detail="Il file dei giri deve essere un .ldx")
    if (carburante_inizio_l is None) != (carburante_fine_l is None):
        raise HTTPException(status_code=400,
                            detail="Per il consumo servono i litri a inizio E a fine sessione")

    raw_ld = await _leggi_upload(ld, MAX_BYTE_MOTEC)
    raw_ldx = await _leggi_upload(ldx) if ldx is not None else None
    try:
        registrazione = registrazione_da_byte(raw_ld, raw_ldx, nome_ld)
    except (FileMotecNonValido, LdxNonValido) as e:
        log.warning("400: MoTeC non leggibile (%s, %d byte): %s", nome_ld, len(raw_ld), e)
        raise HTTPException(status_code=400, detail=str(e))

    setup_letto = None
    if setup is not None:
        raw_setup = await _leggi_upload(setup)
        try:
            setup_letto = leggi_setup_acc(
                raw_setup, nome=(setup.filename or "").removesuffix(".json") or None)
        except SetupAccError as e:
            raise HTTPException(status_code=400, detail=f"setup: {e}")

    carburante = (CarburanteManuale(carburante_inizio_l, carburante_fine_l)
                  if carburante_inizio_l is not None else None)
    try:
        bundle, canali, metadati = bundle_da_motec(
            registrazione, setup=setup_letto, carburante=carburante, mescola=mescola,
            riferimento=riferimento, nome_file=nome_ld)
    except MotecNonConvertibile as e:
        log.warning("422: MoTeC non convertibile (%s): %s", nome_ld, e)
        raise HTTPException(status_code=422, detail=str(e))

    id_registrazione = registratore.nuovo_id(bundle.meta.car, bundle.meta.track)
    cartella = registratore.cartella_telemetria() / id_registrazione
    bundle.canali.file = f"{id_registrazione}/canali.npz"
    metadati["id"] = id_registrazione
    metadati["file_origine"] = nome_ld
    try:
        salva_registrazione(cartella, canali, metadati)
        id_sessione = store.salva(bundle)
    except Exception:
        shutil.rmtree(cartella, ignore_errors=True)   # niente canali orfani su disco
        raise
    log.info("MoTeC importato: %s (%s, %s, %d giri, riferimento=%s, carburante=%s)",
             id_sessione, bundle.meta.car, bundle.meta.track, len(bundle.giri),
             riferimento, bundle.carburante_fonte.value if bundle.carburante_fonte else "—")
    return {
        "id": id_sessione,
        "id_registrazione": id_registrazione,
        "riassunto": store.riassunto(id_sessione),
        "giri": len(bundle.giri),
        "giri_con_tempo": len([g for g in bundle.giri if g.tempo_ms]),
        "assunzioni": bundle.assunzioni,
    }


@router.get("/sessions/{id_sessione}/export/motec")
async def esporta_motec(id_sessione: str):
    """La sessione come coppia `.ld` + `.ldx`, in uno zip, da aprire in MoTeC i2 (L5 · F5).

    Solo lettura: non scrive niente sul disco del server. Funziona per ogni sessione con i
    canali (registrazioni, demo, import MoTeC); senza canali risponde 409.
    """
    from fastapi.responses import Response

    from app.motec.esporta import EsportazioneImpossibile, esporta

    bundle = _leggi_o_errore(id_sessione)
    canali = canali_del_bundle(bundle)
    if not canali:
        raise HTTPException(status_code=409,
                            detail="Questa sessione non ha canali: niente da esportare per MoTeC")
    try:
        esportazione = esporta(bundle, canali)
    except EsportazioneImpossibile as e:
        raise HTTPException(status_code=422, detail=str(e))
    log.info("export MoTeC: %s → %s (%d canali, %d byte)", id_sessione,
             esportazione.nome_base, len(esportazione.canali), len(esportazione.ld))
    return Response(
        content=esportazione.zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{esportazione.nome_base}.zip"'},
    )


@router.get("/sessions")
async def elenco_sessioni(limite: int = 50):
    limite = max(1, min(limite, 200))
    demo.assicura_demo()
    return {"sessioni": store.elenca(limite), "demo_id": demo.DEMO_ID}


@router.get("/riferimenti/fisica")
async def riferimenti():
    """Le soglie di gomme e freni, divise per affidabilità (Kunos | community)."""
    return riferimenti_fisica.come_json()


@router.get("/sessions/{id_sessione}")
async def leggi_sessione(id_sessione: str):
    return _leggi_o_errore(id_sessione)


@router.get("/sessions/{id_sessione}/analisi")
async def analisi_sessione(id_sessione: str):
    """Il report deterministico della sessione: nessuna rete, nessun modello, zero spesa."""
    bundle = _leggi_o_errore(id_sessione)
    # Se la sessione viene da una registrazione, i suoi canali sono ancora sul disco:
    # il report cresce (curve, gomme, freni) invece di restare quello dei soli tempi.
    canali = canali_del_bundle(bundle)
    report = analizza(bundle, canali)
    log.info("analisi di %s: %d giri, %d voci nel verdetto%s",
             id_sessione, report.giri_totali, len(report.verdetto),
             " (con canali)" if canali else "")
    return report


# Canali che si possono chiedere per i grafici: quelli che una schermata disegna
# davvero sulla distanza. Una lista chiusa, così una richiesta non trascina fuori
# 200 colonne per sbaglio.
CANALI_TRACCE = (
    "physics.speedKmh", "physics.brake", "physics.gas", "physics.steerAngle", "physics.gear",
    # il tempo sulla distanza: serve al delta fra due giri, anche di sessioni diverse (L5)
    "pitwall.tempo_ms",
)


@router.get("/sessions/{id_sessione}/tracce")
async def tracce_sessione(
    id_sessione: str,
    giri: str = Query(..., description="numeri dei giri separati da virgola (max 4)"),
    canali: str = Query(default="physics.speedKmh,physics.brake,physics.gas"),
    punti: int = Query(default=800, ge=100, le=2000),
):
    """I canali di alcuni giri ricampionati sulla **stessa griglia di posizione**.

    È ciò che serve per sovrapporre due giri curva per curva: nel tempo scivolerebbero,
    sulla distanza no. La posizione è in quota di giro (0-1) e, se la lunghezza del
    tracciato si stima, anche in metri.
    """
    from app.analisi.curve import (
        CurveNonCalcolabili,
        dividi_in_giri,
        griglia,
        lunghezza_stimata,
        su_distanza,
    )

    bundle = _leggi_o_errore(id_sessione)
    serie = canali_del_bundle(bundle)
    if not serie:
        raise HTTPException(status_code=409,
                            detail="Questa sessione non ha canali: niente tracce da disegnare")
    try:
        numeri = [int(n) for n in giri.split(",") if n.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="giri: numeri separati da virgola")
    if not numeri or len(numeri) > 4:
        raise HTTPException(status_code=400, detail="giri: da 1 a 4")
    nomi = [n.strip() for n in canali.split(",") if n.strip()]
    sconosciuti = [n for n in nomi if n not in CANALI_TRACCE]
    if sconosciuti or not nomi:
        raise HTTPException(status_code=400,
                            detail=f"canali ammessi: {', '.join(CANALI_TRACCE)}")

    per_numero = {g.numero: g for g in dividi_in_giri(serie)}
    fuori = []
    lunghezza = None
    for numero in numeri:
        giro = per_numero.get(numero)
        if giro is None or not giro.completo:
            raise HTTPException(status_code=404, detail=f"giro {numero} assente o incompleto")
        try:
            profilo = su_distanza(serie, giro, nomi + ["physics.speedKmh"], punti)
        except CurveNonCalcolabili as e:
            raise HTTPException(status_code=422, detail=str(e))
        if lunghezza is None:
            lunghezza = lunghezza_stimata(profilo, giro.tempo_ms)
        fuori.append({
            "giro": numero,
            "tempo_ms": giro.tempo_ms,
            "canali": {n: [round(float(v), 3) for v in profilo[n]] for n in nomi if n in profilo},
        })
    posizioni = griglia(punti)
    return {
        "id": id_sessione,
        "punti": punti,
        "posizione": [round(float(p), 5) for p in posizioni],
        "metri": ([round(float(p) * lunghezza, 1) for p in posizioni] if lunghezza else None),
        "lunghezza_stimata_m": round(lunghezza, 1) if lunghezza else None,
        "giri": fuori,
    }


@router.delete("/sessions/{id_sessione}")
async def cancella_sessione(id_sessione: str):
    if demo.e_demo(id_sessione):
        raise HTTPException(status_code=403, detail="La sessione demo non si cancella")
    try:
        bundle = store.leggi(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        store.cancella(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # I canali di un import MoTeC sono una conversione del file del pilota, non una
    # registrazione originale: se ne vanno con la sessione. (Le registrazioni della
    # shared memory hanno la loro rotta di cancellazione e restano.)
    if bundle.meta.fonte == Fonte.MOTEC and bundle.canali is not None:
        import shutil

        from app.telemetria.registratore import cartella_telemetria

        radice = cartella_telemetria().resolve()
        cartella_canali = (radice / bundle.canali.file).parent.resolve()
        if cartella_canali.parent == radice and cartella_canali.is_dir():
            shutil.rmtree(cartella_canali, ignore_errors=True)
    log.info("sessione cancellata: %s", id_sessione)
    return {"cancellata": id_sessione}
