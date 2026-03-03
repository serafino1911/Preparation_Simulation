#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''writes the .inp file for the calmet'''

from datetime import datetime, timedelta
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as file_handle:
        return json.load(file_handle)


def _parse_date(date_value: str) -> datetime:
    supported_formats = ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y')
    for date_format in supported_formats:
        try:
            return datetime.strptime(date_value.strip(), date_format)
        except ValueError:
            continue
    raise ValueError(f"Formato data non supportato: {date_value}")


def _normalize_zone(zone_value: str) -> tuple[str, str]:
    raw_value = (zone_value or '').strip().upper().replace(' ', '')
    if not raw_value:
        return '32', 'N'

    index = 0
    while index < len(raw_value) and raw_value[index].isdigit():
        index += 1

    zone_num = raw_value[:index] or '32'
    zone_dir = raw_value[index:index + 1] or 'N'
    return zone_num, zone_dir


def generate_daily_inp_files(
    calmet_config_path: Path,
    temporal_config_path: Path,
    domain_config_path: Path,
    landuse_config_path: Path,
    output_dir: Path | None = None,
    template_path: Path | None = None,
) -> list[Path]:
    """Genera un file .inp CALMET per ogni giorno del periodo in temporal_config."""
    calmet_config = _read_json(Path(calmet_config_path))
    temporal_config = _read_json(Path(temporal_config_path))
    domain_config = _read_json(Path(domain_config_path))
    landuse_config = _read_json(Path(landuse_config_path))

    start_date_raw = temporal_config.get('start_date') or calmet_config.get('start_date')
    end_date_raw = temporal_config.get('end_date') or calmet_config.get('end_date')

    if not start_date_raw or not end_date_raw:
        raise ValueError('Date non trovate in temporal_config o calmet_config')

    start_date = _parse_date(start_date_raw)
    end_date = _parse_date(end_date_raw)
    if end_date < start_date:
        raise ValueError('La data finale è precedente alla data iniziale')

    workspace_root = Path(calmet_config_path).resolve().parent.parent
    resolved_output_dir = Path(output_dir) if output_dir else workspace_root / 'CALMET_INP'
    resolved_template_path = Path(template_path) if template_path else workspace_root / 'Working_Files' / 'calmet_try.txt'

    if not resolved_template_path.exists():
        raise FileNotFoundError(f'Template non trovato: {resolved_template_path}')

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    template_text = resolved_template_path.read_text(encoding='utf-8')

    zone_from_calmet = calmet_config.get('zone')
    zone_from_domain = domain_config.get('zona_utm')
    zone_from_landuse = landuse_config.get('zona_utm')
    zone_num, zone_dir = _normalize_zone(zone_from_calmet or zone_from_domain or zone_from_landuse)

    geo_dat = calmet_config.get('calmet_output', 'Auto')
    if not geo_dat or str(geo_dat).strip().lower() == 'auto':
        geo_dat = 'makegeo.dat'
    
    base_replacements = {
        '[geo_dat]': str(geo_dat),
        '[projection]': str(calmet_config.get('proj', 'UTM') or 'UTM'),
        '[zone_num]': zone_num,
        '[zone_dir]': zone_dir,
        '[or_lat]': str(calmet_config.get('origin_lat', '44.404709N') or '44.404709N'),
        '[or_lon]': str(calmet_config.get('origin_lon', '8.868261E') or '8.868261E'),
        '[x_lat1]': str(calmet_config.get('mach_lat1', '40.00N') or '40.00N'),
        '[x_lat2]': str(calmet_config.get('mach_lat2', '40.01N') or '40.01N'),
        '[x_grid]': str(calmet_config.get('nx', 250)),
        '[y_grid]': str(calmet_config.get('ny', 185)),
        '[delta]': str(calmet_config.get('dim', 0.081)),
        '[x_or]': str(calmet_config.get('xori', 479.385)),
        '[y_or]': str(calmet_config.get('yori', 4909.341)),
        '[z_grid]': str(calmet_config.get('nz', 10)),
        '[z_grid_face]': str(calmet_config.get('zface', '0.,20.,40.,80.,160.,300.,600.,1000.,1500.,2200.,3000.')),
        '[num_wrf_files_temp]': '24',
    }
    metdata = calmet_config.get('calmet_data', 'CALMETDATA') or 'CALMETDATA'
    created_files = []
    current_date = start_date
    while current_date <= end_date:
        file_content = template_text
        date_c = current_date.strftime('%Y%m%d')
        date_replacements = {
            '[year_temp]': current_date.strftime('%Y'),
            '[month_temp]': current_date.strftime('%m'),
            '[day_temp]': current_date.strftime('%d'),
            '[hour_temp]': '00',
            '[srfdat_temp]': f'wrf_{date_c}_all.m2d',
            '[m3ddat_temp]': f'wrf_{date_c}_all.m3d',
            '[metdat_temp]': f'{metdata}_{date_c}.dat',
        }
        all_replacements = {**base_replacements, **date_replacements}

        for placeholder, value in all_replacements.items():
            file_content = file_content.replace(placeholder, value)

        output_file = resolved_output_dir / f"calmet_{current_date.strftime('%Y%m%d')}.inp"
        output_file.write_text(file_content, encoding='utf-8')
        created_files.append(output_file)
        current_date += timedelta(days=1)

    return created_files

def calmet_writer(calmet_data_list : list, date_in : str, number_of_days : int, calmet_folder : str = 'CALMET') -> None:
    '''writes the .inp file for the calmet
    Args:
        wrf_path (str) : path where tht wrf file are
        calmet_data_list (List[str]) : a list with only three element, the name of the .m3d  and .m2d output of the calwrf and the name of the .dat output of thre calmet
    Returns:
        None
    '''
    try:
        import pypack_day.functions.fastask as ff
        import pypack_day.functions.wrf_date as wrf_date
        from pypack_day.configuration.config_met import HOUR_SIM, MAKEDAT
        from pypack_day.configuration.config_makegeo import GEODAT
        from pypack_day.configuration.general_configuration import (
            PROJ,
            ZONE,
            ORIGIN_LAT,
            ORIGIN_LON,
            MACH_LAT1,
            MACH_LAT2,
            NX,
            NY,
            DIM,
            XORI,
            YORI,
            NZ,
            ZFACE,
        )
    except ModuleNotFoundError as import_error:
        raise ModuleNotFoundError(
            'Dipendenze legacy pypack_day non disponibili per calmet_writer'
        ) from import_error

    num_files = number_of_days * HOUR_SIM
    star_wrf, end_wrf = wrf_date.wrf_start_end_choosen(date_in, number_of_days)
    year = star_wrf[:4]
    month = star_wrf[4:6]
    day = star_wrf[6:8]
    hour = star_wrf[8:]
    file_calmet = ff.file_opener('Working_Files\\calmet_try.txt')
    filename = f'{calmet_folder}/calmet.inp'
    if MAKEDAT == 'Auto':
        GEO_DAT = GEODAT
    else:
        GEO_DAT = MAKEDAT
    #BASE WRITING
    file_calmet = ff.sobstituter(file_calmet, '[geo_dat]', GEO_DAT)
    file_calmet = ff.sobstituter(file_calmet, '[srfdat_temp]', calmet_data_list[0])
    file_calmet = ff.sobstituter(file_calmet, '[metdat_temp]', calmet_data_list[2])
    file_calmet = ff.sobstituter(file_calmet, '[m3ddat_temp]', calmet_data_list[1])
    file_calmet = ff.sobstituter(file_calmet, '[year_temp]', year)
    file_calmet = ff.sobstituter(file_calmet, '[month_temp]', month)
    file_calmet = ff.sobstituter(file_calmet, '[day_temp]', day)
    file_calmet = ff.sobstituter(file_calmet, '[hour_temp]', hour)
    file_calmet = ff.sobstituter(file_calmet, '[num_wrf_files_temp]', num_files)
    #PROJECTION WRITING 
    file_calmet = ff.sobstituter(file_calmet, '[projection]', PROJ)
    file_calmet = ff.sobstituter(file_calmet, '[zone_num]', ZONE.split()[0])
    file_calmet = ff.sobstituter(file_calmet, '[zone_dir]', ZONE.split()[1])
    file_calmet = ff.sobstituter(file_calmet, '[or_lat]', ORIGIN_LAT)
    file_calmet = ff.sobstituter(file_calmet, '[or_lon]', ORIGIN_LON)
    file_calmet = ff.sobstituter(file_calmet, '[x_lat1]', MACH_LAT1)
    file_calmet = ff.sobstituter(file_calmet, '[x_lat2]', MACH_LAT2)
    #GRID WRITING
    file_calmet = ff.sobstituter(file_calmet, '[x_grid]', NX)
    file_calmet = ff.sobstituter(file_calmet, '[y_grid]', NY)
    file_calmet = ff.sobstituter(file_calmet, '[delta]', DIM)
    file_calmet = ff.sobstituter(file_calmet, '[x_or]', XORI)
    file_calmet = ff.sobstituter(file_calmet, '[y_or]', YORI)
    file_calmet = ff.sobstituter(file_calmet, '[z_grid]', NZ)
    file_calmet = ff.sobstituter(file_calmet, '[z_grid_face]', ZFACE)
    
    ff.write_inp(filename, file_calmet)
