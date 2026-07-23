from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

from service.filetti_common import coerce_datetime, format_dt, load_delimited_dataframe, resolve_output_path, sci_format


HEADER = f'''PTEMARB.DAT     2.1
   1
Puntuali
LCC
44.44783N       8.889191E       40.00N          40.01N
 0.00000000E+00 0.00000000E+00
WGS-84   02-21-2003 
  KM
UTC+0000'''

DEFAULT_MOLPESIS = {
    'NOX': {'mol': '40.', 'units': 'g/s'},
    'PM10': {'mol': '10.', 'units': 'g/s'},
}


def _load_input(path: Path) -> pd.DataFrame:
    dataframe = load_delimited_dataframe(Path(path), '\t', '\t')
    dataframe['date'] = dataframe['year'] + '-' + dataframe['month'] + '-' + dataframe['day'] + '-' + dataframe['hour']
    dataframe['date'] = pd.to_datetime(dataframe['date'], format='%Y-%m-%d-%H')
    dataframe = dataframe.sort_values(by='date')
    return dataframe.drop(columns=['year', 'month', 'day', 'hour'])


def _load_params(path: Path) -> pd.DataFrame:
    return load_delimited_dataframe(Path(path), ',', ',')


def _selected_mol(pollutant: str, molpesis: dict[str, dict]) -> str:
    value = molpesis.get(pollutant)
    if isinstance(value, dict) and str(value.get('mol', '')).strip():
        return str(value['mol']).strip()

    fallback = next(iter(molpesis.values()), None)
    if isinstance(fallback, dict) and str(fallback.get('mol', '')).strip():
        return str(fallback['mol']).strip()

    return '0.'


def generate_filetti_puntuali(
    input_path: Path,
    params_path: Path,
    start_date,
    end_date,
    molpesis: dict[str, dict] | None = None,
    output_dir: Path | None = None,
    output_name: str | None = None,
) -> Path:
    start_dt = coerce_datetime(start_date)
    end_dt = coerce_datetime(end_date)
    if end_dt < start_dt:
        raise ValueError('DATE_END deve essere successiva o uguale a DATE_START')

    resolved_molpesis = molpesis or DEFAULT_MOLPESIS
    df_input = _load_input(Path(input_path))
    df_params = _load_params(Path(params_path))
    pollutant_names = [column for column in df_input.columns if column not in {'date', 'terminal'}]

    output_path = resolve_output_path(output_dir, output_name, 'filetti_puntuali.txt')
    lines = [HEADER]
    lines.append(f'{format_dt(start_dt)} {format_dt(end_dt)}')
    lines.append(f' {len(df_params)} {len(pollutant_names)}')
    lines.append(' '.join([f"'{pollutant}'" for pollutant in pollutant_names]))
    lines.append(' '.join([_selected_mol(pollutant, resolved_molpesis) for pollutant in pollutant_names]))

    for source_id in df_params['ID_PUNT']:
        row = df_params[df_params['ID_PUNT'] == source_id].iloc[0]
        x = float(row['X'])
        y = float(row['Y'])
        hstk = float(row['hstk'])
        diam = float(row['diam'])
        hbase = float(row['hbase'])
        line = f"'{source_id}'"
        line += f'  {sci_format(x)}'
        line += f'  {sci_format(y)}'
        line += f'  {sci_format(hstk)}'
        line += f'  {sci_format(diam)}'
        line += f'  {sci_format(hbase)}'
        line += '  0.0 0.0 0.0'
        lines.append(line)

    current_hr = start_dt
    while current_hr < end_dt:
        next_hr = current_hr + timedelta(hours=1)
        lines.append(f'{format_dt(current_hr)} {format_dt(next_hr)}')
        for source_id in df_params['ID_PUNT']:
            row = df_params[df_params['ID_PUNT'] == source_id].iloc[0]
            temp = float(row['Temp'])
            vel = float(row['vel'])
            line = f"'{source_id}'"
            line += f'  {sci_format(temp)}'
            line += f'  {sci_format(vel)}'
            line += '  0.0 0.0'
            lines.append(line)
        current_hr = next_hr

    output_path.write_text('\n'.join(lines), encoding='utf-8')
    return output_path