import streamlit as st
import os
from datetime import datetime

from modelo_estado import inicializar_grupo, init_session_state
from ui_docente import render_docente
from ui_estudiante import render_estudiante

st.set_page_config(page_title="Psycholinguistics Lab :)", layout="wide", page_icon="🧪")

DATA_DIR = "data/usuarios"
os.makedirs(DATA_DIR, exist_ok=True)

st.markdown(
    """
    <style>
    .badge { padding: 5px 12px; border-radius: 15px; color: white; font-weight: bold; font-size: 0.8rem; }
    .incipiente { background-color: #f44336; }
    .adecuada { background-color: #ff9800; }
    .solida { background-color: #4caf50; }
    .sofisticada { background-color: #00bcd4; }
    .status-bar {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        border: 1px solid #d1d5db;
        margin-bottom: 25px;
    }
    .commitment-box {
        background-color: #e8eef9;
        border-left: 4px solid #3b82f6;
        padding: 10px 12px;
        margin-top: 12px;
        border-radius: 6px;
        color: #1f2937;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_session_state()

if st.session_state.perfil_acceso is None:
    st.title("🧠 Psycholinguistics Lab")
    st.subheader("Selecciona tu perfil de acceso")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 👥 Estudiante")
        st.write("Ingresa al laboratorio con tu grupo de trabajo.")
        if st.button("Ingresar como estudiante", width="stretch"):
            st.session_state.docente_autenticado = False
            st.session_state.grupo_actual = inicializar_grupo()
            st.session_state.miembro_actual = None
            st.session_state.perfil_acceso = "estudiante"
            st.rerun()

    with col2:
        st.markdown("### 👨‍🏫 Docente")
        st.write("Accede a la consola de seguimiento y evaluación.")
        if st.button("Ingresar como docente", width="stretch"):
            st.session_state.grupo_actual = inicializar_grupo()
            st.session_state.miembro_actual = None
            st.session_state.docente_autenticado = False
            st.session_state.perfil_acceso = "docente"
            st.rerun()

    st.stop()

if st.session_state.perfil_acceso == "docente":
    render_docente()

if st.session_state.perfil_acceso == "estudiante":
    render_estudiante()

st.divider()
st.caption(f"Psycholinguistics Lab v4.1 | {datetime.now().year} | Universidad de Antioquia")
