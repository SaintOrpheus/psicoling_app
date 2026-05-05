import streamlit as st

from persistencia import save_group_data


def ganar_xp(mision: int = 0, epistemico: int = 0, miembro=None):
    st.session_state.grupo_actual["progreso"]["xp_mision"] = min(
        st.session_state.grupo_actual["progreso"]["xp_mision"] + mision,
        1000,
    )

    st.session_state.grupo_actual["progreso"]["xp_epistemico_grupal"] += epistemico

    miembro_efectivo = miembro or st.session_state.miembro_actual

    if miembro_efectivo:
        if miembro_efectivo not in st.session_state.grupo_actual["seguimiento_individual"]:
            st.session_state.grupo_actual["seguimiento_individual"][miembro_efectivo] = {
                "xp_epistemico": 0,
                "participacion": 0.0,
            }

        st.session_state.grupo_actual["seguimiento_individual"][miembro_efectivo][
            "xp_epistemico"
        ] += epistemico

    save_group_data(st.session_state.grupo_actual)