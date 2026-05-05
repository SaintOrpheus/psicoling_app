import streamlit as st

from logica import ganar_xp
from persistencia import save_group_data


def resolver_expediente_opcion_unica(
    expediente_id,
    pregunta,
    opciones,
    respuesta_correcta,
    feedback_correcto,
    feedback_incorrecto="Respuesta registrada. Revisa el concepto antes de continuar.",
    xp_epistemico=15,
):
    """
    Renderiza un expediente de opción única.

    La respuesta solo se evalúa después de presionar "Guardar respuesta".
    Una vez guardada, queda fijada y no puede modificarse.
    """

    grupo = st.session_state.grupo_actual

    respuestas = grupo.setdefault("respuestas_expedientes", {})
    casos_resueltos = grupo.setdefault("casos_resueltos", [])

    # Si ya fue respondido, mostrar respuesta fijada
    if expediente_id in respuestas:
        respuesta_guardada = respuestas[expediente_id]["respuesta"]
        correcta = respuestas[expediente_id]["correcta"]

        st.info(f"Respuesta registrada: {respuesta_guardada}")

        if correcta:
            st.success(feedback_correcto)
        else:
            st.warning(feedback_incorrecto)

        return correcta

    # Si aún no fue respondido
    seleccion = st.radio(
        pregunta,
        opciones,
        key=f"{expediente_id}_seleccion",
    )

    if st.button("Guardar respuesta", key=f"{expediente_id}_guardar"):
        if seleccion == "Selecciona...":
            st.warning("Selecciona una opción antes de guardar.")
            return None

        correcta = seleccion == respuesta_correcta

        respuestas[expediente_id] = {
            "respuesta": seleccion,
            "correcta": correcta,
        }

        if correcta:
            ganar_xp(epistemico=xp_epistemico)

            if expediente_id not in casos_resueltos:
                casos_resueltos.append(expediente_id)

            st.success(feedback_correcto)
        else:
            st.warning(feedback_incorrecto)

        save_group_data(grupo)
        st.rerun()

    return None

def evaluar_calidad_respuesta_abierta(
    texto,
    conceptos_clave=None,
    conectores_argumentativos=None,
    acciones_metodologicas=None,
    min_caracteres=120,
    min_palabras=20,
    min_conceptos=2,
):
    texto_limpio = texto.strip().lower()

    if conceptos_clave is None:
        conceptos_clave = []

    if conectores_argumentativos is None:
        conectores_argumentativos = [
            "porque",
            "ya que",
            "debido a",
            "por lo tanto",
            "esto indica",
            "podría deberse",
            "en consecuencia",
        ]

    if acciones_metodologicas is None:
        acciones_metodologicas = [
            "revisar",
            "auditar",
            "justificar",
            "reportar",
            "excluir",
            "conservar",
            "comparar",
            "analizar",
        ]

    respuestas_vacias = [
        "no sé",
        "no se",
        "no entiendo",
        "está bien",
        "esta bien",
        "porque sí",
        "porque si",
        "ninguna",
    ]

    problemas = []

    if len(texto_limpio) < min_caracteres:
        problemas.append(f"La respuesta debe tener al menos {min_caracteres} caracteres.")

    palabras = texto_limpio.split()

    if len(palabras) < min_palabras:
        problemas.append(f"La respuesta debe tener al menos {min_palabras} palabras.")

    if any(frase in texto_limpio for frase in respuestas_vacias):
        problemas.append("La respuesta parece demasiado general o evasiva.")

    conceptos_encontrados = [
        concepto for concepto in conceptos_clave
        if concepto.lower() in texto_limpio
    ]

    if len(conceptos_encontrados) < min_conceptos:
        problemas.append(
            f"Debes usar al menos {min_conceptos} conceptos metodológicos relevantes."
        )

    if not any(conector in texto_limpio for conector in conectores_argumentativos):
        problemas.append("La respuesta necesita una explicación o justificación más clara.")

    if not any(accion in texto_limpio for accion in acciones_metodologicas):
        problemas.append("La respuesta debe incluir una decisión metodológica concreta.")

    return {
        "valida": len(problemas) == 0,
        "problemas": problemas,
        "conceptos_encontrados": conceptos_encontrados,
    }