from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple


Coord = Tuple[float, float]
PointMap = Dict[Coord, float]


def read_oro(path: Path) -> PointMap:
    """Read an oro.txt file: 3 header rows, then x y z rows."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    data_lines = lines[3:]

    points: PointMap = {}
    for i, line in enumerate(data_lines, start=4):
        parts = line.split()
        if len(parts) < 3:
            continue

        try:
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2])
        except ValueError as exc:
            raise ValueError(f"Invalid numeric row in {path} at line {i}: {line}") from exc

        points[(x, y)] = z

    return points


def domain(points: PointMap) -> Tuple[float, float, float, float]:
    xs = [xy[0] for xy in points]
    ys = [xy[1] for xy in points]
    return min(xs), max(xs), min(ys), max(ys)


def area_and_density(points: PointMap) -> Tuple[float, float]:
    xmin, xmax, ymin, ymax = domain(points)
    area = (xmax - xmin) * (ymax - ymin)
    density = (len(points) / area) if area > 0 else 0.0
    return area, density


def print_domain(name: str, points: PointMap) -> None:
    xmin, xmax, ymin, ymax = domain(points)
    print(f"{name} domain:")
    print(f"  x min = {xmin:.2f}, x max = {xmax:.2f}")
    print(f"  y min = {ymin:.2f}, y max = {ymax:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two oro.txt files (3 header rows + x y z)."
    )
    parser.add_argument(
        "file_a",
        nargs="?",
        default="CALMET_FARM/oro.txt",
        help="First oro file path (default: CALMET_FARM/oro.txt)",
    )
    parser.add_argument(
        "file_b",
        nargs="?",
        default="Outputs_utm/oro.txt",
        help="Second oro file path (default: Outputs_utm/oro.txt)",
    )
    parser.add_argument(
        "--output",
        default="compare_oro_output.txt",
        help="Output report file path (default: compare_oro_output.txt)",
    )
    args = parser.parse_args()

    path_a = Path(args.file_a)
    path_b = Path(args.file_b)

    if not path_a.exists():
        raise FileNotFoundError(f"File not found: {path_a}")
    if not path_b.exists():
        raise FileNotFoundError(f"File not found: {path_b}")

    points_a = read_oro(path_a)
    points_b = read_oro(path_b)

    report_lines: list[str] = []

    def emit(line: str = "") -> None:
        print(line)
        report_lines.append(line)

    def emit_domain(name: str, points: PointMap) -> None:
        xmin, xmax, ymin, ymax = domain(points)
        area, density = area_and_density(points)
        emit(f"{name} domain:")
        emit(f"  x min = {xmin:.2f}, x max = {xmax:.2f}")
        emit(f"  y min = {ymin:.2f}, y max = {ymax:.2f}")
        emit(f"  area = {area:.2f}")
        emit(f"  point density = {density:.8f}")

    emit_domain(path_a.as_posix(), points_a)
    emit_domain(path_b.as_posix(), points_b)
    area_a, density_a = area_and_density(points_a)
    area_b, density_b = area_and_density(points_b)
    emit("Grid deltas (file_b - file_a):")
    emit(f"  delta area = {area_b - area_a:.2f}")
    emit(f"  delta point density = {density_b - density_a:.8f}")
    emit()

    common = sorted(set(points_a.keys()) & set(points_b.keys()))
    only_a = sorted(set(points_a.keys()) - set(points_b.keys()))
    only_b = sorted(set(points_b.keys()) - set(points_a.keys()))

    emit(f"Common coordinates: {len(common)}")
    emit(f"Only in {path_a.as_posix()}: {len(only_a)}")
    emit(f"Only in {path_b.as_posix()}: {len(only_b)}")
    emit()

    emit("Differences on common coordinates (dz = z_b - z_a):")
    if not common:
        emit("  No common coordinates found.")
        output_path = Path(args.output)
        output_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        print(f"\nReport written to: {output_path.as_posix()}")
        return

    emit("      x           y        z_a      z_b       dz")
    emit("------------------------------------------------------")
    for x, y in common:
        z_a = points_a[(x, y)]
        z_b = points_b[(x, y)]
        dz = z_b - z_a
        emit(f"{x:10.2f}  {y:10.2f}  {z_a:7.2f}  {z_b:7.2f}  {dz:7.2f}")

    output_path = Path(args.output)
    output_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nReport written to: {output_path.as_posix()}")


if __name__ == "__main__":
    main()
