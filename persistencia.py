from storage_gsheets import (
    ensure_headers,
    save_group_to_sheets,
    load_group_from_sheets,
    load_all_group_ids,
)


_HEADERS_READY = False


def init_persistencia() -> None:
    """Garantiza que las hojas tengan encabezados antes de operar."""
    global _HEADERS_READY
    if not _HEADERS_READY:
        ensure_headers()
        _HEADERS_READY = True


# Inicialización temprana para mantener compatibilidad con el código actual.
init_persistencia()



def save_group_data(grupo_actual: dict) -> None:
    """Guarda el estado de un grupo en Google Sheets.

    No persiste el grupo temporal del sistema (G00).
    """
    grupo_id = grupo_actual.get("grupo", {}).get("grupo_id", "G00")
    if grupo_id != "G00":
        save_group_to_sheets(grupo_actual)



def load_group_data(grupo_id: str):
    """Carga el estado de un grupo desde Google Sheets."""
    return load_group_from_sheets(grupo_id)



def get_all_group_ids():
    """Retorna todos los IDs de grupo registrados."""
    return load_all_group_ids()
