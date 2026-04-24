import json
import gspread
import streamlit as st
from datetime import datetime

SPREADSHEET_KEY = "1Z3gBww6LGLfQVrGn92PTDJGFNs-Ft3FzT9sT8Wv5jf0"
GOOGLE_CREDS_FILE = "service_account.json"

gc = gspread.service_account_from_dict(
    st.secrets["gcp_service_account"]
)
sh = gc.open_by_key(SPREADSHEET_KEY)

GRUPOS_HEADERS = [
    "grupo_id",
    "nombre_grupo",
    "integrantes",
    "xp_mision",
    "xp_epistemico_grupal",
    "fase_actual",
    "perfil_grupal_json",
    "casos_resueltos_json",
    "updated_at",
]

INTEGRANTES_HEADERS = [
    "grupo_id",
    "integrante",
    "xp_epistemico",
    "participacion",
    "updated_at",
]

ENTREGAS_HEADERS = [
    "grupo_id",
    "entrega_id",
    "contenido_json",
    "updated_at",
]


def get_or_create_worksheet(title):
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=title, rows=2000, cols=30)


ws_grupos = get_or_create_worksheet("grupos")
ws_integrantes = get_or_create_worksheet("integrantes")
ws_entregas = get_or_create_worksheet("entregas")


def set_headers_if_needed(ws, headers):
    current = ws.row_values(1)
    if current != headers:
        existing = ws.get_all_values()

        if not existing:
            ws.update("A1", [headers])
            return

        if len(existing) == 1:
            ws.clear()
            ws.update("A1", [headers])
            return

        old_headers = existing[0]
        old_rows = existing[1:]

        if old_headers == headers:
            return

        # Reescribe con los nuevos headers y conserva solo lo que coincida por nombre
        new_rows = []
        for row in old_rows:
            row_dict = {}
            for idx, h in enumerate(old_headers):
                if idx < len(row):
                    row_dict[h] = row[idx]

            new_row = [row_dict.get(h, "") for h in headers]
            new_rows.append(new_row)

        ws.clear()
        ws.update("A1", [headers] + new_rows)


def ensure_headers():
    set_headers_if_needed(ws_grupos, GRUPOS_HEADERS)
    set_headers_if_needed(ws_integrantes, INTEGRANTES_HEADERS)
    set_headers_if_needed(ws_entregas, ENTREGAS_HEADERS)


def find_row_by_value(ws, col_index, value):
    values = ws.col_values(col_index)
    for i, cell_value in enumerate(values, start=1):
        if str(cell_value).strip() == str(value).strip():
            return i
    return None


def delete_rows_for_group(ws, grupo_id):
    all_values = ws.get_all_values()
    if not all_values:
        return

    headers = all_values[0]
    filtered_rows = [headers]

    for row in all_values[1:]:
        if not row:
            continue
        if str(row[0]).strip() != str(grupo_id).strip():
            filtered_rows.append(row)

    ws.clear()
    ws.update("A1", filtered_rows)


def save_group_to_sheets(group_data):
    ensure_headers()
    now = datetime.now().isoformat()

    grupo = group_data.get("grupo", {})
    progreso = group_data.get("progreso", {})
    seguimiento = group_data.get("seguimiento_individual", {})
    entregas = group_data.get("entregas", {})
    perfil_grupal = group_data.get("perfil_grupal", {})
    casos_resueltos = group_data.get("casos_resueltos", [])

    grupo_id = str(grupo.get("grupo_id", "")).strip()
    nombre_grupo = grupo.get("nombre_grupo", grupo_id)
    integrantes = grupo.get("integrantes", [])

    if not grupo_id:
        return

    grupo_row = [
        grupo_id,
        nombre_grupo,
        " | ".join(integrantes),
        progreso.get("xp_mision", 0),
        progreso.get("xp_epistemico_grupal", 0),
        progreso.get("fase_actual", 1),
        json.dumps(perfil_grupal, ensure_ascii=False),
        json.dumps(casos_resueltos, ensure_ascii=False),
        now,
    ]

    existing_row = find_row_by_value(ws_grupos, 1, grupo_id)

    if existing_row and existing_row > 1:
        ws_grupos.update(f"A{existing_row}:I{existing_row}", [grupo_row])
    else:
        ws_grupos.append_row(grupo_row)

    delete_rows_for_group(ws_integrantes, grupo_id)
    for nombre, datos in seguimiento.items():
        ws_integrantes.append_row([
            grupo_id,
            nombre,
            datos.get("xp_epistemico", 0),
            datos.get("participacion", 0.0),
            now,
        ])

    delete_rows_for_group(ws_entregas, grupo_id)
    for entrega_id, contenido in entregas.items():
        ws_entregas.append_row([
            grupo_id,
            entrega_id,
            json.dumps(contenido, ensure_ascii=False) if contenido else "",
            now,
        ])


def load_group_from_sheets(grupo_id):
    ensure_headers()

    grupo_id = str(grupo_id).strip()
    grupos = ws_grupos.get_all_records()

    grupo_row = None
    for g in grupos:
        if str(g.get("grupo_id", "")).strip() == grupo_id:
            grupo_row = g
            break

    if not grupo_row:
        return None

    integrantes_rows = [
        r for r in ws_integrantes.get_all_records()
        if str(r.get("grupo_id", "")).strip() == grupo_id
    ]

    entregas_rows = [
        r for r in ws_entregas.get_all_records()
        if str(r.get("grupo_id", "")).strip() == grupo_id
    ]

    integrantes = [r["integrante"] for r in integrantes_rows if str(r.get("integrante", "")).strip()]

    seguimiento = {}
    for r in integrantes_rows:
        nombre = str(r.get("integrante", "")).strip()
        if not nombre:
            continue
        seguimiento[nombre] = {
            "xp_epistemico": int(float(r["xp_epistemico"])) if str(r.get("xp_epistemico", "")).strip() else 0,
            "participacion": float(r["participacion"]) if str(r.get("participacion", "")).strip() else 0.0,
        }

    entregas = {
        "f1_pre_registro": None,
        "f2_protocolo": None,
        "f3_informe": None,
        "f3_juguete": None,
        "f4_diseno_exp": None,
        "f5_informe_final": None,
    }

    for r in entregas_rows:
        entrega_id = str(r.get("entrega_id", "")).strip()
        contenido = r.get("contenido_json", "")
        if entrega_id:
            entregas[entrega_id] = json.loads(contenido) if contenido else None

    perfil_grupal_json = grupo_row.get("perfil_grupal_json", "")
    casos_resueltos_json = grupo_row.get("casos_resueltos_json", "")

    perfil_grupal = json.loads(perfil_grupal_json) if perfil_grupal_json else {
        "racha": 1,
        "identidad_puntos": {
            "experimental": 0,
            "aplicada": 0,
            "desarrollo": 0,
            "procesamiento": 0,
        },
    }

    casos_resueltos = json.loads(casos_resueltos_json) if casos_resueltos_json else []

    return {
        "grupo": {
            "grupo_id": grupo_row["grupo_id"],
            "nombre_grupo": grupo_row["nombre_grupo"],
            "integrantes": integrantes,
        },
        "perfil_grupal": perfil_grupal,
        "progreso": {
            "xp_mision": int(float(grupo_row["xp_mision"])) if str(grupo_row.get("xp_mision", "")).strip() else 0,
            "xp_epistemico_grupal": int(float(grupo_row["xp_epistemico_grupal"])) if str(grupo_row.get("xp_epistemico_grupal", "")).strip() else 0,
            "fase_actual": int(float(grupo_row["fase_actual"])) if str(grupo_row.get("fase_actual", "")).strip() else 1,
        },
        "seguimiento_individual": seguimiento,
        "entregas": entregas,
        "casos_resueltos": casos_resueltos,
    }


def load_all_group_ids():
    ensure_headers()
    grupos_rows = ws_grupos.get_all_records()
    ids = []
    vistos = set()

    for row in grupos_rows:
        grupo_id = str(row.get("grupo_id", "")).strip()
        if grupo_id and grupo_id not in vistos:
            vistos.add(grupo_id)
            ids.append(grupo_id)

    return ids