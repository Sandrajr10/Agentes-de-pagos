"""Utilidad de fecha del negocio.

La app calcula los vencimientos con el día real en Costa Rica. El servidor
donde corre (Render) usa UTC, que va 6 horas adelante, por lo que cerca de la
medianoche la fecha del servidor ya es la del día siguiente.
"""

from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo

    ZONA_COSTA_RICA = ZoneInfo("America/Costa_Rica")
except Exception:  # pragma: no cover - depende del sistema operativo
    ZONA_COSTA_RICA = None


def hoy_en_costa_rica() -> date:
    """Devuelve la fecha actual en Costa Rica."""
    if ZONA_COSTA_RICA is None:
        return date.today()
    return datetime.now(ZONA_COSTA_RICA).date()
