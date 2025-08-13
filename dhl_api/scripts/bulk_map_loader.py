"""
Cargador por lotes para el CSV masivo de ubicaciones/postales -> mapeo service_area -> display.

Características:
- Ejecuta el management command load_service_area_map en chunks (start_row/max_rows)
- Filtros por países (CA,US,...) y delimitador opcional
- Modo interactivo para decidir cuándo subir el siguiente chunk
- Reintentos por chunk y pausa configurable entre chunks

Uso dentro del contenedor (Windows):
  django-manage.bat shell -c "import dhl_api.scripts.bulk_map_loader as m; m.main()"

O directamente (si prefieres):
  docker compose exec backend python dhl_api/scripts/bulk_map_loader.py --help
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from typing import Optional

# Bootstrap de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dhl_project.settings')
try:
    import django  # type: ignore
    django.setup()
except Exception as e:
    print(f"[bootstrap] No se pudo inicializar Django: {e}")
    sys.exit(1)

from django.core.management import call_command  # type: ignore


def positive_int(val: str) -> int:
    i = int(val)
    if i < 0:
        raise argparse.ArgumentTypeError('Debe ser >= 0')
    return i


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Carga por lotes del mapeo service_area -> ciudad (CSV masivo)')
    p.add_argument('--file', required=True, help='Ruta del CSV dentro del contenedor, ej: /app/dhl_api/Postal_...csv')
    p.add_argument('--countries', default='', help='ISO2 separados por coma, ej: CA,US')
    p.add_argument('--delimiter', default='', help='Delimitador CSV (auto si vacío)')
    p.add_argument('--derive-service-area', action='store_true', help='Inferir service_area por postal con ServiceZone')
    p.add_argument('--upsert', action='store_true', help='Actualizar si existe (idempotente)')

    p.add_argument('--start-row', type=positive_int, default=0, help='Fila inicial (datos) para empezar (skip)')
    p.add_argument('--chunk-rows', type=positive_int, default=1_000_000, help='Filas por chunk (ej: 1,000,000)')
    p.add_argument('--max-chunks', type=positive_int, default=0, help='Máximo de chunks a procesar (0 = sin límite)')

    p.add_argument('--progress-every', type=positive_int, default=100_000, help='Progreso por N filas dentro del command')
    p.add_argument('--pause-seconds', type=positive_int, default=5, help='Pausa entre chunks (segundos)')
    p.add_argument('--retries', type=positive_int, default=2, help='Reintentos por chunk si falla')
    p.add_argument('--interactive', action='store_true', help='Pedir confirmación antes de cada chunk')
    p.add_argument('--dry-run', action='store_true', help='Solo mostrar plan de ejecución, no inserta')

    return p.parse_args(argv)


def run_chunk(args: argparse.Namespace, start_row: int, rows: int) -> None:
    kwargs = {
        'file': args.file,
        'start_row': start_row,
        'max_rows': rows,
        'progress_every': args.progress_every,
    }
    if args.countries:
        kwargs['countries'] = args.countries
    if args.delimiter:
        kwargs['delimiter'] = args.delimiter
    if args.derive_service_area:
        kwargs['derive_service_area'] = True
    if args.upsert:
        kwargs['upsert'] = True

    print(f"[chunk] start_row={start_row} rows={rows} countries={kwargs.get('countries','ALL')} upsert={args.upsert}")
    call_command('load_service_area_map', **kwargs)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)

    start = args.start_row
    chunk = args.chunk_rows
    max_chunks = args.max_chunks or float('inf')

    print("=== Carga por lotes del mapeo service_area ===")
    print(f"Archivo: {args.file}")
    print(f"Países: {args.countries or 'ALL'}  chunk: {chunk}  inicio: {start}  max_chunks: {args.max_chunks or '∞'}")
    if args.dry_run:
        print("[dry-run] Sin ejecutar inserciones. Solo plan.")

    c = 0
    while c < max_chunks:
        if args.interactive:
            resp = input(f"¿Ejecutar chunk #{c+1} desde {start} por {chunk} filas? [S/n] ").strip().lower()
            if resp not in ('', 's', 'si', 'y', 'yes'):
                print("Cancelado por usuario.")
                break
        t0 = time.time()
        if args.dry_run:
            print(f"[dry-run] Ejecutaría: start_row={start} max_rows={chunk}")
        else:
            attempt = 0
            while True:
                try:
                    run_chunk(args, start_row=start, rows=chunk)
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > args.retries:
                        print(f"[chunk] Falló tras {args.retries} reintentos: {e}")
                        raise
                    wait = min(30, 5 * attempt)
                    print(f"[chunk] Error: {e}  -> reintentando en {wait}s (intento {attempt}/{args.retries})...")
                    time.sleep(wait)
        dt = time.time() - t0
        print(f"[chunk] OK en {dt:.1f}s\n")

        c += 1
        start += chunk
        if args.pause_seconds:
            time.sleep(args.pause_seconds)

    print("=== Finalizado ===")


if __name__ == '__main__':
    main()
