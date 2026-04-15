#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''writes the .inp file for the calpost'''

import importlib
import json
from datetime import datetime, timedelta
from pathlib import Path


class _FastAskCompat:
    @staticmethod
    def file_opener(path: str) -> str:
        return Path(path).read_text(encoding='utf-8')

    @staticmethod
    def sobstituter(text: str, token: str, value) -> str:
        return text.replace(token, str(value))

    @staticmethod
    def write_inp(path: str, content: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')


try:
    ff = importlib.import_module('pypack_day.functions.fastask')
except Exception:
    ff = _FastAskCompat()


# Placeholders
INQ = ['NOX','PM10']
FORMAT = 2 #1=.DAT 2=.CSV 3=.GRD 4=.ASC
UNITS_OUTPUT = 3 #conc_dep: 1=g/m3_g/m2/s, 2=mg/m3_mg/m2/s, 3=ug/m3_ug/m2/s, 4=ng/m3_ng/m2/s, 5=odor_-, 6=TBq/m3, 7=GBq/m3, 8=Bq/m3


def calpost_writer(calpuff_name: str, j: int, start_date: str, output_folder: str = 'CALPOST', species: list[str] = None, units_output: int = None, format_type: int = None) -> str:
    '''
    Scrive il file .inp per CALPOST per una specifica ora e periodo.
    - Genera sia il file standard (calpost.inp) sia un file con nome unico per output.
    Args:
        calpuff_name (str): nome del file di output CALPUFF da post-processare
        j (int): numero dell'ora (0-23, o superiore per più giorni)
        start_date (str): data di inizio simulazione in formato 'YYYYMMDD'
        output_folder (str): cartella di output per i file .inp generati
        species (list[str]): lista inquinanti da processare (da CALPUFF config)
        units_output (int): unità di output CALPOST
        format_type (int): formato output (default 2=CSV)
    Returns:
        str: nome del file di output LST generato
    '''
    # Calcola l'intervallo temporale di post-processing (ora corrente e ora successiva)
    start_date_b = datetime.strptime(start_date+ ' 00', '%Y%m%d %H')
    start_date = start_date_b + timedelta(hours=j)
    end_date = start_date_b + timedelta(hours=j+1) 
    star_wrf = start_date.strftime('%Y%m%d%H') # data/ora inizio
    end_wrf = end_date.strftime('%Y%m%d%H')   # data/ora fine

    # Estrae anno, mese, giorno, ora di inizio e fine
    year_s = star_wrf[:4]
    month_s = star_wrf[4:6]
    day_s = star_wrf[6:8]
    hour_s = star_wrf[8:]
    year_e = end_wrf[:4]
    month_e = end_wrf[4:6]
    day_e = end_wrf[6:8]
    hour_e = end_wrf[8:]
    print('start ', day_s, hour_s)
    print('end', day_e, hour_e )
    print('start_wrf', star_wrf)
    print()
    print()
    print()
    
    # Determina quali specie e unità usare
    if species is None:
        species = INQ
    if units_output is None:
        units_output = UNITS_OUTPUT
    if format_type is None:
        format_type = FORMAT
    
    # Apre il template del file di input CALPOST
    template_candidates = [
        Path('Working_Files') / 'calpost_try.txt',
        Path('Working_files') / 'calpost_try.txt',
        Path('pypack_day') / 'lib' / 'calpost_try.txt',
    ]
    template_path = next((candidate for candidate in template_candidates if candidate.exists()), None)
    if template_path is None:
        raise FileNotFoundError('Template CALPOST non trovato (calpost_try.txt)')
    
    file_calpost = ff.file_opener(str(template_path))
    filename = f'{output_folder}/calpost.inp'  # Nome file standard

    # Nome file di output LST per questa ora
    filename_output = f'CALPOST_{star_wrf[:]}.LST'
    # Sostituisce i parametri temporali e di input/output nel template
    file_calpost = ff.sobstituter(file_calpost, '[con_file_temp]', calpuff_name)
    file_calpost = ff.sobstituter(file_calpost, '[lst_out_temp]', filename_output)
    file_calpost = ff.sobstituter(file_calpost, '[year_start_temp]', year_s)
    file_calpost = ff.sobstituter(file_calpost, '[month_start_temp]', month_s)
    file_calpost = ff.sobstituter(file_calpost, '[day_start_temp]', day_s)
    file_calpost = ff.sobstituter(file_calpost, '[hour_start_temp]', hour_s)
    file_calpost = ff.sobstituter(file_calpost, '[year_end_temp]', year_e)
    file_calpost = ff.sobstituter(file_calpost, '[month_end_temp]', month_e)
    file_calpost = ff.sobstituter(file_calpost, '[day_end_temp]', day_e)
    file_calpost = ff.sobstituter(file_calpost, '[hour_end_temp]', hour_e)

    # Sostituisce i parametri relativi alle specie e al formato output
    file_calpost = ff.sobstituter(file_calpost, '[num_spec_temp]', len(species)) # Numero specie
    file_calpost = ff.sobstituter(file_calpost, '[format_temp]', format_type)

    num_ele = len(species)  # Numero di specie effettive

    # Costruisce le stringhe per le varie sezioni del file .inp
    spec_string = '  ,   '.join(species)    # Nomi specie
    layer_string = '  ,   '.join(['1']*num_ele)  # Layer di output (1 per tutti)
    units_string = '  ,   '.join([str(units_output)]*num_ele)  # Unità di output
    period_string =  '  ,   '.join(['T']*num_ele)  # Periodo (T per tutti)
    string_0 =  '  ,   '.join(['0']*num_ele)  # Zeri placeholder
    F_string =  '  ,   '.join(['F']*num_ele)  # Flag F
    minus_string =  '  ,   '.join(['-1.0']*num_ele)  # Placeholder -1.0

    # Inserisce le stringhe nel template
    file_calpost = ff.sobstituter(file_calpost, '[spec_string_temp]', spec_string)
    file_calpost = ff.sobstituter(file_calpost, '[layer_string_temp]', layer_string)
    file_calpost = ff.sobstituter(file_calpost, '[units_string_temp]', units_string)
    file_calpost = ff.sobstituter(file_calpost, '[period_string_temp]', period_string)
    file_calpost = ff.sobstituter(file_calpost, '[0_string_temp]', string_0)
    file_calpost = ff.sobstituter(file_calpost, '[F_string_temp]', F_string)
    file_calpost = ff.sobstituter(file_calpost, '[-1.0_string_temp]', minus_string)

    # Scrive il file .inp nella cartella CALPOST
    ff.write_inp(filename, file_calpost)
    return filename_output


def _read_json(path: Path) -> dict:
    """Legge un file JSON di configurazione."""
    if not path.exists():
        raise FileNotFoundError(f'File di configurazione non trovato: {path}')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _parse_date(date_str: str) -> datetime:
    """Converte una stringa data in oggetto datetime supportando più formati."""
    supported_formats = ('%d/%m/%Y', '%Y-%m-%d', '%Y%m%d', '%Y%m%d%H')
    for fmt in supported_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f'Formato data non supportato: {date_str}')


def generate_daily_calpost_files(
    calpuff_config_path: Path,
    temporal_config_path: Path,
    calmet_config_path: Path,
    output_dir: Path | None = None,
) -> list[Path]:
    """
    Genera un file .inp CALPOST per ogni giorno del periodo temporale.
    Legge le specie e le unità dalla configurazione CALPUFF, genera file per tutte le ore di ogni giorno.
    """
    calpuff_config = _read_json(Path(calpuff_config_path))
    temporal_config = _read_json(Path(temporal_config_path))
    calmet_config = _read_json(Path(calmet_config_path))

    # Estrae date dal temporal_config o calmet_config
    start_date_raw = temporal_config.get('start_date') or calmet_config.get('start_date')
    end_date_raw = temporal_config.get('end_date') or calmet_config.get('end_date')
    if not start_date_raw or not end_date_raw:
        raise ValueError('Date non trovate in temporal_config o calmet_config')

    start_date = _parse_date(start_date_raw)
    end_date = _parse_date(end_date_raw)
    if end_date < start_date:
        raise ValueError('La data finale è precedente alla data iniziale')

    # Determina la cartella di output
    resolved_output_dir = Path(output_dir) if output_dir else Path(calpuff_config_path).resolve().parent.parent / 'CALPOST_INP'
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    # Estrae gli inquinanti dalla configurazione CALPUFF
    species_dict = calpuff_config.get('species', {})
    if not species_dict:
        raise ValueError('Nessun inquinante trovato nella configurazione CALPUFF')
    species_list = list(species_dict.keys())

    # Mappa IPRTU da CALPUFF (o CALMET) a unità CALPOST
    units_output= calpuff_config.get('iprtu')

    # Nome base dei file di output CALPUFF (assumo siano generati con nome standard)
    calpuff_output_base = calpuff_config.get('calpuff_output', 'CALPUFFOUTPUT')

    created_files: list[Path] = []
    current_date = start_date

    # Loop per ogni giorno nel periodo
    while current_date <= end_date:
        day_token = current_date.strftime('%Y%m%d')
        
        # Nome file CALPUFF per questo giorno (deve corrispondere a quello generato da CALPUFF)
        calpuff_name = f'{calpuff_output_base}_{day_token}.CON'
        
        # Genera un file CALPOST per ogni ora del giorno (24 ore)
        for hour in range(24):
            if hour == 23:
                day_token_next = (current_date + timedelta(days=1)).strftime('%Y%m%d')
                calpuff_name = f'{calpuff_output_base}_{day_token_next}.CON'
            calpost_writer(
                calpuff_name=calpuff_name,
                j=hour,
                start_date=day_token,
                output_folder=str(resolved_output_dir),
                species=species_list,
                units_output=units_output,
                format_type=2  # Formato sempre 2 (CSV)
            )
            
            # Rinomina il file generato (calpost.inp) con nome univoco
            generated_file = resolved_output_dir / 'calpost.inp'
            if generated_file.exists():
                target_file = resolved_output_dir / f'calpost_{day_token}_{hour:02d}.inp'
                if target_file.exists():
                    target_file.unlink()
                generated_file.rename(target_file)
                created_files.append(target_file)

        current_date += timedelta(days=1)

    return created_files
