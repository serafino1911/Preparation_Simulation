from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

from service.filetti_common import coerce_datetime, format_dt, load_delimited_dataframe, resolve_output_path, sci_format


HEADER = '''BAEMARB.DAT     2.1
1
Areali
UTM
  32N
WGS-84  02-21-2003
  KM
UTC+0100'''

DEFAULT_MOLPESIS = {'PM10': {'mol': '200.', 'units': 'g/s'}}
DEFAULT_UNITS = 'g/s'


def _load_input(path: Path) -> pd.DataFrame:
    dataframe = load_delimited_dataframe(Path(path), '\t', '\t')
    dataframe['date'] = dataframe['year'] + '-' + dataframe['month'] + '-' + dataframe['day'] + '-' + dataframe['hour']
    dataframe['date'] = pd.to_datetime(dataframe['date'], format='%Y-%m-%d-%H')
    dataframe = dataframe.sort_values(by='date')
    return dataframe.drop(columns=['year', 'month', 'day', 'hour'])


def _load_params(path: Path) -> pd.DataFrame:
    return load_delimited_dataframe(Path(path), ',', ',')


def _selected_units(molpesis: dict[str, dict]) -> str:
    for value in molpesis.values():
        if isinstance(value, dict) and str(value.get('units', '')).strip():
            return str(value['units']).strip()
    return DEFAULT_UNITS


def _selected_mol(pollutant: str, molpesis: dict[str, dict]) -> str:
    value = molpesis.get(pollutant)
    if isinstance(value, dict) and str(value.get('mol', '')).strip():
        return str(value['mol']).strip()

    fallback = next(iter(molpesis.values()), None)
    if isinstance(fallback, dict) and str(fallback.get('mol', '')).strip():
        return str(fallback['mol']).strip()

    return '0.'


def _format_source_line(source_id: str, units: str) -> str:
    return f"'{source_id}'  '{units}'  0.0  0.0"


def _format_hourly_line(source_id: str, row, pollutant_names: list[str], df_input: pd.DataFrame, start_hr, end_hr) -> str:
    coordinates = [float(row[column]) for column in ('X1', 'X2', 'X3', 'X4', 'Y1', 'Y2', 'Y3', 'Y4')]
    hstk = float(row['hstk'])
    hbase = float(row['hbase'])
    temp = float(row['Temp'])
    vel = float(row['vel'])
    radius = float(row['radius'])

    line = f"'{source_id}'"
    for value in coordinates:
        line += f'  {sci_format(value)}'
    line += f'  {hstk: .1f}'
    line += f'  {hbase: .1f}'
    line += f' {temp: .1f}'
    line += f'  {vel: .1f}'
    line += f'  {radius: .1f}'
    line += f'  {0.0: .1f}'

    for pollutant in pollutant_names:
        values = df_input[
            (df_input['date'] >= start_hr)
            & (df_input['date'] < end_hr)
            & (df_input['areale'] == source_id)
        ][pollutant]
        amount = float(values.iloc[0]) if len(values) > 0 else 0.0
        line += f'  {sci_format(amount)}'

    return line


def generate_filetti_areali(
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
    pollutant_names = [column for column in df_input.columns if column not in {'date', 'areale'}]

    header_end = end_dt
    effective_end = end_dt + timedelta(days=1) if end_dt.hour == 0 and end_dt.minute == 0 else end_dt
    output_path = resolve_output_path(output_dir, output_name, 'filetti_areali.txt')
    units = _selected_units(resolved_molpesis)

    lines = [HEADER]
    lines.append(f'{format_dt(start_dt)} {format_dt(header_end)}')
    lines.append(f' {len(df_params)} {len(pollutant_names)}')
    lines.append(' '.join([f"'{pollutant}'" for pollutant in pollutant_names]))
    lines.append(' '.join([_selected_mol(pollutant, resolved_molpesis) for pollutant in pollutant_names]))

    for source_id in df_params['ID_Areale']:
        lines.append(_format_source_line(str(source_id), units))

    current_hr = start_dt
    while current_hr < effective_end:
        next_hr = current_hr + timedelta(hours=1)
        lines.append(f'{format_dt(current_hr)} {format_dt(next_hr)}')
        for source_id in df_params['ID_Areale']:
            row = df_params[df_params['ID_Areale'] == source_id].iloc[0]
            lines.append(_format_hourly_line(str(source_id), row, pollutant_names, df_input, current_hr, next_hr))
        current_hr = next_hr

    output_path.write_text('\n'.join(lines), encoding='utf-8')
    return output_path