import streamlit as st

from persistencia import save_group_data, load_group_data
from modelo_estado import inicializar_grupo, fusionar_grupo_con_base

def normalizar_grupo(grupo_id):
    if not grupo_id:
        return ""
    grupo_id = grupo_id.strip().upper()
    if not grupo_id.startswith("G"):
        grupo_id = f"G{grupo_id}"
    return grupo_id

def ganar_xp(mision: int = 0, epistemico: int = 0, miembro=None):
    st.session_state.grupo_actual["progreso"]["xp_mision"] = min(
        st.session_state.grupo_actual["progreso"]["xp_mision"] + mision, 1000
    )
    st.session_state.grupo_actual["progreso"]["xp_epistemico_grupal"] += epistemico

    miembro_efectivo = miembro or st.session_state.miembro_actual
    if miembro_efectivo:
        if miembro_efectivo not in st.session_state.grupo_actual["seguimiento_individual"]:
            st.session_state.grupo_actual["seguimiento_individual"][miembro_efectivo] = {
                "xp_epistemico": 0,
                "participacion": 0.0,
            }
        st.session_state.grupo_actual["seguimiento_individual"][miembro_efectivo]["xp_epistemico"] += epistemico

    save_group_data(st.session_state.grupo_actual)

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

def calcular_identidad_grupal() -> str:
    return calcular_identidad_desde_perfil(st.session_state.grupo_actual["perfil_grupal"])

def obtener_compromiso_activo() -> str:
    entregas = st.session_state.grupo_actual["entregas"]

    if entregas["f4_diseno_exp"]:
        hip = entregas["f4_diseno_exp"].get("hipotesis", "")
        if hip:
            return f"🔬 Hipótesis experimental: {hip[:120]}{'...' if len(hip) > 120 else ''}"

    if entregas["f1_pre_registro"]:
        fenomeno = entregas["f1_pre_registro"].get("fenomeno", "")
        if fenomeno:
            return f"👶 Foco de observación: {fenomeno}"

    return "🌱 Fase de exploración inicial"

def barra_estatus() -> None:
    grupo = st.session_state.grupo_actual
    xp_m = grupo["progreso"]["xp_mision"]
    xp_e = grupo["progreso"]["xp_epistemico_grupal"]
    identidad = calcular_identidad_grupal()
    nota_est = round((xp_m / 1000) * 5, 1)
    compromiso = obtener_compromiso_activo()
    miembro = st.session_state.miembro_actual or "---"

    st.markdown(
        f"""
        <div class="status-bar">
            <div style="display: flex; justify-content: space-between; align-items: center; color: #111827; font-size: 1.1rem; font-weight: 600; gap: 20px; flex-wrap: wrap;">
                <div><b>👥 Grupo:</b> {grupo['grupo']['grupo_id']} | <b>👤 Miembro activo:</b> {miembro} | <b>🆔 Perfil:</b> {identidad}</div>
                <div><b>🎓 Nota Est.:</b> {nota_est} | <b>✨ XP Epistémico grupal:</b> {xp_e}</div>
            </div>
            <div class="commitment-box">
                <b>📍 Compromiso actual:</b> {compromiso}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(xp_m / 1000, text=f"Progreso evaluativo grupal ({xp_m}/1000 XP)")

def cerrar_sesion_estudiante() -> None:
    save_group_data(st.session_state.grupo_actual)
    st.session_state.grupo_actual = inicializar_grupo()
    st.session_state.miembro_actual = None
    st.session_state.perfil_acceso = None
    st.rerun()


def render_acceso_estudiante() -> None:
    st.title("🧠 Psycholinguistics Lab: Acceso Grupal")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Volver", width="stretch", key="btn_volver_acceso_estudiante"):
            st.session_state.docente_autenticado = False
            st.session_state.perfil_acceso = None
            st.rerun()

    modo = st.radio(
        "Modo de acceso:",
        ["Ingresar a grupo existente", "Crear grupo nuevo"],
        key="modo_acceso_estudiante",
    )

    if modo == "Ingresar a grupo existente":
        grupo_id = st.text_input(
            "Código de grupo (ej. G01)",
            key="login_grupo_id",
        )
        miembro = st.text_input(
            "Tu nombre",
            key="login_miembro",
        )

        if st.button("Entrar al Laboratorio", key="btn_entrar_laboratorio"):
            grupo_id_limpio = normalizar_grupo(grupo_id)
            miembro_limpio = miembro.strip()

            if not grupo_id_limpio:
                st.error("Escribe el código del grupo.")
            elif not miembro_limpio:
                st.error("Escribe tu nombre.")
            else:
                datos = load_group_data(grupo_id_limpio)

                if not datos:
                    st.error("Ese grupo no existe. Verifica el código o crea un grupo nuevo.")
                else:
                    st.session_state.perfil_acceso = "estudiante"
                    st.session_state.docente_autenticado = False
                    st.session_state.grupo_actual = fusionar_grupo_con_base(datos)

                    if miembro_limpio not in st.session_state.grupo_actual["grupo"]["integrantes"]:
                        st.session_state.grupo_actual["grupo"]["integrantes"].append(miembro_limpio)

                    if miembro_limpio not in st.session_state.grupo_actual["seguimiento_individual"]:
                        st.session_state.grupo_actual["seguimiento_individual"][miembro_limpio] = {
                            "xp_epistemico": 0,
                            "participacion": 0.0,
                        }

                    st.session_state.miembro_actual = miembro_limpio
                    save_group_data(st.session_state.grupo_actual)
                    st.rerun()

    else:
        grupo_id = st.text_input(
            "Nuevo código de grupo (ej. G01)",
            key="crear_grupo_id",
        )
        integrantes_texto = st.text_area(
            "Integrantes iniciales, uno por línea",
            key="crear_integrantes",
        )
        miembro = st.text_input(
            "Tu nombre",
            key="crear_miembro",
        )

        if st.button("Crear grupo y entrar", key="btn_crear_grupo_entrar"):
            grupo_id_limpio = normalizar_grupo(grupo_id)
            miembro_limpio = miembro.strip()
            integrantes = [x.strip() for x in integrantes_texto.splitlines() if x.strip()]

            if miembro_limpio and miembro_limpio not in integrantes:
                integrantes.append(miembro_limpio)

            if not grupo_id_limpio:
                st.error("Escribe un código de grupo, por ejemplo G01.")
            elif grupo_id_limpio == "G00":
                st.error("G00 está reservado por el sistema. Usa otro código de grupo, por ejemplo G01.")
            elif not miembro_limpio:
                st.error("Escribe tu nombre para entrar como miembro activo.")
            elif not integrantes:
                st.error("Agrega al menos un integrante del grupo.")
            elif load_group_data(grupo_id_limpio):
                st.error("Ese código de grupo ya existe. Puedes ingresar al grupo existente.")
            else:
                st.session_state.perfil_acceso = "estudiante"
                st.session_state.docente_autenticado = False
                st.session_state.grupo_actual = inicializar_grupo(grupo_id_limpio, integrantes)
                st.session_state.miembro_actual = miembro_limpio
                save_group_data(st.session_state.grupo_actual)
                st.rerun()

    st.stop()


def render_sidebar_estudiante():
    with st.sidebar:
        st.title("🚀 Misiones")
        st.caption(f"Grupo activo: {st.session_state.grupo_actual['grupo']['grupo_id']}")
        st.caption(f"Miembro activo: {st.session_state.miembro_actual}")

        fase = st.radio(
            "Sprints Semanales:",
            [
                "Semana 1: Aprender a ver el lenguaje",
                "Semana 2: Desarrollo del Lenguaje",
                "Semana 3: El Código y la Gran Síntesis",
                "Semana 4: Diseño Experimental",
                "Semana 5: Lab Final y Cierre",
            ],
        )

        st.divider()

        with st.expander("👩‍🔬👨‍🔬 Integrantes del grupo"):
            for integrante in st.session_state.grupo_actual["grupo"]["integrantes"]:
                st.write(f"- {integrante}")

        with st.expander("📂 Resumen del Trayecto"):
            e = st.session_state.grupo_actual.get("entregas", {})
            fenomeno = e.get("f1_pre_registro", {}).get("fenomeno", "---") if e.get("f1_pre_registro") else "---"
            sujeto = e.get("f2_protocolo", {}).get("caso_unico", "---") if e.get("f2_protocolo") else "---"
            juguete = e.get("f3_juguete", {}).get("nombre", "---") if e.get("f3_juguete") else "---"
            vi_exp = e.get("f4_diseno_exp", {}).get("vi", "---") if e.get("f4_diseno_exp") else "---"

            st.write(f"**1. Fenómeno:** {fenomeno}")
            st.write(f"**2. Sujeto:** {sujeto}")
            st.write(f"**3. Juguete:** {juguete}")
            st.write(f"**4. VI Exp.:** {vi_exp}")

        if st.button("Cerrar Sesión"):
            cerrar_sesion_estudiante()

    return fase


def render_semana_1():
    st.title("🔬 Semana 1: Aprender a ver el lenguaje")
    st.info(
        "Bienvenido al laboratorio, Investigador Junior. En esta fase debes definir qué vas a observar, desde qué idea inicial y en qué contexto. Lo que selles aquí orientará tu trabajo de campo."
    )

    entregas = st.session_state.grupo_actual["entregas"]
    pre_existente = entregas.get("f1_pre_registro")

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🧬 Expediente 01: Homo loquens y las propiedades del lenguaje"):
        st.markdown(
            """
            **El lenguaje humano es único.** Las adaptaciones anatómicas (como el descenso de la laringe y la especialización del cerebro en las áreas de Broca y Wernicke) nos permiten usar el canal vocal-auditivo.

            Según Hockett, nuestro sistema se distingue de la comunicación animal por propiedades clave:
            * **Productividad:** Capacidad infinita de crear mensajes nuevos que nunca antes habíamos escuchado.
            * **Arbitrariedad:** Relación convencional y no natural entre el sonido y el significado.
            * **Desplazamiento:** Capacidad de hablar de hechos ajenos al presente (pasado, futuro o ficción).
            * **Doble articulación (Dualidad):** Nivel de sonidos sin significado que se combinan para crear formas con significado.
            """
        )

        propiedad = st.selectbox(
            "¿Qué propiedad lingüística le permite a un niño de 4 años relatar un sueño que tuvo anoche sobre un dinosaurio?",
            ["Selecciona...", "Productividad", "Desplazamiento", "Arbitrariedad"],
            key="s1_propiedad",
        )
        if propiedad == "Desplazamiento" and "s1_prop" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto. Aquí aparece la capacidad de referirse a hechos no presentes.")
            ganar_xp(epistemico=10)
            st.session_state.grupo_actual["casos_resueltos"].append("s1_prop")
            save_group_data(st.session_state.grupo_actual)

    with st.expander("⚖️ Expediente 02: ¿Adquisición, Aprendizaje o Construcción?"):
        st.markdown(
            """
            Identifica tu postura teórica antes de observar:
            * **Adquisición:** Perspectiva innatista. El niño incorpora una gramática estable y preexistente gracias a una capacidad genética.
            * **Aprendizaje:** Implica operaciones mentales formales accesibles a la conciencia (más vinculado a la instrucción formal).
            * **Construcción:** Perspectiva socio-constructivista. El niño hace uso de los recursos del ambiente asumiendo un rol de agente activo para armar su gramática en y para la comunicación.
            """
        )

        respuesta = st.radio(
            "Si al observar al niño te centras en cómo interactúa con el entorno y cómo usa los recursos para lograr sus planes comunicativos, tu visión se alinea más con:",
            ["Selecciona...", "La Adquisición innata (Déficit/Norma)", "La Construcción (Agencia/Comunicabilidad)"],
            key="s1_postura",
        )
        if (
            respuesta == "La Construcción (Agencia/Comunicabilidad)"
            and "s1_acq" not in st.session_state.grupo_actual["casos_resueltos"]
        ):
            st.success("Correcto. Esa postura favorece una observación menos patologizante.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s1_acq")
            save_group_data(st.session_state.grupo_actual)

    st.markdown("## 🔬 Taller Metodológico")
    with st.expander("📄 La ilusión del dato crudo"):
        st.markdown(
            """
            **Observar no es lo mismo que diagnosticar.**
            En la investigación, el evento comunicativo en vivo no es todavía el dato analizable. Al usar medios de registro y transcribir, produces una **representación mediada** que ya organiza la realidad según tus intereses teóricos.
            """
        )
        texto_analisis = st.text_area(
            "Reflexión de laboratorio: ¿Por qué incluir pausas, entonación o gestos en tu registro ya implica una decisión teórica?",
            key="s1_reflexion",
        )
        if st.button("Enviar análisis a la bitácora", key="btn_s1_reflexion"):
            if len(texto_analisis.strip()) > 50:
                ganar_xp(epistemico=20)
                st.success("Reflexión registrada.")
            else:
                st.warning("Tu respuesta todavía es muy breve para justificar una decisión metodológica.")

    st.divider()
    st.markdown("## 🎯 Misión: Pre-registro del diseño observacional (15%)")
    st.info(
        "Aquí defines tu primer compromiso metodológico. En la siguiente fase tendrás que convertir esta decisión en categorías observables y procedimiento de registro."
    )

    if pre_existente:
        st.success("✅ Ya tienes un pre-registro sellado.")
        st.markdown("### 🧾 Compromiso actual")
        st.write(f"**Foco de observación:** {pre_existente.get('fenomeno', '---')}")
        st.write(f"**Hipótesis inicial:** {pre_existente.get('hipotesis', '---')}")
        st.write(f"**Caso anticipado:** {pre_existente.get('sujeto', '---')}")
        st.write(f"**Contexto:** {pre_existente.get('contexto', '---')}")
        st.write(f"**Rol del observador:** {pre_existente.get('rol', '---')}")
        st.caption("Este compromiso será retomado en la siguiente fase para construir el protocolo de observación.")

    else:
        with st.form("pre_registro_fase1"):
            st.subheader("1. Foco de observación")
            fenomeno = st.text_input(
                "Fenómeno lingüístico a observar (ej. simplificación fonológica, sobreextensión semántica)"
            )
            justificacion = st.text_area(
                "Justificación psicolingüística: ¿por qué vale la pena observar este fenómeno?"
            )
            tipo_pregunta = st.selectbox("Forma de tu compromiso inicial", ["Hipótesis", "Pregunta de investigación"])
            hipotesis = st.text_area("Escribe tu hipótesis o pregunta guía")

            st.subheader("2. Escenario de observación")
            posible_sujeto = st.text_input("Caso único previsto (ej. sobrino de 3 años, vecina de 4 años)")
            contexto = st.text_input("Contexto sociocomunicativo (ej. juego libre en casa, rutina en el parque)")
            rol_obs = st.selectbox("Rol como observador", ["Participante interactuante", "Observador periférico pasivo"])

            st.subheader("3. Conciencia metodológica")
            mediacion = st.selectbox(
                "¿Qué aspecto de tu futura observación crees que requerirá más cuidado en el registro?",
                ["Selecciona...", "Pausas y silencios", "Entonación", "Gestos y mirada", "Turnos de habla", "Aún no lo sé"],
            )

            enviar = st.form_submit_button("Sellar Pre-registro de Investigación")

            if enviar:
                fenomeno_limpio = fenomeno.strip()
                justificacion_limpia = justificacion.strip()
                hipotesis_limpia = hipotesis.strip()
                sujeto_limpio = posible_sujeto.strip()
                contexto_limpio = contexto.strip()

                problemas = []
                terminos_genericos = ["lenguaje", "habla", "comunicación", "comunicacion"]

                if not fenomeno_limpio:
                    problemas.append("Debes definir un fenómeno lingüístico.")
                elif fenomeno_limpio.lower() in terminos_genericos:
                    problemas.append("El fenómeno es demasiado amplio. Delimítalo mejor.")
                if not justificacion_limpia or len(justificacion_limpia) < 30:
                    problemas.append("La justificación debe estar mejor argumentada.")
                if not hipotesis_limpia or len(hipotesis_limpia) < 30:
                    problemas.append("La hipótesis o pregunta debe estar mejor formulada.")
                if not sujeto_limpio:
                    problemas.append("Debes anticipar un caso único.")
                if not contexto_limpio:
                    problemas.append("Debes definir un contexto de observación.")
                if mediacion == "Selecciona...":
                    problemas.append("Debes identificar al menos un aspecto que exigirá cuidado en el registro.")

                if problemas:
                    for p in problemas:
                        st.error(p)
                else:
                    st.session_state.grupo_actual["entregas"]["f1_pre_registro"] = {
                        "fenomeno": fenomeno_limpio,
                        "justificacion": justificacion_limpia,
                        "tipo_compromiso": tipo_pregunta,
                        "hipotesis": hipotesis_limpia,
                        "sujeto": sujeto_limpio,
                        "contexto": contexto_limpio,
                        "rol": rol_obs,
                        "mediacion": mediacion,
                    }
                    ganar_xp(mision=150)
                    st.success("✅ Pre-registro sellado. En la siguiente fase tendrás que volver esta idea observable.")
                    st.balloons()
                    st.rerun()


def render_semana_2():
    st.title("🧠 Semana 2: Desarrollo del Lenguaje y Trabajo de Campo")
    st.info(
        "En esta fase debes convertir tu compromiso inicial en un protocolo de observación claro, replicable y coherente con lo que sellaste en la fase anterior."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🗣️ Expediente 03: Dimensiones del lenguaje infantil"):
        st.markdown(
            """
            **La evolución de la forma y el sentido:**
            Al observar el habla infantil, notarás grandes diferencias respecto al modelo adulto. Estas no son fallas, sino **estrategias naturales de aproximación**:
            * **Fonético-Fonológico:** Los niños usan *procesos de simplificación*, como reducir sílabas (decir "pato" por "zapato") o asimilar sonidos.
            * **Léxico-Semántico:** Experimentan la *sobreextensión* (usar una palabra para referirse a otras con características similares, ej. decirle "perro" a una vaca) y *sobrerrestricción*.
            * **Morfosintáctico:** Evolucionan desde la *holofrase* hasta el habla telegráfica.
            """
        )

        fenomeno = st.radio(
            "Si observas que un niño de 18 meses le dice 'guau guau' a un caballo, ¿qué fenómeno lingüístico estás presenciando?",
            ["Selecciona...", "Un proceso de simplificación fonológica", "Una sobreextensión semántica", "Un error de atención conjunta"],
            key="s2_fenomeno",
        )
        if fenomeno == "Una sobreextensión semántica" and "s2_sobreext" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto. Aquí no ves un 'error' aislado, sino una estrategia de categorización.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s2_sobreext")
            save_group_data(st.session_state.grupo_actual)

    with st.expander("⚠️ Expediente 04: Hitos del desarrollo y el riesgo de patologizar"):
        st.markdown(
            """
            **Observar ≠ Diagnosticar.**
            Los referentes del desarrollo son trayectorias generales, no normas rígidas. En psicolingüística, el objetivo es **describir recursos, estrategias y comunicabilidad**, no comparar al niño con un ideal adulto para detectar déficit.
            """
        )

        postura = st.radio(
            "Si grabas a un niño de 2 años y medio diciendo 'ota auto' (otro auto), tu rol metodológico debe ser:",
            ["Selecciona...", "Diagnosticar un retraso del lenguaje por falta de concordancia gramatical.", "Registrarlo como un dato de consolidación morfosintáctica sin patologizar."],
            key="s2_postura",
        )
        if (
            postura == "Registrarlo como un dato de consolidación morfosintáctica sin patologizar."
            and "s2_patolog" not in st.session_state.grupo_actual["casos_resueltos"]
        ):
            st.success("Correcto. Tu tarea aquí es describir procesos, no cerrar un juicio clínico.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s2_patolog")
            save_group_data(st.session_state.grupo_actual)

    st.markdown("## 🔧 Operacionalización del diseño")
    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    proto_existente = st.session_state.grupo_actual["entregas"].get("f2_protocolo")

    if not pre:
        st.warning("Debes completar y sellar el pre-registro de la fase anterior para habilitar esta fase.")
    else:
        st.markdown("### 🧾 Compromiso recuperado de la Fase 1")
        st.write(f"**Fenómeno:** {pre.get('fenomeno', '---')}")
        st.write(f"**{pre.get('tipo_compromiso', 'Hipótesis')}:** {pre.get('hipotesis', '---')}")
        st.write(f"**Caso anticipado:** {pre.get('sujeto', '---')}")
        st.write(f"**Contexto inicial:** {pre.get('contexto', '---')}")
        st.write(f"**Aspecto de mediación a cuidar:** {pre.get('mediacion', '---')}")
        st.caption("Ahora debes convertir este compromiso en categorías observables, instrumento y procedimiento.")

        if proto_existente:
            st.success("✅ Ya tienes un protocolo operativo sellado.")
            st.markdown("### 📋 Protocolo actual")
            st.write(f"**Caso único:** {proto_existente.get('caso_unico', '---')} ({proto_existente.get('edad_caso', '---')})")
            st.write(f"**Objetivo:** {proto_existente.get('objetivo', '---')}")
            st.write(f"**Instrumento:** {proto_existente.get('instrumento', '---')}")
            st.write(f"**Marco de referencia:** {proto_existente.get('baremos', '---')}")
            st.write(f"**Puente con Fase 1:** {proto_existente.get('puente_pre', '---')}")
            st.caption("En la siguiente fase tendrás que usar este protocolo para producir y analizar datos.")

        else:
            sugerencia_instrumento = {
                "Pausas y silencios": "Grabación de Audio (Voz)",
                "Entonación": "Grabación de Audio (Voz)",
                "Gestos y mirada": "Grabación de Video (Gestos + Voz)",
                "Turnos de habla": "Grabación de Video (Gestos + Voz)",
                "Aún no lo sé": "Diario de campo / Notas en vivo",
            }.get(pre.get("mediacion", "Aún no lo sé"), "Diario de campo / Notas en vivo")

            with st.form("form_s2_protocolo"):
                st.subheader("1. Caso único y contexto real")
                col1, col2 = st.columns(2)
                with col1:
                    c_u = st.text_input("Seudónimo o iniciales del niño/a")
                with col2:
                    e_c = st.text_input("Edad exacta (años y meses)")
                ctx = st.text_area("Contexto exacto de observación")

                st.subheader("2. Traducción del pre-registro en método")
                puente_pre = st.text_area(
                    "Explica en una frase cómo este protocolo responde al fenómeno y a la hipótesis que sellaste en la Fase 1."
                )
                obj = st.text_input("Objetivo de la observación")

                col3, col4 = st.columns(2)
                with col3:
                    instrumento = st.selectbox(
                        "Instrumento de mediación y registro",
                        ["Grabación de Audio (Voz)", "Grabación de Video (Gestos + Voz)", "Diario de campo / Notas en vivo"],
                        index=["Grabación de Audio (Voz)", "Grabación de Video (Gestos + Voz)", "Diario de campo / Notas en vivo"].index(sugerencia_instrumento),
                    )
                with col4:
                    baremos = st.selectbox(
                        "Marco de referencia del desarrollo",
                        ["Guía UNICEF (Vigilancia e Hitos)", "Manual PUC (Clínico-Funcional)", "Ambos"],
                    )

                st.caption(f"Sugerencia recuperada de Fase 1 según tu mediación prioritaria: **{sugerencia_instrumento}**")

                cat = st.text_area(
                    "Categorías y criterios de observación (¿qué contará exactamente como una ocurrencia en tus datos?)"
                )
                proc = st.text_area(
                    "Procedimiento paso a paso (ej. preparar registro, iniciar interacción, registrar, transcribir, organizar ocurrencias)"
                )

                enviar_proto = st.form_submit_button("Guardar y sellar protocolo operativo")

                if enviar_proto:
                    problemas = []

                    if not c_u.strip():
                        problemas.append("Debes identificar un caso único.")
                    if not e_c.strip():
                        problemas.append("Debes registrar la edad exacta del caso.")
                    if not ctx.strip():
                        problemas.append("Debes describir el contexto real de observación.")
                    if len(puente_pre.strip()) < 30:
                        problemas.append("Debes explicar mejor cómo este protocolo se deriva del pre-registro.")
                    if len(obj.strip()) < 15:
                        problemas.append("El objetivo de observación todavía es demasiado breve.")
                    if len(cat.strip()) < 30:
                        problemas.append("Las categorías deben estar mejor definidas.")
                    if len(proc.strip()) < 30:
                        problemas.append("El procedimiento debe ser más claro y replicable.")

                    fenomeno_pre = pre.get("fenomeno", "").lower().strip()
                    if fenomeno_pre and fenomeno_pre not in (puente_pre.lower() + " " + cat.lower()):
                        problemas.append("No se ve con claridad cómo tus categorías responden al fenómeno definido en Fase 1.")

                    if pre.get("mediacion") == "Gestos y mirada" and instrumento == "Grabación de Audio (Voz)":
                        problemas.append("Elegiste priorizar gestos y mirada en Fase 1, pero el instrumento actual no los captura bien.")

                    if pre.get("mediacion") == "Turnos de habla" and instrumento == "Diario de campo / Notas en vivo":
                        problemas.append("Si quieres analizar turnos de habla, el diario de campo puede ser insuficiente sin apoyo de audio o video.")

                    if problemas:
                        for p in problemas:
                            st.error(p)
                    else:
                        st.session_state.grupo_actual["entregas"]["f2_protocolo"] = {
                            "caso_unico": c_u.strip(),
                            "edad_caso": e_c.strip(),
                            "contexto_caso": ctx.strip(),
                            "puente_pre": puente_pre.strip(),
                            "objetivo": obj.strip(),
                            "instrumento": instrumento,
                            "baremos": baremos,
                            "categorias": cat.strip(),
                            "procedimiento": proc.strip(),
                        }
                        ganar_xp(mision=200)
                        st.session_state.grupo_actual["perfil_grupal"]["identidad_puntos"]["desarrollo"] += 10
                        save_group_data(st.session_state.grupo_actual)
                        st.success("✅ Protocolo operativo sellado. En la siguiente fase tendrás que contrastar este diseño con datos reales.")
                        st.balloons()
                        st.rerun()


def render_semana_3():
    st.title("🧩 Semana 3: El Código - Caso Único y La Gran Síntesis")
    st.info(
        "En esta fase debes contrastar tu diseño con datos reales y, a partir de ese análisis, traducir tus hallazgos en una propuesta aplicada."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🪁 Expediente 05: El juego como motor cognitivo y la ZDP"):
        st.markdown(
            """
            **El juguete como herramienta cultural.**
            Según distintas teorías del desarrollo, el juego no es un complemento, sino un medio de reorganización cognitiva.
            * **Piaget:** Permite la asimilación y acomodación de la realidad.
            * **Vygotsky:** El juguete puede funcionar como andamiaje en la **Zona de Desarrollo Próximo (ZDP)**.
            """
        )

        zdp_q = st.radio(
            "Si diseñas un juguete que el niño no puede resolver por sí solo, pero sí con apoyo o con la estructura del objeto, estás operando en:",
            ["Selecciona...", "La etapa preoperacional estricta", "La Zona de Desarrollo Próximo (ZDP)"],
            key="s3_zdp",
        )
        if zdp_q == "La Zona de Desarrollo Próximo (ZDP)" and "s3_zdp" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto. Aquí el objeto no solo entretiene: estructura una posibilidad de desarrollo.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s3_zdp")
            save_group_data(st.session_state.grupo_actual)

    with st.expander("♻️ Expediente 06: Diseño Adaptativo, Identidad y Economía Circular"):
        st.markdown(
            """
            **Sustentabilidad y pertinencia cultural.**
            El diseño adaptativo exige considerar seguridad, ergonomía y contexto. También puede incorporar materiales y referencias locales para darle al objeto mayor pertinencia cultural.
            """
        )

        eco_q = st.radio(
            "¿Por qué puede ser preferible usar recursos de la región en lugar de materiales genéricos para tu prototipo?",
            ["Selecciona...", "Para reducir tiempo de fabricación y costos logísticos", "Para dotar al objeto de pertinencia cultural y aprovechar materiales disponibles"],
            key="s3_eco",
        )
        if eco_q == "Para dotar al objeto de pertinencia cultural y aprovechar materiales disponibles" and "s3_eco" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto. El diseño también comunica contexto e identidad.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s3_eco")
            save_group_data(st.session_state.grupo_actual)

    st.markdown("## 🔬 Laboratorio de Síntesis")
    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    proto = st.session_state.grupo_actual["entregas"].get("f2_protocolo")
    informe_existente = st.session_state.grupo_actual["entregas"].get("f3_informe")
    juguete_existente = st.session_state.grupo_actual["entregas"].get("f3_juguete")

    if not proto or not pre:
        st.warning("Debes tener completadas las fases anteriores para acceder a esta etapa.")
    else:
        st.markdown("### 🧾 Memoria del proceso")
        st.write(f"**Fenómeno inicial:** {pre.get('fenomeno', '---')}")
        st.write(f"**{pre.get('tipo_compromiso', 'Hipótesis')}:** {pre.get('hipotesis', '---')}")
        st.write(f"**Caso observado:** {proto.get('caso_unico', '---')} ({proto.get('edad_caso', '---')})")
        st.write(f"**Categorías previstas:** {proto.get('categorias', '---')}")
        st.caption("Ahora debes responder con datos a lo que planteaste en las fases anteriores.")

        st.markdown("### 📊 Producto 1: Informe de observación (20%)")
        st.caption("Aquí no basta describir: debes contrastar lo observado con tu compromiso inicial.")

        if informe_existente:
            st.success("✅ Ya tienes un informe de observación sellado.")
            st.write(f"**Decisión frente a la hipótesis:** {informe_existente.get('decision_hipotesis', '---')}")
            st.write(f"**Perfil observado:** {informe_existente.get('perfil', '---')[:300]}...")
            st.write(f"**Contraste empírico:** {informe_existente.get('contraste', '---')[:300]}...")
        else:
            with st.form("f3_informe"):
                perfil = st.text_area(
                    "1. Sistematización del perfil lingüístico observado (describe ocurrencias reales y organizadas según tus categorías)"
                )
                decision_hipotesis = st.selectbox(
                    "2. ¿Qué ocurrió con tu hipótesis o pregunta inicial?",
                    ["Selecciona...", "Se confirma", "Se ajusta parcialmente", "No se sostiene con los datos"],
                )
                contraste = st.text_area(
                    "3. Contraste empírico: explica tu decisión basándote en los datos recogidos"
                )
                sesgo = st.text_area(
                    "4. ¿Qué riesgo de sesgo o lectura patologizante tuviste que evitar durante el análisis?"
                )

                enviar_informe = st.form_submit_button("Sellar y entregar informe de caso")

                if enviar_informe:
                    problemas = []

                    if len(perfil.strip()) < 100:
                        problemas.append("La descripción del perfil aún es demasiado breve.")
                    if decision_hipotesis == "Selecciona...":
                        problemas.append("Debes tomar una decisión explícita frente a tu hipótesis inicial.")
                    if len(contraste.strip()) < 100:
                        problemas.append("El contraste con la hipótesis necesita más desarrollo.")
                    if len(sesgo.strip()) < 40:
                        problemas.append("Debes explicitar mejor el sesgo que evitaste o la cautela interpretativa que adoptaste.")

                    categorias_previas = proto.get("categorias", "").lower().strip()
                    if categorias_previas and not any(pal in perfil.lower() for pal in categorias_previas.split()[:3]):
                        problemas.append("No se ve con claridad la relación entre tus categorías de observación y la descripción del perfil.")

                    if problemas:
                        for p in problemas:
                            st.error(p)
                    else:
                        st.session_state.grupo_actual["entregas"]["f3_informe"] = {
                            "perfil": perfil.strip(),
                            "decision_hipotesis": decision_hipotesis,
                            "contraste": contraste.strip(),
                            "sesgo": sesgo.strip(),
                        }
                        ganar_xp(mision=200, epistemico=20)
                        save_group_data(st.session_state.grupo_actual)
                        st.success("✅ Informe sellado. Ahora puedes traducir esos hallazgos en una propuesta aplicada.")
                        st.balloons()
                        st.rerun()

        st.markdown("### 🧸 Producto 2: Juguete adaptativo (15%)")
        st.caption("El juguete debe derivarse del perfil observado. No es una idea libre: es una respuesta aplicada a tus hallazgos.")

        if not informe_existente:
            st.warning("Debes sellar primero el informe de observación para habilitar el diseño del juguete.")
        elif juguete_existente:
            st.success("✅ Ya tienes un juguete adaptativo registrado.")
            st.write(f"**Nombre:** {juguete_existente.get('nombre', '---')}")
            st.write(f"**Rasgo observado que lo inspira:** {juguete_existente.get('rasgo_inspirador', '---')}")
            st.write(f"**Justificación de caso:** {juguete_existente.get('just_caso', '---')[:300]}...")
        else:
            with st.form("f3_juguete"):
                nombre_j = st.text_input("Nombre del juguete")
                rasgo_inspirador = st.text_input(
                    "¿Qué rasgo o patrón observado en el niño inspiró directamente este diseño?"
                )

                col1, col2 = st.columns(2)
                with col1:
                    just_caso = st.text_area(
                        "Justificación de caso: ¿cómo responde este juguete al perfil observado?"
                    )
                    just_pedag = st.text_area(
                        "Justificación pedagógica: ¿cómo opera en la ZDP o favorece reorganización del lenguaje?"
                    )
                with col2:
                    diseno_ergo = st.text_area("Diseño y ergonomía: seguridad, uso, adecuación a la etapa")
                    sustentabilidad = st.text_area("Materiales, contexto y/o pertinencia cultural")

                link_j = st.text_input("Enlace a ficha visual o boceto (Drive/Canva)")

                enviar_juguete = st.form_submit_button("Entregar diseño de juguete")

                if enviar_juguete:
                    problemas = []

                    if not nombre_j.strip():
                        problemas.append("Debes nombrar el juguete.")
                    if not rasgo_inspirador.strip():
                        problemas.append("Debes indicar qué hallazgo del informe inspiró el diseño.")
                    if len(just_caso.strip()) < 60:
                        problemas.append("La justificación de caso necesita mayor desarrollo.")
                    if len(just_pedag.strip()) < 40:
                        problemas.append("Debes fundamentar mejor la dimensión pedagógica.")
                    if not link_j.strip():
                        problemas.append("Debes adjuntar un enlace a la evidencia visual del diseño.")

                    perfil_obs = (st.session_state.grupo_actual["entregas"].get("f3_informe") or {}).get("perfil", "").lower()
                    palabras_clave = rasgo_inspirador.lower().split()
                    if palabras_clave and not any(p in perfil_obs for p in palabras_clave if len(p) > 4):
                        st.warning("La relación con el informe no es evidente. Revísala.")

                    if problemas:
                        for p in problemas:
                            st.error(p)
                    else:
                        st.session_state.grupo_actual["entregas"]["f3_juguete"] = {
                            "nombre": nombre_j.strip(),
                            "rasgo_inspirador": rasgo_inspirador.strip(),
                            "just_caso": just_caso.strip(),
                            "just_pedag": just_pedag.strip(),
                            "diseno": diseno_ergo.strip(),
                            "sustentabilidad": sustentabilidad.strip(),
                            "link": link_j.strip(),
                        }
                        ganar_xp(mision=150, epistemico=25)
                        save_group_data(st.session_state.grupo_actual)
                        st.success("✅ Juguete registrado. Has traducido un hallazgo observacional en una propuesta aplicada.")
                        st.balloons()
                        st.rerun()


def render_semana_4():
    st.title("🧩 Semana 4: El Sentido - Modelos Cognitivos y Diseño Experimental")
    st.info("En esta fase dejas la observación naturalista y pasas a aislar procesos mentales en condiciones controladas.")

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🔄 Expediente 07: Producción vs. Comprensión"):
        st.markdown(
            """
            * **Comprensión:** Del estímulo al significado.
            * **Producción:** De la intención al habla.
            """
        )
        flujo = st.radio(
            "Si mides el tiempo de reconocimiento de una palabra, estás estudiando:",
            ["Selecciona...", "Producción", "Comprensión"],
            key="s4_comp",
        )
        if flujo == "Comprensión" and "s4_comp" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto.")
            ganar_xp(epistemico=10)
            st.session_state.grupo_actual["casos_resueltos"].append("s4_comp")
            save_group_data(st.session_state.grupo_actual)

    with st.expander("🏛️ Expediente 08: Modelos de procesamiento"):
        st.markdown(
            """
            * **Modular:** Serial, encapsulado.
            * **Interactivo:** Paralelo, con influencia mutua.
            """
        )
        modelo = st.radio(
            "Si el contexto ayuda a reconocer letras, apoyas un modelo:",
            ["Selecciona...", "Modular/Autónomo", "Interactivo/Conexionista"],
            key="s4_mod",
        )
        if modelo == "Interactivo/Conexionista" and "s4_mod" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Correcto.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s4_mod")
            save_group_data(st.session_state.grupo_actual)

    st.divider()
    st.markdown("## 🎯 Misión: Diseño Experimental (25%)")

    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    informe = st.session_state.grupo_actual["entregas"].get("f3_informe")

    if pre and informe:
        st.markdown("### 🧾 Memoria del proceso")
        st.write(f"**Fenómeno inicial:** {pre.get('fenomeno','---')}")
        st.write(f"**Decisión sobre hipótesis:** {informe.get('decision_hipotesis','---')}")

    tipo_exp = st.radio(
        "Origen de tu diseño experimental:",
        ["Derivado de la observación del niño", "Independiente (procesamiento en adultos)"],
        key="s4_tipo_exp",
    )

    with st.form("f4_exp"):
        if st.session_state["s4_tipo_exp"] == "Derivado de la observación del niño":
            puente = st.text_area(
                "¿Qué observaste en el niño que te llevó a formular este experimento?",
                key="s4_puente",
            )
            fundamento = ""
        else:
            fundamento = st.text_area(
                "¿Qué fenómeno del procesamiento lingüístico adulto estás modelando y por qué es relevante?",
                key="s4_fundamento",
            )

            st.selectbox(
                "Tipo de tarea experimental (opcional, orientador)",
                ["Selecciona...", "Decisión léxica", "Tiempo de lectura", "Ambigüedad semántica", "Priming", "Otro"],
                key="s4_dominio",
            )

            st.info("Aquí no necesitas conectar con el niño. Define un fenómeno cognitivo medible.")
            puente = ""

        hipotesis = st.text_area("Hipótesis experimental (direccional)")

        col1, col2 = st.columns(2)
        with col1:
            vi = st.text_input("Variable Independiente (VI) con niveles (ej. alta vs baja)")
        with col2:
            vd = st.text_input("Variable Dependiente (VD) (ej. tiempo de reacción)")

        control_vars = st.text_area("Variables de control")
        ruido = st.text_area("¿Qué podría estar midiendo otra cosa distinta a lo que crees?")

        enviar = st.form_submit_button("Registrar diseño experimental")

        if enviar:
            problemas = []

            if st.session_state["s4_tipo_exp"] == "Derivado de la observación del niño":
                if not puente or len(puente.strip()) < 30:
                    problemas.append("Debes justificar el vínculo con la observación previa.")
            else:
                if not fundamento or len(fundamento.strip()) < 30:
                    problemas.append("Debes definir claramente el fenómeno de procesamiento.")

            if len(hipotesis.strip()) < 30:
                problemas.append("Hipótesis insuficiente.")

            if not vi.strip():
                problemas.append("Define la VI.")
            elif "vs" not in vi.lower() and "," not in vi:
                st.warning("Incluye niveles en la VI (ej. alta vs baja).")

            if not vd.strip():
                problemas.append("Define la VD.")
            elif not any(p in vd.lower() for p in ["tiempo", "errores", "aciertos", "latencia"]):
                st.warning("La VD debería ser medible.")

            if len(control_vars.strip()) < 30:
                problemas.append("Debes definir controles.")

            if len(ruido.strip()) < 20:
                problemas.append("Debes anticipar al menos una fuente de ruido.")

            if problemas:
                for p in problemas:
                    st.error(p)
            else:
                st.session_state.grupo_actual["entregas"]["f4_diseno_exp"] = {
                    "tipo": st.session_state["s4_tipo_exp"],
                    "hipotesis": hipotesis,
                    "vi": vi,
                    "vd": vd,
                    "control": control_vars,
                    "ruido": ruido,
                    "puente": puente,
                    "fundamento": fundamento,
                }

                ganar_xp(mision=200, epistemico=20)
                st.session_state.grupo_actual["perfil_grupal"]["identidad_puntos"]["experimental"] += 15
                save_group_data(st.session_state.grupo_actual)
                st.success("✅ Diseño experimental registrado. En la siguiente fase trabajarás con datos.")
                st.balloons()
                st.rerun()


def render_semana_5():
    st.title("📊 Semana 5: La Síntesis - El Laboratorio Final")
    st.info(
        "Has llegado a la cumbre de tu entrenamiento, Investigador Junior. Es hora de enfrentar los datos empíricos reales, gestionar el caos metodológico y defender tus hallazgos."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("⏱️ Expediente 10: ¿Procesos o Productos? (On-line vs. Off-line)"):
        st.markdown(
            """
            **¿Cuándo medir la comprensión?**
            * **Medidas posteriores (Off-line):** Como el recuerdo libre o el reconocimiento. Apuntan al producto final o la representación mental resultante después de que la comprensión ha tenido lugar.
            * **Medidas en curso (On-line o cronométricas):** Como el registro de movimientos oculares, la ventana móvil o la decisión léxica. Permiten investigar los subprocesos en el momento en que operan, asumiendo que un mayor tiempo de reacción (milisegundos) implica una mayor carga de procesamiento.
            """
        )

        tecnica = st.radio(
            "Si tu objetivo es medir exactamente en qué milisegundo el cerebro del lector detecta una anomalía sintáctica al leer una oración, debes usar:",
            ["Selecciona...", "Una técnica Off-line (Prueba de memoria al final del texto)", "Una técnica On-line (Registro de movimientos oculares o potenciales evocados)"],
        )
        if tecnica == "Una técnica On-line (Registro de movimientos oculares o potenciales evocados)" and "s5_online" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("¡Exacto! Necesitas capturar el proceso mental en tiempo real. +15 XP Epistémico.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s5_online")
            save_group_data(st.session_state.grupo_actual)

    with st.expander("🌪️ Expediente 11: El Ruido Experimental"):
        st.markdown(
            """
            **La incertidumbre en los datos empíricos:**
            En un experimento real, a veces los tiempos de reacción son inconsistentes. Esto puede ocurrir porque:
            1. Tu técnica interrumpió el proceso natural de lectura (confusión entre la activación lingüística y las exigencias de la propia tarea experimental).
            2. Variables de confusión no controladas (fatiga, distracciones, diferencias individuales).
            El buen científico no oculta el ruido, lo audita y lo explica.
            """
        )

        ruido_sel = st.radio(
            "Si un participante tarda 4000 milisegundos en una tarea de decisión léxica donde el promedio es de 600 ms, la acción más ética metodológicamente es:",
            ["Selecciona...", "Eliminar el dato en silencio para que la hipótesis cuadre perfecta", "Auditar el valor atípico (outlier), justificar estadísticamente su exclusión y reportarlo"],
        )
        if ruido_sel == "Auditar el valor atípico (outlier), justificar estadísticamente su exclusión y reportarlo" and "s5_ruido" not in st.session_state.grupo_actual["casos_resueltos"]:
            st.success("Excelente criterio ético y metodológico. La ciencia exige transparencia. +15 XP Epistémico.")
            ganar_xp(epistemico=15)
            st.session_state.grupo_actual["casos_resueltos"].append("s5_ruido")
            save_group_data(st.session_state.grupo_actual)

    st.divider()
    st.markdown("## ⚠️ Simulación de Incertidumbre")
    st.warning("¡Alerta en el Laboratorio! El software de decisión léxica ha arrojado los siguientes tiempos de reacción (TR) para la condición experimental. Hay una anomalía evidente.")

    datos_simulados = {
        "Sujeto": [1, 2, 3, 4, 5],
        "TR (Milisegundos)": [580, 610, 4000, 595, 620],
        "Respuesta": ["Correcta", "Correcta", "Incorrecta", "Correcta", "Correcta"],
    }
    st.table(datos_simulados)

    interpretacion = st.text_area(
        "Bitácora de Laboratorio: ¿Cómo manejas el 'outlier' del Sujeto 3 en tu análisis? ¿Qué pudo haber causado este ruido metodológico?"
    )
    if st.button("Registrar Análisis Crítico del Ruido"):
        if len(interpretacion.strip()) > 50:
            st.session_state.grupo_actual["perfil_grupal"]["identidad_puntos"]["experimental"] += 15
            ganar_xp(epistemico=20)
            st.success("Rigor metodológico validado. Sabes interrogar al ruido. +20 XP Epistémico.")
            save_group_data(st.session_state.grupo_actual)
        else:
            st.error("Debes argumentar mejor tu decisión metodológica (mínimo 50 caracteres).")

    st.divider()
    st.markdown("## 🎯 Misión Final: Protocolo Experimental e Informe (20%)")
    st.caption("Cierre del ciclo investigativo. Interpreta los resultados finales de tu diseño.")

    with st.form("f5_informe_final"):
        tecnica_usada = st.selectbox(
            "Técnica instrumental justificada en el informe",
            ["Medida On-line (Cronométrica/Ventana Móvil)", "Medida Off-line (Recuerdo/Reconocimiento)", "Doble Tarea / Potenciales Evocados"],
        )
        contraste = st.text_area(
            "1. Contraste de Hipótesis (¿Los datos obtenidos confirmaron o refutaron tu pre-registro de la Semana 4?)"
        )
        discusion = st.text_area(
            "2. Discusión Crítica (Limitaciones de tu experimento, variables de confusión detectadas y posibles mejoras futuras)"
        )

        if st.form_submit_button("Entregar Informe Final y Consolidar Ciclo"):
            if len(contraste.strip()) < 80 or len(discusion.strip()) < 80:
                st.error("Un informe final requiere profundidad analítica. Amplía tus conclusiones (mínimo 80 caracteres por campo).")
            else:
                st.session_state.grupo_actual["entregas"]["f5_informe_final"] = {
                    "tecnica": tecnica_usada,
                    "contraste": contraste.strip(),
                    "discusion": discusion.strip(),
                }
                ganar_xp(mision=200, epistemico=50)
                save_group_data(st.session_state.grupo_actual)
                st.balloons()
                st.success("¡MISIÓN CUMPLIDA! Has completado el informe final y consolidado tu identidad como Erudito Psicolingüístico. +200 Mission XP.")
                st.rerun()


def render_estudiante() -> None:
    grupo = st.session_state.get("grupo_actual", {})
    grupo_id = grupo.get("grupo", {}).get("grupo_id", "G00")
    miembro = st.session_state.get("miembro_actual")

    if grupo_id == "G00" or not miembro:
        render_acceso_estudiante()

    fase = render_sidebar_estudiante()
    barra_estatus()

    if "Semana 1" in fase:
        render_semana_1()
    elif "Semana 2" in fase:
        render_semana_2()
    elif "Semana 3" in fase:
        render_semana_3()
    elif "Semana 4" in fase:
        render_semana_4()
    elif "Semana 5" in fase:
        render_semana_5()

