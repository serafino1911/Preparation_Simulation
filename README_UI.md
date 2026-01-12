# Configuratore UI per Simulazioni

Questo tool fornisce un'interfaccia grafica per configurare le procedure di simulazione.

## Installazione

```bash
pip install -r requirements_ui.txt
```

## Utilizzo

```bash
python ui_config_tool.py
```

## Funzionalità

### 1. Definisci Dominio
- Definisci il dominio geografico della simulazione selezionando 4 vertici
- Visualizza i vertici su una mappa interattiva (Folium)
- Modifica le coordinate manualmente nelle celle
- Imposta il passo della griglia in km o gradi
- Salva la configurazione in un file JSON temporaneo

### File di Output

Il dominio viene salvato in `temp_config/domain_config.json` con la seguente struttura:

```json
{
    "vertices": {
        "NW": {"lat": 45.5, "lon": 9.0},
        "NE": {"lat": 45.5, "lon": 9.5},
        "SE": {"lat": 45.0, "lon": 9.5},
        "SW": {"lat": 45.0, "lon": 9.0}
    },
    "grid_step": {
        "value": 1.0,
        "unit": "km"
    }
}
```

## Struttura dei File

- `ui_config_tool.py`: Applicazione principale con menu
- `domain_window.py`: Finestra per definire il dominio geografico
- `temp_config/`: Directory per i file di configurazione temporanei

## Sviluppi Futuri

- Aggiunta di ulteriori configurazioni (meteo, emissioni, etc.)
- Integrazione con le procedure esistenti
- Visualizzazione avanzata della griglia sulla mappa
