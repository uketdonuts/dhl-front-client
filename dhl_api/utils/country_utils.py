"""Utilidades para normalizar nombres de países a partir del CSV ISO.

Lee el archivo ISO_Country_Codes_fullset_*.csv y expone helpers para
resolver el nombre normalizado (en MAYÚSCULAS) desde el código ISO alpha-2.
"""
from __future__ import annotations

import csv
import glob
import os
from functools import lru_cache

from django.conf import settings


def _find_iso_csv_path() -> str | None:
    """Obtiene la ruta más reciente del CSV ISO en dhl_api/.

    Busca archivos con patrón ISO_Country_Codes_fullset_*.csv.
    Devuelve el más reciente si existe; en caso contrario None.
    """
    base_dir = getattr(settings, 'BASE_DIR', None)
    if not base_dir:
        return None
    pattern = os.path.join(base_dir, 'dhl_api', 'ISO_Country_Codes_fullset_*.csv')
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


@lru_cache(maxsize=1)
def get_iso_country_map() -> dict[str, str]:
    """Carga un mapeo {ISO2: NOMBRE_NORMALIZADO} desde el CSV ISO.

    Preferimos la columna "ISO Short Name"; si falta, usamos "ISO Full Name";
    si ambas faltan, caemos a "DHL Internal Short Name". El nombre se retorna
    en MAYÚSCULAS.
    """
    path = _find_iso_csv_path()
    mapping: dict[str, str] = {}
    if not path or not os.path.exists(path):
        return mapping

    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        # Normalizar headers a claves simples
        for row in reader:
            code = (row.get('ISO Country Code') or '').strip().upper()
            if not code:
                continue
            short_name = (row.get('ISO Short Name') or '').strip()
            full_name = (row.get('ISO Full Name') or '').strip()
            dhl_name = (row.get('DHL Internal Short Name') or '').strip()

            name = short_name or full_name or dhl_name or code
            mapping[code] = name.upper()

    return mapping


def get_country_name_from_iso(code: str) -> str:
    """Retorna el nombre de país normalizado (MAYÚSCULAS) para un código ISO2.

    Si no se encuentra, retorna el propio código en MAYÚSCULAS.
    """
    if not code:
        return ''
    code = code.strip().upper()
    return get_iso_country_map().get(code, code)
