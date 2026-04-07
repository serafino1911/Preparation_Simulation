#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Modulo per la scrittura automatica del file di input (.inp) per CALPUFF.
Gestisce la sostituzione dei parametri nel template e la configurazione delle emissioni (puntuali, areali, volumetriche, lineari, stradali, flare).
'''
import os
import json
import importlib
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


class _WrfDateCompat:
    @staticmethod
    def wrf_start_end_choosen(start_date: str, num_days: int) -> tuple[str, str]:
        start_dt = _parse_date(start_date)
        end_dt = start_dt + timedelta(days=max(int(num_days), 0))
        return start_dt.strftime('%Y%m%d00'), end_dt.strftime('%Y%m%d00')


try:
    ff = importlib.import_module('pypack_day.functions.fastask')
except Exception:
    ff = _FastAskCompat()

try:
    wrf_date = importlib.import_module('pypack_day.functions.wrf_date')
except Exception:
    wrf_date = _WrfDateCompat()


# Default runtime configuration (used when legacy imports are unavailable)
NUM_PERIODS = 24
IOUTU = 1
IPRTU = 3

IPTU = 1
NPT2 = 0
IARU = 1
NAR2 = 0
IVLU = 1
NVL2 = 0
NFL2 = 0
NRD1 = 0
IRDU = 1
NRD2 = 0
NLN2 = 0
NLINES = 0
ILNU = 1
MXNSEG = 2
NLRISE = 1
XL = 20.0
HBL = 30.0
WBL = 20.0
DXL = 10.0
FPRIMEL = 10000.0
WML = 10.0

TABELLA = True
SPECIES = {
    'VOC': {
        'dry_deposition': 1,
        'gas_inq': {'diffus': '0.1345', 'alfa': '1.0', 'react': '2.0', 'Mesophyll': '25.0', 'Henry_coef': '18.0'},
        'dry_inq': None,
        'wet_inq': {'Liq_Prec': '3.0E-05', 'Froz_Prec': '0.0E00'},
    }
}

POINT_NAMES = ['DUMMY.DAT']
AREA_NAMES = ['DUMMY.DAT']
VOLUME_NAMES = ['DUMMY.DAT']
ROAD_NAMES = ['DUMMY.DAT']
LINE_NAMES = ['DUMMY.DAT']
FLARE_NAMES = ['DUMMY.DAT']

Puntual_Emission = []
Area_Emission = []
Volume_Emission = []
Road_Emission = []
Line_Emission = []

scal_fact_punt_sor = []
scal_fact_area_sor = []
scal_fact_vol_sor = []
scal_fact_road_sor = []
scal_fact_line_sor = []

TABELLA_FINALE_HD = []
TABELLA_FINALE_HOUR24 = {}
TABELLA_FINALE_DAY7 = {}
TABELLA_FINALE_MONTH12 = {}

PROJ = 'UTM'
ZONE = '32 N'
FEAST = '0.0'
FNORTH = '0.0'
ORIGIN_LAT = '45.200000N'
ORIGIN_LON = '9.100000E'
MACH_LAT1 = '40.00N'
MACH_LAT2 = '40.01N'
NX = 180
NY = 200
DIM = 0.081
NZ = 10
ZFACE = '0.,20.,40.,80.,160.,300.,600.,1000.,1500.,2200.,3000.'
XORI = 479.385
YORI = 4909.341


def _read_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as file_handle:
        return json.load(file_handle)


def _parse_date(date_value: str) -> datetime:
    supported_formats = (
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%Y%m%d',
        '%Y%m%d%H',
    )
    for date_format in supported_formats:
        try:
            return datetime.strptime(str(date_value).strip(), date_format)
        except ValueError:
            continue
    raise ValueError(f"Formato data non supportato: {date_value}")


def _normalize_zone(zone_value: str) -> str:
    raw_value = (zone_value or '').strip().upper().replace(' ', '')
    if not raw_value:
        return '32 N'

    index = 0
    while index < len(raw_value) and raw_value[index].isdigit():
        index += 1

    zone_num = raw_value[:index] or '32'
    zone_dir = raw_value[index:index + 1] or 'N'
    return f'{zone_num} {zone_dir}'


def _apply_runtime_config(calpuff_config: dict, calmet_config: dict, domain_config: dict, landuse_config: dict) -> None:
    global NUM_PERIODS, IOUTU, IPRTU
    global IPTU, NPT2, IARU, NAR2, IVLU, NVL2, NFL2, NRD1, IRDU, NRD2
    global NLN2, NLINES, ILNU, MXNSEG, NLRISE, XL, HBL, WBL, DXL, FPRIMEL, WML
    global TABELLA, SPECIES
    global POINT_NAMES, AREA_NAMES, VOLUME_NAMES, ROAD_NAMES, LINE_NAMES, FLARE_NAMES
    global Puntual_Emission, Area_Emission, Volume_Emission, Road_Emission, Line_Emission
    global scal_fact_punt_sor, scal_fact_area_sor, scal_fact_vol_sor, scal_fact_road_sor, scal_fact_line_sor
    global TABELLA_FINALE_HD, TABELLA_FINALE_HOUR24, TABELLA_FINALE_DAY7, TABELLA_FINALE_MONTH12
    global PROJ, ZONE, FEAST, FNORTH, ORIGIN_LAT, ORIGIN_LON, MACH_LAT1, MACH_LAT2
    global NX, NY, DIM, NZ, ZFACE, XORI, YORI

    NUM_PERIODS = calpuff_config.get('num_periods', NUM_PERIODS)
    IOUTU = calpuff_config.get('ioutu', IOUTU)
    IPRTU = calpuff_config.get('iprtu', IPRTU)

    IPTU = calpuff_config.get('iptu', IPTU)
    NPT2 = calpuff_config.get('npt2', NPT2)
    IARU = calpuff_config.get('iaru', IARU)
    NAR2 = calpuff_config.get('nar2', NAR2)
    IVLU = calpuff_config.get('ivlu', IVLU)
    NVL2 = calpuff_config.get('nvl2', NVL2)
    NFL2 = calpuff_config.get('nfl2', NFL2)
    NRD1 = calpuff_config.get('nrd1', NRD1)
    IRDU = calpuff_config.get('irdu', IRDU)
    NRD2 = calpuff_config.get('nrd2', NRD2)
    NLN2 = calpuff_config.get('nln2', NLN2)
    NLINES = calpuff_config.get('nlines', NLINES)
    ILNU = calpuff_config.get('ilnu', ILNU)
    MXNSEG = calpuff_config.get('mxnseg', MXNSEG)
    NLRISE = calpuff_config.get('nlrise', NLRISE)
    XL = calpuff_config.get('xl', XL)
    HBL = calpuff_config.get('hbl', HBL)
    WBL = calpuff_config.get('wbl', WBL)
    DXL = calpuff_config.get('dxl', DXL)
    FPRIMEL = calpuff_config.get('fprimel', FPRIMEL)
    WML = calpuff_config.get('wml', WML)

    TABELLA = calpuff_config.get('tabella', TABELLA)
    SPECIES = calpuff_config.get('species', SPECIES)

    POINT_NAMES = calpuff_config.get('point_names', POINT_NAMES)
    AREA_NAMES = calpuff_config.get('area_names', AREA_NAMES)
    VOLUME_NAMES = calpuff_config.get('volume_names', VOLUME_NAMES)
    ROAD_NAMES = calpuff_config.get('road_names', ROAD_NAMES)
    LINE_NAMES = calpuff_config.get('line_names', LINE_NAMES)
    FLARE_NAMES = calpuff_config.get('flare_names', FLARE_NAMES)

    Puntual_Emission = calpuff_config.get('point_sources', Puntual_Emission)
    Area_Emission = calpuff_config.get('area_emission', Area_Emission)
    Volume_Emission = calpuff_config.get('volume_emission', Volume_Emission)
    Road_Emission = calpuff_config.get('road_emission', Road_Emission)
    Line_Emission = calpuff_config.get('line_emission', Line_Emission)

    scal_fact_punt_sor = calpuff_config.get('scal_fact_punt_sor', scal_fact_punt_sor)
    scal_fact_area_sor = calpuff_config.get('scal_fact_area_sor', scal_fact_area_sor)
    scal_fact_vol_sor = calpuff_config.get('scal_fact_vol_sor', scal_fact_vol_sor)
    scal_fact_road_sor = calpuff_config.get('scal_fact_road_sor', scal_fact_road_sor)
    scal_fact_line_sor = calpuff_config.get('scal_fact_line_sor', scal_fact_line_sor)

    TABELLA_FINALE_HD = calpuff_config.get('scaling_factors', TABELLA_FINALE_HD)
    scaling_data = calpuff_config.get('scaling_data', {})
    TABELLA_FINALE_HOUR24 = scaling_data.get('HOUR24', TABELLA_FINALE_HOUR24)
    TABELLA_FINALE_DAY7 = scaling_data.get('DAY7', TABELLA_FINALE_DAY7)
    TABELLA_FINALE_MONTH12 = scaling_data.get('MONTH12', TABELLA_FINALE_MONTH12)

    PROJ = calmet_config.get('proj', PROJ)
    zone_value = calmet_config.get('zone') or domain_config.get('zona_utm') or landuse_config.get('zona_utm')
    ZONE = _normalize_zone(zone_value) if zone_value else ZONE
    FEAST = calmet_config.get('feast', FEAST)
    FNORTH = calmet_config.get('fnorth', FNORTH)
    ORIGIN_LAT = calmet_config.get('origin_lat', ORIGIN_LAT)
    ORIGIN_LON = calmet_config.get('origin_lon', ORIGIN_LON)
    MACH_LAT1 = calmet_config.get('mach_lat1', MACH_LAT1)
    MACH_LAT2 = calmet_config.get('mach_lat2', MACH_LAT2)

    grid_origin = domain_config.get('grid_origin', {})
    grid_step = domain_config.get('grid_step', {})
    vertices = domain_config.get('vertices', {})
    sw_vertex = vertices.get('SW', {})

    NX = calmet_config.get('nx', grid_origin.get('nx', NX))
    NY = calmet_config.get('ny', grid_origin.get('ny', NY))
    DIM = calmet_config.get('dim', grid_step.get('value', DIM))
    NZ = calmet_config.get('nz', NZ)
    ZFACE = calmet_config.get('zface', ZFACE)
    XORI = calmet_config.get('xori', sw_vertex.get('km_x', XORI))
    YORI = calmet_config.get('yori', sw_vertex.get('km_y', YORI))


def generate_daily_inp_files(
    calpuff_config_path: Path,
    temporal_config_path: Path,
    calmet_config_path: Path,
    domain_config_path: Path,
    landuse_config_path: Path,
    output_dir: Path | None = None,
) -> list[Path]:
    """Genera un file .inp CALPUFF per ogni giorno del periodo temporale."""
    calpuff_config = _read_json(Path(calpuff_config_path))
    temporal_config = _read_json(Path(temporal_config_path))
    calmet_config = _read_json(Path(calmet_config_path))
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

    resolved_output_dir = Path(output_dir) if output_dir else Path(calpuff_config_path).resolve().parent.parent / 'CALPUFF_INP'
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    _apply_runtime_config(calpuff_config, calmet_config, domain_config, landuse_config)

    calmet_output = calmet_config.get('calmet_data', 'CALMETDATA').lower()
    created_files: list[Path] = []

    current_date = start_date
    while current_date <= end_date:
        day_token = current_date.strftime('%Y%m%d')
        calpuff_writer(calmet_output, day_token, 1, str(resolved_output_dir))

        generated_file = resolved_output_dir / 'calpuff.inp'
        if not generated_file.exists():
            raise FileNotFoundError(f'File CALPUFF non generato per {day_token}')

        target_file = resolved_output_dir / f'calpuff_{day_token}.inp'
        if target_file.exists():
            target_file.unlink()
        generated_file.rename(target_file)
        created_files.append(target_file)

        current_date += timedelta(days=1)

    return created_files

# Funzione principale per la scrittura del file .inp di CALPUFF
def calpuff_writer(calmet_output, start_date : str, num_days : int, calpuff_folder : str) -> str:
    '''
    Scrive il file di input per CALPUFF a partire dal template e dai parametri di configurazione.
    Args:
        calmet_output (str): nome del file di output di CALMET
        start_date (str): data di inizio simulazione
        num_days (int): numero di giorni di simulazione
        calpuff_folder (str): cartella di lavoro CALPUFF
    Returns:
        out_name+'CON' (str): nome del file di output principale
    '''
    # Calcola le date di inizio/fine simulazione
    star_wrf, end_wrf = wrf_date.wrf_start_end_choosen(start_date, num_days)
    if num_days == 0:
        star_wrf = end_wrf
    # Gestione file di restart: se esiste un file di restart per la data di inizio, lo usa
    restart_in = 'RESTARTEMP.DAT' 
    RESTART = 2
    if os.path.exists(f'{calpuff_folder}/RESTART_{star_wrf[:8]}.DAT'): 
        restart_in = f'RESTART_{star_wrf[:8]}.DAT'
        RESTART = 3
    restart_out = f'RESTART_{end_wrf[:8]}.DAT'
    # Estrae anno, mese, giorno, ora da stringa data
    year_s, month_s, day_s, hour_s = extract_date_parts(star_wrf)
    year_e, month_e, day_e, hour_e = extract_date_parts(end_wrf)
    hour_s = 0
    hour_e = 0
    # Nome base per i file di output
    out_name = f'CALPUFFOUTPUT_{star_wrf[:8]}.'
    calmet_output = f'calmet_{star_wrf[:8]}.dat'
    # Apre il template del file di input
    template_candidate = Path('Working_Files') / 'calpuff_try.txt'
    template_path = template_candidate if template_candidate.exists() else None
    if template_path is None:
        raise FileNotFoundError('Template CALPUFF non trovato (calpuff_try.txt)')

    file_calpuff = ff.file_opener(template_path)
    filename = f'{calpuff_folder}/calpuff.inp' 
    #filename = 'calpuff.inp' 

    #BASE CONFIGURATION
    file_calpuff = ff.sobstituter(file_calpuff, '[metdat_temp]', calmet_output) #output calmet; in general configuration
    file_calpuff = ff.sobstituter(file_calpuff, '[rstartb_temp]', restart_in)
    file_calpuff = ff.sobstituter(file_calpuff, '[puflst_temp]', out_name + 'LST') 
    file_calpuff = ff.sobstituter(file_calpuff, '[condat_temp]', out_name + 'CON') 
    file_calpuff = ff.sobstituter(file_calpuff, '[rstarte_temp]', restart_out) 
    file_calpuff = ff.sobstituter(file_calpuff, '[MRESTART]',RESTART)
    file_calpuff = ff.sobstituter(file_calpuff, '[nrespd_temp]', NUM_PERIODS)

    #CHEMICAL CONFIGURATION
    NSPEC = len(SPECIES)  
    NSE = len(SPECIES)  
    cspec_string = '\n'.join(f' ! CSPEC =           {inq}!         !END!' for inq in SPECIES.keys())
    mod_string_temp = '\n'.join(f'!           {inq}  =         1,               1,           {SPECIES[inq]["dry_deposition"]},                 0   !' for inq in SPECIES.keys())
    save_string_temp = '\n'.join(f'!           {inq} =     1,           1,           0,           0,           0,           0,           0   !' for inq in SPECIES.keys())
    gas_string_temp = '\n'.join(f'!           {inq} =      {vals["gas_inq"]["diffus"]},           {vals["gas_inq"]["alfa"]},           {vals["gas_inq"]["react"]},              {vals["gas_inq"]["Mesophyll"]},                  {vals["gas_inq"]["Henry_coef"]} !' for inq, vals in SPECIES.items() if vals["gas_inq"] is not None)
    dry_string_temp = '\n'.join(f'!        {inq} =           {vals["dry_inq"]["Geo_mass_mean_diam"]},                     {vals["dry_inq"]["Geo_std_dev"]}   !' for inq, vals in SPECIES.items() if vals["dry_inq"] is not None)
    wet_string_temp = '\n'.join(f'!           {inq} =         {vals["wet_inq"]["Liq_Prec"]},              {vals["wet_inq"]["Froz_Prec"]} !' for inq, vals in SPECIES.items() if vals["wet_inq"] is not None)
    file_calpuff = ff.sobstituter(file_calpuff, '[NSPEC]', NSPEC)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NSE]', NSE)   
    file_calpuff = ff.sobstituter(file_calpuff, '[cspec_temp]', cspec_string)   
    file_calpuff = ff.sobstituter(file_calpuff, '[mod_string_temp]', mod_string_temp)   
    file_calpuff = ff.sobstituter(file_calpuff, '[save_string_temp]', save_string_temp)   
    file_calpuff = ff.sobstituter(file_calpuff, '[gas_string_temp]', gas_string_temp)   
    file_calpuff = ff.sobstituter(file_calpuff, '[wet_string_temp]', wet_string_temp)   
    file_calpuff = ff.sobstituter(file_calpuff, '[dry_string_temp]', dry_string_temp)   

    #PUNTUAL EMISSION
    NPTDAT = len(POINT_NAMES)  
    is_point_true = NPTDAT > 1 or (NPTDAT == 1 and POINT_NAMES[0] != 'DUMMY.DAT')  
    is_point = '!' if is_point_true else '*'  
    NPTDAT = NPTDAT if is_point_true else 0  
    NPT1 = len(Puntual_Emission) if not is_point_true else 0
    print("NPT1:", NPT1)
    string_point_name = ""  
    for name_point in POINT_NAMES:  
        string_point_name += f' none         input       {is_point} PTDAT={name_point}{is_point}   {is_point}END{is_point}\n'  
    file_calpuff = ff.sobstituter(file_calpuff, '[NPT1]', NPT1)   
    file_calpuff = ff.sobstituter(file_calpuff, '[IPTU]', IPTU)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NPTDAT]', NPTDAT)   
    file_calpuff = ff.sobstituter(file_calpuff, '[string_point_name]', string_point_name)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NPT2]', NPT2)   
    NSPT1 = len(scal_fact_punt_sor)  if TABELLA else 0
    file_calpuff = ff.sobstituter(file_calpuff, '[NSPT1]', NSPT1)   
    is_here_point_true  = NPT1 >=1
    stinga_emission_constant = emission_constant_stringer(Puntual_Emission, is_here_point_true) 

    string_scaling_factors_point = emission_scalefactor_stringer(scal_fact_punt_sor, is_here_point_true)  
    
    file_calpuff=ff.sobstituter(file_calpuff, '[STRINGS_EMISSIONS_CONSTANT]', stinga_emission_constant)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_SCALING_FACTORS]', string_scaling_factors_point)  
    
    
    #AREA EMISSION
    NAR1 = len(Area_Emission) if Area_Emission else 0
    file_calpuff = ff.sobstituter(file_calpuff, '[NAR1]', NAR1)   
    file_calpuff = ff.sobstituter(file_calpuff, '[IARU]', IARU)   
    NARDAT = len(AREA_NAMES)  
    is_area_true = NARDAT > 1 or (NARDAT == 1 and AREA_NAMES[0] != 'DUMMY.DAT')  
    is_area = '!' if is_area_true else '*'  
    is_area_inp = True if Area_Emission else False
    print("is_area_true: ", is_area_true)
    print("is_area_inp: ", is_area_inp)
    print("in_area: ", is_area)
    NARDAT = NARDAT if is_area_true else 0  
    string_area_name = ""  
    for name_area in AREA_NAMES:  
        string_area_name += f' none         input       {is_area} ARDAT={name_area}{is_area}   {is_area}END{is_area}\n'
    file_calpuff = ff.sobstituter(file_calpuff, '[NARDAT]', NARDAT)   
    file_calpuff = ff.sobstituter(file_calpuff, '[string_area_name]', string_area_name)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NAR2]', NAR2)   
    string_areal_constant = emission_constant_stringer_areal(Area_Emission, is_area_inp)  
    print("string_areal_constant: ", string_areal_constant)
    string_areal_geom = emission_geom_stringer_areal(Area_Emission, is_area_inp)  
    print("string_areal_geom: ", string_areal_geom)
    string_scaling_factors_area = emission_scalefactor_stringer(scal_fact_area_sor, is_area_inp)  
    print("string_scaling_factors_area: ", string_scaling_factors_area)
    file_calpuff=ff.sobstituter(file_calpuff, '[AREA_SCALE_FACTORS_NAMES]', string_scaling_factors_area)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_AREALI_CONSTANT]', string_areal_constant)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_AREA_GEOM]', string_areal_geom)  
    file_calpuff = ff.sobstituter(file_calpuff, '[NAR2]', NAR2)   
    NSAR1 = len(scal_fact_area_sor)  if TABELLA else 0
    file_calpuff = ff.sobstituter(file_calpuff, '[NSAR1]', NSAR1)   


    # VOLUME EMISSION
    NVL1 = len(Volume_Emission) 
    file_calpuff = ff.sobstituter(file_calpuff, '[NVL1]', NVL1)   
    file_calpuff = ff.sobstituter(file_calpuff, '[IVLU]', IVLU)   
    NVOLDAT = len(VOLUME_NAMES)
    is_volume_true = NVOLDAT > 1 or (NVOLDAT == 1 and VOLUME_NAMES[0] != 'DUMMY.DAT')  
    is_volume = '!' if is_volume_true else '*'  
    NVOLDAT = NVOLDAT if is_volume_true else 0  
    
    string_volume_name = ""  
    for name_volume in VOLUME_NAMES:  
        string_volume_name += f' none         input       {is_volume} VOLDAT={name_volume}{is_volume}   {is_volume}END{is_volume}\n'
    file_calpuff = ff.sobstituter(file_calpuff, '[NVOLDAT]', NVOLDAT)   
    file_calpuff = ff.sobstituter(file_calpuff, '[string_volume_name]', string_volume_name)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NVL2]', NVL2)   
    is_volume_inp = True if NVL1 >=1 else False
    string_volume_constant = emission_volume_stringer(Volume_Emission, is_volume_inp)  
    string_scaling_factors_volume = emission_scalefactor_stringer(scal_fact_vol_sor, is_volume_inp)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_VOLUME_CONSTANT]', string_volume_constant)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_VOLUME_SCALE_FACTORS]', string_scaling_factors_volume)  
    file_calpuff = ff.sobstituter(file_calpuff, '[NVL2]', NVL2)      
    NSVL1 = len(scal_fact_vol_sor)  
    file_calpuff = ff.sobstituter(file_calpuff, '[NSVL1]', NSVL1)   
    
    # LINE EMISSION
    file_calpuff = ff.sobstituter(file_calpuff, '[ILNU]', ILNU)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NLINES]', NLINES)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NLN2]', NLN2)   
    file_calpuff = ff.sobstituter(file_calpuff, '[MXNSEG]', MXNSEG)   
    NLNDAT = len(LINE_NAMES)  
    is_line_true = NLINES > 1 or (NLINES == 1 and LINE_NAMES[0] != 'DUMMY.DAT')  
    is_line = '!' if is_line_true else '*'  
    NLNDAT = NLNDAT if is_line_true else 0  
    string_line_name = ""  
    for name_line in LINE_NAMES:  
        string_line_name += f' none         input       {is_line} LNDAT={name_line}{is_line}   {is_line}END{is_line}\n'
    file_calpuff = ff.sobstituter(file_calpuff, '[string_line_name]', string_line_name)   
    if True:#NLN2 == 0 and NLINES > 0:
        file_calpuff = ff.sobstituter(file_calpuff, '[NLRISE]', NLRISE)   
        file_calpuff = ff.sobstituter(file_calpuff, '[XL]', XL)   
        file_calpuff = ff.sobstituter(file_calpuff, '[HBL]', HBL)   
        file_calpuff = ff.sobstituter(file_calpuff, '[WBL]', WBL)   
        file_calpuff = ff.sobstituter(file_calpuff, '[WML]', WML)      
        file_calpuff = ff.sobstituter(file_calpuff, '[DXL]', DXL)   
        file_calpuff = ff.sobstituter(file_calpuff, '[FPRIMEL]', FPRIMEL)   

    file_calpuff = ff.sobstituter(file_calpuff, '[NLNDAT]', NLNDAT)   
    NSLN1 = len(scal_fact_line_sor)  
    file_calpuff = ff.sobstituter(file_calpuff, '[NSLN1]', NSLN1)   
    string_line_constant = emission_line_stringer(Line_Emission, is_line_true)  
    string_scaling_factors_line = emission_scalefactor_stringer(scal_fact_line_sor, is_line_true)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_LINE_STRING]', string_line_constant)  
    file_calpuff=ff.sobstituter(file_calpuff, '[LINE_SCALE_FACTORS_NAMES]', string_scaling_factors_line)  

    #ROAD EMISSION
    file_calpuff = ff.sobstituter(file_calpuff, '[NRD1]', NRD1)   
    file_calpuff = ff.sobstituter(file_calpuff, '[IRDU]', IRDU)   
    NRDDAT = len(ROAD_NAMES)  
    is_road_true = NRDDAT > 1 or (NRDDAT == 1 and ROAD_NAMES[0] != 'DUMMY.DAT')  
    is_road = '!' if is_road_true else '*'  
    NRDDAT = NRDDAT if is_road_true else 0  
    string_road_name = ""  
    for name_road in ROAD_NAMES:  
        string_road_name += f' none         input       {is_road} RDDAT={name_road}{is_road}   {is_road}END{is_road}\n'
    file_calpuff = ff.sobstituter(file_calpuff, '[string_road_name]', string_road_name)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NRDDAT]', NRDDAT)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NRD2]', NRD2)   
    string_road_constant = emission_road_stringer(Road_Emission, is_road_true)  
    string_scaling_factors_road = emission_scalefactor_stringer(scal_fact_road_sor, is_road_true)  
    string_road_geom = emission_geom_stringer_road(Road_Emission, is_road_true)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_ROAD_EMISSIONS_CONSTANT]', string_road_constant)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_ROAD_SCALE_FACTORS]', string_scaling_factors_road)  
    file_calpuff=ff.sobstituter(file_calpuff, '[STRING_ROAD_COORDINATES]', string_road_geom)  
    NSFRDS = len(scal_fact_road_sor)  
    file_calpuff = ff.sobstituter(file_calpuff, '[NSFRDS]', NSFRDS)   


    # FLARE EMISSION
    file_calpuff = ff.sobstituter(file_calpuff, '[NFL2]', NFL2)   
    NFLDAT = len(FLARE_NAMES)  
    is_flare_true = NFLDAT > 1 or (NFLDAT == 1 and FLARE_NAMES[0] != 'DUMMY.DAT')  
    is_flare = '!' if is_flare_true else '*'  
    NFLDAT = NFLDAT if is_flare_true else 0  
    string_flare_name = ""  
    for name_flare in FLARE_NAMES:  
        string_flare_name += f' none         input       {is_flare} FRDAT={name_flare}{is_flare}   {is_flare}END{is_flare}\n'
    file_calpuff = ff.sobstituter(file_calpuff, '[string_flare_name]', string_flare_name)   
    file_calpuff = ff.sobstituter(file_calpuff, '[NFLDAT]', NFLDAT) 
    

    NSFTAB = len(TABELLA_FINALE_HD) if TABELLA else 0
    file_calpuff = ff.sobstituter(file_calpuff, '[NSFTAB]', NSFTAB) 

    #DATE configuration
    file_calpuff = ff.sobstituter(file_calpuff, '[year_s_temp]', year_s)
    file_calpuff = ff.sobstituter(file_calpuff, '[month_s_temp]', month_s)
    file_calpuff = ff.sobstituter(file_calpuff, '[day_s_temp]', day_s)
    file_calpuff = ff.sobstituter(file_calpuff, '[hour_s_temp]', hour_s)
    file_calpuff = ff.sobstituter(file_calpuff, '[year_e_temp]', year_e)
    file_calpuff = ff.sobstituter(file_calpuff, '[month_e_temp]', month_e)
    file_calpuff = ff.sobstituter(file_calpuff, '[day_e_temp]', day_e)
    file_calpuff = ff.sobstituter(file_calpuff, '[hour_e_temp]', hour_e)

    
    #PROJECTION WRITING 
    file_calpuff = ff.sobstituter(file_calpuff, '[projection]', PROJ)
    file_calpuff = ff.sobstituter(file_calpuff, '[IUTMZN]', ZONE.split()[0])
    file_calpuff = ff.sobstituter(file_calpuff, '[UTMHEM]', ZONE.split()[1])
    file_calpuff = ff.sobstituter(file_calpuff, '[FEAST]', FEAST)
    file_calpuff = ff.sobstituter(file_calpuff, '[FNORTH]', FNORTH)
    file_calpuff = ff.sobstituter(file_calpuff, '[RLAT0]', ORIGIN_LAT)
    file_calpuff = ff.sobstituter(file_calpuff, '[RLON0]', ORIGIN_LON)
    file_calpuff = ff.sobstituter(file_calpuff, '[XLAT1]', MACH_LAT1)
    file_calpuff = ff.sobstituter(file_calpuff, '[XLAT2]', MACH_LAT2)
    #GRID WRITING
    file_calpuff = ff.sobstituter(file_calpuff, '[NX]', NX)
    file_calpuff = ff.sobstituter(file_calpuff, '[NY]', NY)
    file_calpuff = ff.sobstituter(file_calpuff, '[DGRIDKM]', DIM)
    file_calpuff = ff.sobstituter(file_calpuff, '[NZ]', NZ)
    file_calpuff = ff.sobstituter(file_calpuff, '[z_grid_face]', ZFACE)
    file_calpuff = ff.sobstituter(file_calpuff, '[XORIGKM]', XORI)
    file_calpuff = ff.sobstituter(file_calpuff, '[YORIGKM]', YORI)

    #OUTPUT CONFIGURATION
    file_calpuff = ff.sobstituter(file_calpuff, '[IOUTU]', IOUTU) 
    file_calpuff = ff.sobstituter(file_calpuff, '[IPRTU]', IPRTU) 

    file_calpuff = ff.sobstituter(file_calpuff, '[TABELLA_FINALE]', table_going())

    ff.write_inp(filename, file_calpuff)
    return out_name+'CON'

def celsius_to_kelvin(temp_celsius: float) -> float:
    return temp_celsius + 273.15

def emission_constant_stringer(emission_constant : list, go: bool) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        rates = dicti["emis_rates"]
        rato = ", ".join([str(rate) for rate in rates])

        end_string += f'! X = {dicti["coord_x"]}, {dicti["coord_y"]}, {dicti["height"]}, {dicti["base_elev"]}, {dicti["diam"]}, {dicti["vel"]}, {celsius_to_kelvin(dicti["temp"])}, {dicti["flag_bldg"]}, {rato} !\n'
        end_string += f'!END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
    return end_string

def emission_volume_stringer(emission_constant : list, go: bool) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        rates = dicti["emis_rates"]
        rato = ", ".join([str(rate) for rate in rates])
        end_string += f'! X = {dicti["position"][0]}, {dicti["position"][1]}, {dicti["height"]}, {dicti["base_elev"]}, {dicti["initial_sigma_y"]}, {dicti["initial_sigma_z"]}, {rato} !\n'
        end_string += f'!END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if not TABELLA:
            return end_string
    return end_string

def emission_geom_stringer_road(emission_constant : list, go: bool) -> str:
    end_string = ""
    for i,dicti in enumerate(emission_constant):
        end_string += f' ! SRCNAM = {dicti["source_name"]} !\n' 
        poligon = dicti["position_xyz"]
        end_string += f' ! NPTROAD = {len(poligon)} !\n'
        for i, point in enumerate(poligon):
            end_string += f' {i+1}    ! XYZ = {point[0]}, {point[1]}, {point[2]} ! !END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if not TABELLA:
            return end_string
    return end_string

def emission_geom_stringer_areal(emission_constant : list, go: bool, go2: bool = False) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        poligon = dicti["poligon"]
        xvert = ", ".join([str(point[0]) for point in poligon]) + "!"
        yvert = ", ".join([str(point[1]) for point in poligon]) + "!"
        end_string += f'{i+1} ! XVERT = {xvert}\n'
        end_string += f'{i+1} ! YVERT = {yvert}\n'
        end_string += f'!END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if not TABELLA:
            return end_string
        if go2:
            end_string = end_string.replace('*', '!')
    return end_string

def emission_line_stringer(emission_constant : list, go: bool) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        rates = dicti["emis_rates"]
        rato = ", ".join([str(rate) for rate in rates])
        end_string += f'{i+1} ! X = {dicti["position_xy"][0][0]}, {dicti["position_xy"][0][1]}, {dicti["position_xy"][1][0]}, {dicti["position_xy"][0][1]}, {dicti["relase_height"]}, {dicti["base_elev"]}, {rato} !\n'
        end_string += f'!END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
    return end_string

def emission_road_stringer(emission_constant : list, go :bool) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        rates = dicti["emis_rates"]
        rato = ", ".join([str(rate) for rate in rates])
        end_string += f'{i+1} ! X = {dicti["Effect_height"]}, {dicti["initial_sigma_z"]}, {dicti["initial_sigma_y"]}, {rato} ! !END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if not TABELLA:
            return end_string
    return end_string

def emission_constant_stringer_areal(emission_constant : list, go: bool, go2: bool = False) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_constant):
        end_string += f'{i+1} ! SRCNAM = {dicti["source_name"]} !\n' 
        rates = dicti["emis_rates"]
        if len(rates) > 3:
            rato = ", ".join([str(rate) for rate in rates[:3]]) + ",\n" + " " * 8 + ", ".join([str(rate) for rate in rates[3:]])
        else:
            rato = ",".join([str(rate) for rate in rates])
        end_string += f'{i+1} ! X = {dicti["height"]}, {dicti["base_elev"]}, {dicti["initial_sigma_z"]}, {rato} !\n'
        end_string += f'!END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if go2:
            end_string = end_string.replace('*', '!')
    return end_string

def emission_scalefactor_stringer(emission_scalefactor : list, go :bool, go2: bool = False) -> str:
    end_string = ""
    for i, dicti in enumerate(emission_scalefactor):
        end_string += f'{i+1}  ! SCALEFACTOR  =  {dicti["source_name"]},         {dicti["pollutant"]},       {dicti["scaling_factor"]}              !  !END!\n'
    if not go:
        end_string = end_string.replace('!', '*')
        if not TABELLA:
            return end_string
        if go2:
            end_string = end_string.replace('*', '!')
    if not TABELLA:
        end_string = end_string.replace('!', '*')
    return end_string

def table_going() -> str:
    end_string = ""
    for ele in TABELLA_FINALE_HD:
        table_creation = create_table(ele)
        end_string += f' {ele["index"]} ! FACTORNAME    = {ele["factor_name"]} !\n'
        end_string += f' {ele["index"]} ! FACTORTYPE       = {ele["factor_type"]} !\n'
        end_string += f' {ele["index"]} ! FACTORTABLE   = {table_creation} !\n'
        end_string += f' {ele["index"]} !END!\n\n\n'
    if not TABELLA:
        end_string = end_string.replace('!', '*')
    return end_string

def create_table(ele : dict) -> str:
    take_table = {}
    factor_type = ele["factor_type"]
    if "_" not in factor_type:
        if factor_type == "MONTH12":
            take_table = TABELLA_FINALE_MONTH12
        elif factor_type == "HOUR24":
            take_table = TABELLA_FINALE_HOUR24
        elif factor_type == "DAY7":
            take_table = TABELLA_FINALE_DAY7
        else:
            pass
        return ", ".join(take_table[ele["index"]])
    elif factor_type == "HOUR24_DAY7":
        take_table_1 = TABELLA_FINALE_HOUR24[ele["index"]]
        take_table_2 = TABELLA_FINALE_DAY7[ele["index"]]
        # product of the two tables into a matrix
        table = [[str(a * b) for a in take_table_1] for b in take_table_2]
        stringo = ""
        for row in table:
            stringo += ", ".join(row)
            stringo += ",\n"
        return stringo[:-2]
    else: 
        return ""
    
# Funzione di utilità per estrarre anno, mese, giorno e ora da una stringa data in formato 'YYYYMMDDHH'
def extract_date_parts(star_wrf):
    year_s = star_wrf[:4]
    month_s = star_wrf[4:6]
    day_s = star_wrf[6:8]
    hour_s = star_wrf[8:]
    # Restituisce i valori come tuple (tutti stringhe)
    return year_s, month_s, day_s, hour_s

