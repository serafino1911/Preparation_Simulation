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


def generate_terrel_inp(
    domain_config_path: Path,
    orography_config_path: Path,
    output_dir: Path,
    template_path: Path | None = None,
) -> Path:
    """Genera il file terrel.inp in output_dir da configurazioni dominio e orografia."""
    domain_config = _read_json(Path(domain_config_path))
    orography_config = _read_json(Path(orography_config_path))

    grid_origin = domain_config.get('grid_origin', {})
    vertices = domain_config.get('vertices', {})
    grid_step = domain_config.get('grid_step', {})

    zone_value = domain_config.get('zona_utm') or orography_config.get('zona_utm') or '32N'
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
    resolved_template_path = Path(template_path) if template_path else workspace_root / 'Working_Files' / 'terrel_try.txt'
    if not resolved_template_path.exists():
        raise FileNotFoundError(f'Template TERREL non trovato: {resolved_template_path}')

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gen_file = Path(orography_config.get('output_oro', 'Outputs/oro.txt')).name

    content = resolved_template_path.read_text(encoding='utf-8')
    replacements = {
        '[NTDF]': '1',
        '[OUTFIL]': 'terrel.dat',
        '[LSTFIL]': 'terrel.lst',
        '[PLTFIL]': 'terrel.plt',
        '[RAWECHO]': 'terrel_raw.dat',
        '[GEN]': gen_file,
        '[DWVS]': 'WGS-84',
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

    output_file = output_dir / 'terrel.inp'
    output_file.write_text(content, encoding='utf-8')
    return output_file

def write_terrel_input():
    from pypack_day.configuration import general_configuration as general_cfg
    from pypack_day.configuration import config_terrel as terrel_cfg
    import pypack_day.functions.fastask as ff

    file_terr = ff.file_opener('pypack_day/lib/terrel_try.txt')
    base_dir = os.path.dirname(terrel_cfg.WHERE_TERREL)
    oro_name = os.path.basename(terrel_cfg.INPUT_TERREL)
    filename = os.path.join(base_dir, 'terrel.inp')
    file_terr = ff.sobstituter(file_terr, "[NTDF]", "1")
    file_terr = ff.sobstituter(file_terr, "[OUTFIL]", terrel_cfg.OUTFIL)
    file_terr = ff.sobstituter(file_terr, "[LSTFIL]", terrel_cfg.LSTFIL)
    file_terr = ff.sobstituter(file_terr, "[PLTFIL]", terrel_cfg.PLTFIL)
    file_terr = ff.sobstituter(file_terr, "[RAWECHO]", terrel_cfg.RAWECHO)
    file_terr = ff.sobstituter(file_terr, "[GEN]", oro_name)
    file_terr = ff.sobstituter(file_terr, "[DWVS]", terrel_cfg.DWVS)

    file_terr = ff.sobstituter(file_terr, "[PMAP]", general_cfg.PROJ)
    file_terr = ff.sobstituter(file_terr, "[FEAST]", general_cfg.FEAST)
    file_terr = ff.sobstituter(file_terr, "[FNORTH]", general_cfg.FNORTH)
    file_terr = ff.sobstituter(file_terr, "[IUTMZN]", general_cfg.ZONE.split()[0])
    file_terr = ff.sobstituter(file_terr, "[UTMHEM]", general_cfg.ZONE.split()[1])
    file_terr = ff.sobstituter(file_terr, "[RLAT0]", general_cfg.ORIGIN_LAT)
    file_terr = ff.sobstituter(file_terr, "[RLON0]", general_cfg.ORIGIN_LON)
    file_terr = ff.sobstituter(file_terr, "[RLAT1]", general_cfg.MACH_LAT1)
    file_terr = ff.sobstituter(file_terr, "[RLAT2]", general_cfg.MACH_LAT2)

    file_terr = ff.sobstituter(file_terr, "[XREFKM]", general_cfg.XORI)
    file_terr = ff.sobstituter(file_terr, "[YREFKM]", general_cfg.YORI)

    file_terr = ff.sobstituter(file_terr, "[NX]", general_cfg.NX)
    file_terr = ff.sobstituter(file_terr, "[NY]", general_cfg.NY)
    file_terr = ff.sobstituter(file_terr, "[DGRIDKM]", general_cfg.DIM)

    ff.write_inp(filename, file_terr)


