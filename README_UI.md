# Configuratore UI per Simulazioni

Interfaccia grafica per preparare configurazioni, generare file INP e avviare operazioni su Farm per workflow CALMET/CALPUFF/CALPOST.

## Scopo

La UI permette di:

- definire dominio, orografia e periodo temporale;
- configurare CALMET e CALPUFF (incluse sorgenti, specie e scaling);
- salvare/caricare snapshot completi della configurazione;
- generare automaticamente i file INP necessari;
- eseguire operazioni su Farm (prepare/upload/launch) in modo guidato.

## Installazione

```bash
pip install -r requirements_ui.txt
```

## Avvio

### Avvio standard

```bash
python ui_config_tool.py
```

### Avvio consigliato su Windows con percorso workspace contenente spazi

```powershell
& ".\.venv\Scripts\python.exe" "ui_config_tool.py"
```

## Flusso operativo consigliato

Ordine consigliato in UI:

1. Definisci Dominio
2. Orografia e Uso Terreno
3. Dominio Temporale
4. Configura CALMET
5. Configura CALPUFF
6. Configurazione Farm
7. Operazioni sul Farm

Azioni globali disponibili nella finestra principale:

- Salva Configurazione: copia tutti i JSON correnti in `saved_configurations/<nome>_<timestamp>/`.
- Carica Configurazione: ripristina i JSON selezionati in `temp_config/`.
- Clear Simulazione: svuota `temp_config/`, `Outputs/` e tutte le cartelle `*_INP`.

## Finestra principale e sotto-app

### Finestra principale

La finestra iniziale (`ui_config_tool.py`) espone i pulsanti:

- Definisci Dominio
- Orografia e Uso Terreno
- Dominio Temporale
- Configura CALMET
- Configura CALPUFF
- Configurazione Farm
- Operazioni sul Farm
- Salva Configurazione
- Carica Configurazione
- Clear Simulazione

### Percorso finestre in ordine

1. Definisci Dominio
    - prima finestra da compilare;
    - imposta geometria dominio e griglia di riferimento.

2. Orografia e Uso Terreno
    - usa i parametri del dominio;
    - prepara i dati territoriali necessari ai passaggi successivi.

3. Dominio Temporale
    - definisce inizio/fine periodo simulato;
    - intervallo usato per generare i file giornalieri/orari.

4. Configura CALMET
    - usa dominio + periodo temporale;
    - salva i parametri CALMET e puo generare INP CALMET.

5. Configura CALPUFF (hub emissioni)
    - apre la configurazione principale CALPUFF;
    - richiama le sotto-app:
      - Species
      - Point Sources
      - Area Sources
      - Volume Sources
      - Flare Sources
      - Road Sources
      - Line Sources
      - Scaling Factors
    - le sotto-app lavorano principalmente su `temp_config/calpuff_config.json`.

        Parametri principali usati nella configurazione CALPUFF non in una sotto sezione:

 
        |---|---|
        | **IOUTU** | Unita usate nei file binari di output di CALPUFF per concentrazioni e deposizioni. Tipicamente: 1 = massa (g/m^3), 2 = odore, 3 = radioattivita (Bq/m^3). |
        | **IPRTU** | Unita usate da CALPOST per stampare i risultati. 1 = g/m^3, 2 = mg/m^3, 3 = ug/m^3, 4 = ng/m^3, 5 = unita odorimetriche. |
        | **IPTU** | Unita delle emissioni delle sorgenti puntuali (camini). 1 = g/s, 2 = kg/h, 3 = lb/h, 4 = ton/anno, 7 = tonnellate metriche/anno. |
        | **IARU** | Unita delle emissioni delle sorgenti areali. 1 = g/m^2/s, 2 = kg/m^2/h, 3 = lb/m^2/h, 4 = ton/m^2/anno. |
        | **IVLU** | Unita delle emissioni delle sorgenti volumetriche. Stesse opzioni di IPTU: g/s, kg/h, ton/anno, ecc. |

6. Configurazione Farm
    - imposta endpoint/utenze/working folder remoti.

7. Operazioni sul Farm
    - esegue prepare, upload INP e launch job;
    - da qui si possono aprire anche Meteo e configurazione puntuale.

### Chi chiama cosa (come e quando)

| Caller | Trigger (quando) | Chiamata (come) | Finestra aperta |
|---|---|---|---|
| `ui_config_tool.py` (main window) | click pulsante in home | istanziazione diretta classe finestra | Domain, Orography, Temporal, CALMET, CALPUFF, Farm, Farm Operations |
| `CalpuffWindow` | click sui pulsanti di configurazione interna | import locale + istanziazione finestra figlia | Species, Point, Area, Volume, Flare, Road, Line, Scaling |
| `FarmOperationsWindow` | click su azione meteo | import locale + istanziazione | MeteoWindow |
| `MeteoWindow` | click su configurazione estrazione puntuale | `ConfigPuntualeWindow.show_dialog(...)` | dialog Config Puntuale |
| `FarmOperationsWindow` | click su azione puntuale/post-process | `ConfigPuntualeWindow.show_dialog(...)` | dialog Config Puntuale |

In pratica: la home apre i moduli principali, CALPUFF apre le sotto-app emissioni/specie/scaling, e Farm Operations puo aprire Meteo e la configurazione puntuale.

## Cosa salva ogni sezione

| Sezione UI | File principali letti | File principali scritti | Effetto pratico |
|---|---|---|---|
| Definisci Dominio | `temp_config/domain_config.json` (se presente) | `temp_config/domain_config.json` | Definisce vertici, griglia e riferimenti dominio usati da tutte le altre sezioni |
| Orografia e Uso Terreno | `temp_config/domain_config.json` | `temp_config/orography_config.json`, `temp_config/landuse_config.json` | Prepara dati orografici/uso suolo e file in `Outputs/` |
| Dominio Temporale | `temp_config/temporal_config.json` (se presente) | `temp_config/temporal_config.json` | Imposta intervallo date per generazione INP |
| Configura CALMET | `domain_config.json`, `temporal_config.json`, `calmet_config.json` | `temp_config/calmet_config.json` | Salva parametri CALMET e puo generare i file in `CALMET_INP/` |
| Configura CALPUFF | `temp_config/calpuff_config.json` | `temp_config/calpuff_config.json` | Salva configurazione base CALPUFF + componenti emissioni/specie/scaling; puo generare `CALPUFF_INP/` e `CALPOST_INP/` |
| Configurazione Farm | `temp_config/farm_config.json` (se presente) | `temp_config/farm_config.json` | Salva endpoint e parametri di connessione/working folder |
| Operazioni sul Farm | `farm_config.json` + altri JSON di configurazione | `temp_config/post_process.json` (in base alle operazioni) | Esegue prepare/upload/launch remoti e orchestration job |
| Meteo (richiamabile da Farm Ops) | `domain_config.json`, `temporal_config.json`, `calmet_config.json` | `temp_config/meteo_config.json` | Configura e lancia operazioni meteo |
| Config puntuale (richiamabile da Meteo/Farm Ops) | `domain_config.json`, `post_process.json` (se presente) | `temp_config/post_process.json` | Definisce punti di estrazione e opzioni post-process |

Database persistenti delle sorgenti/specie (riutilizzabili) sono in `saved_configurations/`:

- `species_database.json`
- `point_sources_database.json`
- `area_sources_database.json`
- `volume_sources_database.json`
- `line_sources_database.json`
- `road_sources_database.json`

## File generati e cartelle

### Configurazioni runtime

- `temp_config/`: stato corrente della configurazione (JSON usati dalla UI)
- `saved_configurations/`: snapshot salvati con metadata e database sorgenti/specie

### INP generati

- `CALMET_INP/`
    - `calmet_YYYYMMDD.inp` (uno per giorno)
- `CALPUFF_INP/`
    - `calpuff_YYYYMMDD.inp` (uno per giorno)
- `CALPOST_INP/`
    - `calpost_YYYYMMDD_HH.inp` (24 per giorno)

### File geografici/utility

- `Outputs/`
    - contiene file intermedi/risultato preparati dalla sezione orografia e step geografici
- file INP geografici creati dalle operazioni Farm:
    - `terrel.inp`
    - `ctgproc.inp`
    - `makegeo.inp`

## Workflow Farm (sintetico)

Prerequisiti minimi prima delle operazioni remote:

- `temp_config/farm_config.json` compilato;
- configurazioni locali coerenti (`domain_config.json`, `temporal_config.json`, `calmet_config.json`, `calpuff_config.json`, piu file specifici richiesti dall'operazione);
- template script presenti in `Working_Files/scripts/`.

Sequenza tipica:

1. Prepare cartelle remote
2. Upload file INP locali
3. Launch job (tipicamente in background via `bsub -q pmten`)

La finestra Operazioni sul Farm gestisce anche azioni di meteo e post-process; i log di esecuzione vengono riportati nella UI e nei file di log lato working folder remoto (in base allo script/command lanciato).

## Sezione Meteo: cosa fa

La parte Meteo serve a preparare e lanciare le operazioni meteorologiche che alimentano la catena CALMET/CALPUFF.

In pratica permette di:

- leggere il contesto di simulazione da dominio, periodo e configurazione CALMET;
- salvare i parametri meteo in `temp_config/meteo_config.json`;
- preparare i file INP meteo necessari al run;
- avviare il job meteo su Farm (anche in background via `bsub -q pmten`);
- aprire la configurazione puntuale per definire punti griglia/estrazione da usare nel post-process.

### Input richiesti dalla sezione Meteo

- `temp_config/domain_config.json`
- `temp_config/temporal_config.json`
- `temp_config/calmet_config.json`
- `temp_config/farm_config.json` (se si lancia su Farm)

### Output e stato salvato

- `temp_config/meteo_config.json`: stato completo della configurazione meteo.
- `temp_config/post_process.json`: viene aggiornato quando si usa la configurazione puntuale.
- log operativi in UI e, lato Farm, nei log dei job/script lanciati.

### Quando usarla nel flusso

Usala dopo aver completato almeno:

1. Definizione dominio
2. Dominio temporale
3. Configurazione CALMET

Così eviti errori dovuti a configurazioni mancanti o incoerenti.

## Errori comuni e recovery rapido

### 1) Configurazioni mancanti

Sintomo: errore in creazione INP o in operazioni Farm su file JSON non trovato.

Recovery:

1. completa prima i passi precedenti del flusso consigliato;
2. verifica presenza file in `temp_config/`;
3. se necessario usa Carica Configurazione.

### 2) Date non valide o intervallo invertito

Sintomo: errore parsing data o end date precedente a start date.

Recovery:

1. correggi in Dominio Temporale;
2. usa formati data supportati dalla toolchain (es. `YYYY-MM-DD`).

### 3) Template mancanti

Sintomo: errore su template `*_try.txt` o script `.sh.template` non trovato.

Recovery:

1. verifica i file in `Working_Files/` e `Working_Files/scripts/`;
2. ripristina i template mancanti prima di rilanciare.

### 4) Credenziali Farm incomplete

Sintomo: connessione SSH fallita o job non sottomesso.

Recovery:

1. ricontrolla `Configurazione Farm`;
2. verifica jump server, target server, utente e working folder;
3. rilancia da Operazioni sul Farm.

## Note operative

- Il pulsante in UI e etichettato come `Clear Simulazion` (refuso nel testo), ma la funzione esegue la pulizia delle aree temporanee.
- Le password Farm non vengono tipicamente persistite integralmente nei file di configurazione per motivi di sicurezza.

