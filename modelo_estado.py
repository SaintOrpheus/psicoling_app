import re
import streamlit as st


DATA_DIR = "data/usuarios"



def slugify(texto: str) -> str:
    texto = texto.strip().lower()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r"[^a-z0-9_áéíóúñü]", "", texto)
    return texto



def inicializar_grupo(grupo_id: str = "G00", integrantes=None) -> dict:
    if integrantes is None:
        integrantes = []

    return {
        "grupo": {
            "grupo_id": grupo_id,
            "nombre_grupo": grupo_id,
            "integrantes": integrantes,
        },
        "perfil_grupal": {
            "racha": 1,
            "identidad_puntos": {
                "experimental": 0,
                "aplicada": 0,
                "desarrollo": 0,
                "procesamiento": 0,
            },
        },
        "progreso": {
            "xp_mision": 0,
            "xp_epistemico_grupal": 0,
            "fase_actual": 1,
        },
        "seguimiento_individual": {
            integrante: {
                "xp_epistemico": 0,
                "participacion": 0.0,
            }
            for integrante in integrantes
        },
        "entregas": {
            "f1_pre_registro": None,
            "f2_protocolo": None,
            "f3_informe": None,
            "f3_juguete": None,
            "f4_diseno_exp": None,
            "f5_informe_final": None,
        },
        "casos_resueltos": [],
    }



def get_group_path(grupo_id: str) -> str:
    return f"{DATA_DIR}/{slugify(grupo_id)}_progress.json"



def fusionar_grupo_con_base(datos_cargados: dict) -> dict:
    grupo_id = datos_cargados.get("grupo", {}).get("grupo_id", "G00")
    integrantes = datos_cargados.get("grupo", {}).get("integrantes", [])
    base = inicializar_grupo(grupo_id, integrantes)

    for clave, valor in datos_cargados.items():
        if isinstance(valor, dict) and clave in base:
            base[clave].update(valor)
        else:
            base[clave] = valor

    if "perfil_grupal" in datos_cargados and "identidad_puntos" in datos_cargados["perfil_grupal"]:
        base["perfil_grupal"]["identidad_puntos"].update(
            datos_cargados["perfil_grupal"]["identidad_puntos"]
        )

    if "entregas" in datos_cargados:
        base["entregas"].update(datos_cargados["entregas"])

    if "seguimiento_individual" in datos_cargados:
        base["seguimiento_individual"].update(datos_cargados["seguimiento_individual"])

    return base



def init_session_state() -> None:
    if "grupo_actual" not in st.session_state:
        st.session_state.grupo_actual = inicializar_grupo()

    if "miembro_actual" not in st.session_state:
        st.session_state.miembro_actual = None

    if "perfil_acceso" not in st.session_state:
        st.session_state.perfil_acceso = None

    if "docente_autenticado" not in st.session_state:
        st.session_state.docente_autenticado = False
