import streamlit as st
import pandas as pd

from persistencia import load_group_data, get_all_group_ids
from modelo_estado import fusionar_grupo_con_base, inicializar_grupo


def calcular_identidad_desde_perfil(perfil_grupal: dict) -> str:
    p = perfil_grupal.get("identidad_puntos", {})
    if sum(p.values()) == 0:
        return "Investigación en Formación"
    max_val = max(p, key=p.get)
    mapeo = {
        "experimental": "Experimentalista",
        "aplicada": "Psicología Aplicada",
        "desarrollo": "Especialista en Desarrollo",
        "procesamiento": "Arquitectura del Lenguaje",
    }
    return mapeo.get(max_val, "Trayecto Generalista")


def inferir_fase(entregas: dict) -> int:
    if entregas.get("f5_informe_final"):
        return 5
    if entregas.get("f4_diseno_exp"):
        return 4
    if entregas.get("f3_juguete") or entregas.get("f3_informe"):
        return 3
    if entregas.get("f2_protocolo"):
        return 2
    if entregas.get("f1_pre_registro"):
        return 1
    return 0


def cerrar_sesion_docente() -> None:
    st.session_state.docente_autenticado = False
    st.session_state.grupo_actual = inicializar_grupo()
    st.session_state.miembro_actual = None
    st.session_state.perfil_acceso = None
    st.rerun()


def render_docente() -> None:
    st.title("⚙️ Consola Docente")

    if not st.session_state.docente_autenticado:
        clave_ingresada = st.text_input("Clave docente:", type="password")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Entrar", width="stretch"):
                if clave_ingresada == "profesor_vallejo":
                    st.session_state.docente_autenticado = True
                    st.rerun()
                else:
                    st.error("Clave incorrecta.")
        with col2:
            if st.button("Volver", width="stretch"):
                st.session_state.docente_autenticado = False
                st.session_state.perfil_acceso = None
                st.rerun()
        st.stop()

    grupos = []
    individuos = []

    for grupo_id in get_all_group_ids():
        datos = load_group_data(grupo_id)
        if not datos:
            continue

        g = fusionar_grupo_con_base(datos)

        entregas = g.get("entregas", {})
        progreso = g.get("progreso", {})
        grupo = g.get("grupo", {})
        perfil_grupal = g.get("perfil_grupal", {})
        seguimiento_individual = g.get("seguimiento_individual", {})

        xp_m = progreso.get("xp_mision", 0)
        xp_e = progreso.get("xp_epistemico_grupal", 0)
        nota = round((xp_m / 1000) * 5, 2)

        grupos.append(
            {
                "Grupo": grupo.get("grupo_id", "---"),
                "Integrantes": ", ".join(grupo.get("integrantes", [])),
                "Fase": inferir_fase(entregas),
                "Nota": nota,
                "XP Misión": xp_m,
                "XP Ep. Grupal": xp_e,
                "Perfil": calcular_identidad_desde_perfil(perfil_grupal),
                "F1": "✅" if entregas.get("f1_pre_registro") else "❌",
                "F2": "✅" if entregas.get("f2_protocolo") else "❌",
                "F3 Informe": "✅" if entregas.get("f3_informe") else "❌",
                "F3 Juguete": "✅" if entregas.get("f3_juguete") else "❌",
                "F4": "✅" if entregas.get("f4_diseno_exp") else "❌",
                "F5": "✅" if entregas.get("f5_informe_final") else "❌",
                "Fenómeno": entregas.get("f1_pre_registro", {}).get("fenomeno", "---")
                if entregas.get("f1_pre_registro")
                else "---",
                "Juguete": entregas.get("f3_juguete", {}).get("nombre", "---")
                if entregas.get("f3_juguete")
                else "---",
                "Tipo Exp.": entregas.get("f4_diseno_exp", {}).get("tipo", "---")
                if entregas.get("f4_diseno_exp")
                else "---",
            }
        )

        for nombre, datos_ind in seguimiento_individual.items():
            individuos.append(
                {
                    "Grupo": grupo.get("grupo_id", "---"),
                    "Integrante": nombre,
                    "XP Epistémico": datos_ind.get("xp_epistemico", 0),
                    "Participación": datos_ind.get("participacion", 0.0),
                }
            )

    col1, col2 = st.columns([5, 1])
    with col1:
        st.caption("Vista administrativa del curso")
    with col2:
        if st.button("Cerrar sesión docente", width="stretch"):
            cerrar_sesion_docente()

    if grupos:
        df_grupos = pd.DataFrame(grupos)
        df_ind = pd.DataFrame(individuos)

        st.subheader("📊 Seguimiento grupal")
        st.dataframe(df_grupos, width="stretch")

        st.subheader("👤 Seguimiento individual")
        st.dataframe(df_ind, width="stretch")

        st.subheader("📈 Resumen")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Grupos", len(df_grupos))
        with c2:
            st.metric("Promedio nota grupal", round(df_grupos["Nota"].mean(), 2))
        with c3:
            promedio_xp = round(df_ind["XP Epistémico"].mean(), 1) if len(df_ind) else 0
            st.metric("Promedio XP epistémico individual", promedio_xp)

        csv_grupos = df_grupos.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar seguimiento grupal",
            data=csv_grupos,
            file_name="seguimiento_grupal.csv",
            mime="text/csv",
        )

        csv_ind = df_ind.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar seguimiento individual",
            data=csv_ind,
            file_name="seguimiento_individual.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay grupos registrados todavía.")

    st.stop()
