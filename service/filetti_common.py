from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def load_delimited_dataframe(path: Path, header_separator: str, row_separator: str) -> pd.DataFrame:
    path = Path(path)
    with path.open('r', encoding='utf-8') as handle:
        header = handle.readline().strip().split(header_separator)
        header = [column.split('(')[0].strip() for column in header]
        rows = [line.strip().split(row_separator) for line in handle if line.strip()]
    return pd.DataFrame(rows, columns=header)


def sci_format(value) -> str:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = 0.0

    formatted = f'{numeric_value:.6E}'
    if 'E' not in formatted:
        return formatted

    mantissa, exponent = formatted.split('E')
    sign = exponent[0]
    exponent_value = exponent[1:].zfill(3)
    return f'{mantissa}E{sign}{exponent_value}'


def format_dt(dt: datetime) -> str:
    return f'{dt.year} {dt.timetuple().tm_yday:03d} {dt.hour:02d} 0000'


def coerce_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    formats = (
        '%d/%m/%Y %H:%M',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%Y%m%d%H',
        '%Y%m%d',
    )
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    raise ValueError(f'Formato data non supportato: {value}')


def resolve_output_path(output_dir, output_name: str | None, default_filename: str) -> Path:
    base_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parents[1] / 'Outputs'
    base_dir.mkdir(parents=True, exist_ok=True)

    if output_name:
        candidate = Path(str(output_name).strip())
        filename = candidate.name
        if not candidate.suffix:
            filename = f'{filename}.txt'
    else:
        filename = default_filename

    return base_dir / filename