import os
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as file_handle:
        return json.load(file_handle)


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


def _format_latlon(value: float, positive_suffix: str, negative_suffix: str) -> str:
    suffix = positive_suffix if value >= 0 else negative_suffix
    return f"{abs(value):.6f}{suffix}"


def generate_ctgproc_inp(
    domain_config_path: Path,
    landuse_config_path: Path,
    output_dir: Path,
    template_path: Path | None = None,
) -> Path:
    """Genera il file ctgproc.inp in output_dir da configurazioni dominio e landuse."""
    domain_config = _read_json(Path(domain_config_path))
    landuse_config = _read_json(Path(landuse_config_path))

    grid_origin = domain_config.get('grid_origin', {})
    vertices = domain_config.get('vertices', {})
    grid_step = domain_config.get('grid_step', {})

    zone_value = domain_config.get('zona_utm') or landuse_config.get('zona_utm') or '32N'
    zone_num, zone_dir = _normalize_zone(zone_value)

    origin_lat = grid_origin.get('lat', 44.404709)
    origin_lon = grid_origin.get('lon', 8.868261)
    origin_lat_str = _format_latlon(origin_lat, 'N', 'S')
    origin_lon_str = _format_latlon(origin_lon, 'E', 'W')

    xori = grid_origin.get('km_x')
    yori = grid_origin.get('km_y')
    if xori is None or yori is None:
        sw_vertex = vertices.get('SW', {})
        xori = sw_vertex.get('km_x', 0.0) if xori is None else xori
        yori = sw_vertex.get('km_y', 0.0) if yori is None else yori

    nx = int(grid_origin.get('nx', 250))
    ny = int(grid_origin.get('ny', 185))
    dim = float(grid_step.get('value', 0.081))

    workspace_root = Path(domain_config_path).resolve().parent.parent
    resolved_template_path = Path(template_path) if template_path else workspace_root / 'Working_Files' / 'ctgproc_try.txt'
    if not resolved_template_path.exists():
        raise FileNotFoundError(f'Template CTGPROC non trovato: {resolved_template_path}')

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    nzgen_file = Path(landuse_config.get('output_file', 'Outputs/landuse.xyz')).name

    content = resolved_template_path.read_text(encoding='utf-8')
    replacements = {
        '[NDBF]': '1',
        '[LUDAT]': 'luse.dat',
        '[RUNLST]': 'ctgproc.lst',
        '[NZGEN]': nzgen_file,
        '[PMAP]': 'UTM',
        '[FEAST]': '0.0',
        '[FNORTH]': '0.0',
        '[IUTMZN]': zone_num,
        '[UTMHEM]': zone_dir,
        '[RLAT0]': origin_lat_str,
        '[RLON0]': origin_lon_str,
        '[RLAT1]': '40.00N',
        '[RLAT2]': '40.01N',
        '[XREFKM]': str(xori),
        '[YREFKM]': str(yori),
        '[NX]': str(nx),
        '[NY]': str(ny),
        '[DGRIDKM]': str(dim),
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    output_file = output_dir / 'ctgproc.inp'
    output_file.write_text(content, encoding='utf-8')
    return output_file

def write_ctgproc_input():
    from pypack_day.configuration import general_configuration as general_cfg
    from pypack_day.configuration import config_ctgproc as ctgproc_cfg
    import pypack_day.functions.fastask as ff

    file_ctgproc = ff.file_opener('pypack_day/lib/ctgproc_try.txt')
    base_dir = os.path.dirname(ctgproc_cfg.WHERE_CTGPROC)
    lu_name = os.path.basename(ctgproc_cfg.WHERE_LANDUSE)
    filename = os.path.join(base_dir, 'ctgproc.inp')
    file_ctgproc = ff.sobstituter(file_ctgproc, "[NDBF]", "1")
    file_ctgproc = ff.sobstituter(file_ctgproc, "[LUDAT]", ctgproc_cfg.LUDAT)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[RUNLST]", ctgproc_cfg.RUNLST)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[NZGEN]", lu_name)


    file_ctgproc = ff.sobstituter(file_ctgproc, "[PMAP]", general_cfg.PROJ)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[FEAST]", general_cfg.FEAST)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[FNORTH]", general_cfg.FNORTH)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[IUTMZN]", general_cfg.ZONE.split()[0])
    file_ctgproc = ff.sobstituter(file_ctgproc, "[UTMHEM]", general_cfg.ZONE.split()[1])
    file_ctgproc = ff.sobstituter(file_ctgproc, "[RLAT0]", general_cfg.ORIGIN_LAT)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[RLON0]", general_cfg.ORIGIN_LON)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[RLAT1]", general_cfg.MACH_LAT1)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[RLAT2]", general_cfg.MACH_LAT2)

    file_ctgproc = ff.sobstituter(file_ctgproc, "[XREFKM]", general_cfg.XORI)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[YREFKM]", general_cfg.YORI)

    file_ctgproc = ff.sobstituter(file_ctgproc, "[NX]", general_cfg.NX)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[NY]", general_cfg.NY)
    file_ctgproc = ff.sobstituter(file_ctgproc, "[DGRIDKM]", general_cfg.DIM)

    ff.write_inp(filename, file_ctgproc)


