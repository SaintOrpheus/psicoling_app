import streamlit as st

from persistencia import save_group_data, load_group_data
from modelo_estado import inicializar_grupo, fusionar_grupo_con_base
from logica import ganar_xp
from utils_expedientes import resolver_expediente_opcion_unica

def normalizar_grupo(grupo_id):
    if not grupo_id:
        return ""
    grupo_id = grupo_id.strip().upper()
    if not grupo_id.startswith("G"):
        grupo_id = f"G{grupo_id}"
    return grupo_id

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
                "Semana 2: Observación del desarrollo y análisis del caso",
                "Semana 3: Aplicación experimental: Diseño de un juguete",
                "Semana 4: Diseño Experimental",
                "Semana 5: Informe de experimento y Cierre",
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

        resolver_expediente_opcion_unica(
            expediente_id="s1_prop",
            pregunta="¿Qué propiedad lingüística le permite a un niño de 4 años relatar un sueño que tuvo anoche sobre un dinosaurio?",
            opciones=[
                "Selecciona...",
                "Productividad",
                "Desplazamiento",
                "Arbitrariedad",
                "Doble articulación",
            ],
            respuesta_correcta="Desplazamiento",
            feedback_correcto="Correcto. Aquí aparece la capacidad de referirse a hechos no presentes.",
            feedback_incorrecto="Respuesta registrada. Revisa la propiedad de desplazamiento: permite hablar de hechos no presentes, como sueños, recuerdos o ficción.",
            xp_epistemico=10,
        )

    with st.expander("⚖️ Expediente 02: ¿Adquisición, Aprendizaje o Construcción?"):
        st.markdown(
            """
            Identifica tu postura teórica antes de observar:
            * **Adquisición:** Perspectiva innatista. El niño incorpora una gramática estable y preexistente gracias a una capacidad genética.
            * **Aprendizaje:** Implica operaciones mentales formales accesibles a la conciencia (más vinculado a la instrucción formal).
            * **Construcción:** Perspectiva socio-constructivista. El niño hace uso de los recursos del ambiente asumiendo un rol de agente activo para armar su gramática en y para la comunicación.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s1_acq",
            pregunta="Si al observar al niño te centras en cómo interactúa con el entorno y cómo usa los recursos para lograr sus planes comunicativos, tu visión se alinea más con:",
            opciones=[
                "Selecciona...",
                "La Adquisición innata (Déficit/Norma)",
                "El Aprendizaje (Instrucción formal)",
                "La Construcción (Agencia/Comunicabilidad)",
            ],
            respuesta_correcta="La Construcción (Agencia/Comunicabilidad)",
            feedback_correcto="Correcto. Esa postura favorece una observación menos patologizante.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia entre adquisición, aprendizaje y construcción: aquí el énfasis está en agencia, interacción y comunicabilidad.",
            xp_epistemico=15,
        )

    with st.expander("🧪 Expediente 03: La ilusión del dato crudo"):
        st.markdown(
            """
            **Observar no es lo mismo que diagnosticar.**
            En la investigación, el evento comunicativo en vivo no es todavía el dato analizable. Al usar medios de registro y transcribir, produces una **representación mediada** que ya organiza la realidad según tus intereses teóricos.
            """
        )

        from utils_expedientes import evaluar_calidad_respuesta_abierta

        grupo = st.session_state.grupo_actual
        respuestas = grupo.setdefault("perfil_grupal", {}).setdefault("respuestas_expedientes", {})

        expediente_id = "s1_reflexion"

        if expediente_id in respuestas:
            respuesta_guardada = respuestas[expediente_id]["respuesta"]

            st.info("Ya registraste esta reflexión en la bitácora de laboratorio.")
            st.markdown(f"**Tu respuesta:** {respuesta_guardada}")

        else:
            texto_analisis = st.text_area(
                "Reflexión de laboratorio: ¿Por qué incluir pausas, entonación o gestos en tu registro ya implica una decisión teórica?",
                key="s1_reflexion_texto",
            )

            if st.button("Enviar análisis a la bitácora", key="btn_s1_reflexion"):
                resultado = evaluar_calidad_respuesta_abierta(
                    texto_analisis,
                    conceptos_clave=[
                        "pausas",
                        "entonación",
                        "entonacion",
                        "gestos",
                        "registro",
                        "transcripción",
                        "transcripcion",
                        "dato",
                        "observación",
                        "observacion",
                        "decisión teórica",
                        "decision teorica",
                        "interpretación",
                        "interpretacion",
                        "representación",
                        "representacion",
                    ],
                    acciones_metodologicas=[
                        "registrar",
                        "incluir",
                        "seleccionar",
                        "transcribir",
                        "interpretar",
                        "analizar",
                        "codificar",
                        "observar",
                        "decidir",
                        "diferenciar",
                    ],
                    min_caracteres=120,
                    min_palabras=20,
                    min_conceptos=2,
                )

                if resultado["valida"]:
                    respuestas[expediente_id] = {
                        "respuesta": texto_analisis.strip(),
                        "miembro": st.session_state.miembro_actual,
                        "conceptos_encontrados": resultado["conceptos_encontrados"],
                    }

                    ganar_xp(epistemico=20)

                    if expediente_id not in grupo.setdefault("casos_resueltos", []):
                        grupo["casos_resueltos"].append(expediente_id)

                    save_group_data(grupo)

                    st.success("Reflexión registrada. Has mostrado una comprensión metodológica de la observación como construcción del dato.")
                    st.rerun()

                else:
                    st.error("Tu respuesta aún no cumple con los criterios mínimos de reflexión metodológica.")
                    for problema in resultado["problemas"]:
                        st.warning(f"• {problema}")
                        
    with st.expander("⚗️ Expediente 04: El control del caos: Observar vs. Experimentar"):
        st.markdown(
            """
            **La ciencia tiene distintas herramientas.**

            En un experimento, el investigador manipula variables en un entorno artificial para probar causas. Sin embargo, en la observación naturalista, el investigador examina el comportamiento en las condiciones en que normalmente ocurre, sin controlarlo.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s1_obs_vs_exp",
            pregunta="¿Por qué es preferible usar la observación naturalista en lugar de un experimento formal para estudiar el uso espontáneo del lenguaje en un niño pequeño?",
            opciones=[
                "Selecciona...",
                "Porque permite manipular libremente la variable independiente para ver cómo reacciona el niño.",
                "Porque evita que la artificialidad de la situación (ej. un laboratorio o un adulto desconocido) distorsione el comportamiento real del niño.",
                "Porque es el único método que permite establecer con seguridad que una variable causó a la otra.",
            ],
            respuesta_correcta="Porque evita que la artificialidad de la situación (ej. un laboratorio o un adulto desconocido) distorsione el comportamiento real del niño.",
            feedback_correcto="Correcto. La observación naturalista permite registrar el lenguaje en condiciones habituales.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia entre observación naturalista y experimento formal: aquí se busca reducir la artificialidad del contexto.",
            xp_epistemico=15,
        )

    st.divider()
    st.markdown("## 🎯 Misión 1: Diseño observacional inicial (15%)")
    st.info(
        "Aquí sellas un compromiso metodológico suficiente para salir a campo: fenómeno, pregunta o hipótesis, caso, categorías iniciales y procedimiento mínimo. Todas las observaciones deben contar con registro en video."
    )

    proto_existente = entregas.get("f2_protocolo")

    if pre_existente and proto_existente:
        st.success("✅ Ya tienes un diseño observacional inicial sellado.")
        st.markdown("### 🧾 Compromiso actual")
        st.write(f"**Foco de observación:** {pre_existente.get('fenomeno', '---')}")
        st.write(f"**Hipótesis o pregunta inicial:** {pre_existente.get('hipotesis', '---')}")
        st.write(f"**Caso previsto:** {pre_existente.get('sujeto', '---')}")
        st.write(f"**Contexto:** {pre_existente.get('contexto', '---')}")
        st.write(f"**Rol del observador:** {pre_existente.get('rol', '---')}")
        st.write("**Registro requerido:** Video")
        st.write(f"**Categorías iniciales:** {proto_existente.get('categorias', '---')}")
        st.write(f"**Procedimiento mínimo:** {proto_existente.get('procedimiento', '---')}")
        st.caption("Este diseño orienta el trabajo de campo y el informe de observación de la siguiente semana.")

        with st.expander("🛡️ Expediente 05: La Ética y el sujeto humano"):
            st.markdown(
                """
                **¡Protocolo sellado! Pero antes de salir al campo, detente.**

                En la psicolingüística moderna, las grabaciones encubiertas o el engaño sobre los fines de la investigación ya no son prácticas aceptadas. El niño y su familia son sujetos de derechos.
                """
            )

            resolver_expediente_opcion_unica(
                expediente_id="s1_etica_sujeto",
                pregunta="Antes de encender tu grabadora de audio/video en el entorno del niño (Caso Único) que acabas de seleccionar, ¿cuál es el paso metodológico y ético innegociable que debes cumplir?",
                opciones=[
                    "Selecciona...",
                    "Asegurarte de que el niño no se dé cuenta de que está siendo grabado para que actúe de la forma más natural posible.",
                    "Obtener el consentimiento informado de sus cuidadores y garantizar el anonimato de sus datos y de su imagen.",
                    "Modificar la transcripción si el niño comete demasiados errores, para proteger su historial clínico.",
                ],
                respuesta_correcta="Obtener el consentimiento informado de sus cuidadores y garantizar el anonimato de sus datos y de su imagen.",
                feedback_correcto="Correcto. La observación con sujetos humanos exige consentimiento, transparencia y protección de identidad.",
                feedback_incorrecto="Respuesta registrada. Revisa el principio ético central: consentimiento informado, anonimato y protección de identidad.",
                xp_epistemico=15,
            )

    else:
        with st.form("pre_registro_fase1"):
            st.subheader("1. Foco de observación")
            fenomeno = st.text_input(
                "Fenómeno lingüístico a observar",
                placeholder="Ej.: simplificación fonológica, sobreextensión semántica, turnos de habla, uso de gestos"
            )
            justificacion = st.text_area(
                "Justificación psicolingüística: ¿por qué vale la pena observar este fenómeno?"
            )
            tipo_pregunta = st.selectbox(
                "Forma de tu compromiso inicial",
                ["Hipótesis", "Pregunta de investigación"]
            )
            hipotesis = st.text_area(
                "Escribe tu hipótesis o pregunta guía"
            )

            st.subheader("2. Caso y contexto de observación")
            posible_sujeto = st.text_input(
                "Caso único previsto",
                placeholder="Ej.: sobrino de 3 años, prima de 2 años, niño conocido por la familia"
            )
            contexto = st.text_input(
                "Contexto sociocomunicativo",
                placeholder="Ej.: juego libre en casa, lectura compartida, rutina de alimentación"
            )
            rol_obs = st.selectbox(
                "Rol como observador",
                ["Participante interactuante", "Observador periférico pasivo"]
            )

            st.subheader("3. Diseño mínimo de observación")
            st.caption(
                "Define solo las decisiones necesarias para salir a campo. Las categorías pueden ajustarse cuando tengas datos reales."
            )

            objetivo = st.text_input(
                "Objetivo de la observación",
                placeholder="Ej.: observar cómo el niño usa gestos y vocalizaciones para pedir objetos durante el juego"
            )

            st.info(
                "📹 Todas las observaciones deben realizarse con registro en video. Esto permitirá revisar habla, gestos, mirada, turnos e interacción."
            )

            st.markdown("#### Categorías iniciales, máximo 3")
            cat_1 = st.text_input("Categoría 1")
            crit_1 = st.text_area("¿Qué contará como dato para la categoría 1?")
            cat_2 = st.text_input("Categoría 2 (opcional)")
            crit_2 = st.text_area("¿Qué contará como dato para la categoría 2? (opcional)")
            cat_3 = st.text_input("Categoría 3 (opcional)")
            crit_3 = st.text_area("¿Qué contará como dato para la categoría 3? (opcional)")

            proc = st.text_area(
                "Procedimiento mínimo de campo",
                placeholder="Describe dónde observarás, durante cuánto tiempo, qué situación propondrás o registrarás y cómo identificarás las ocurrencias en el video."
            )

            enviar = st.form_submit_button("Sellar diseño observacional inicial")

            if enviar:
                fenomeno_limpio = fenomeno.strip()
                justificacion_limpia = justificacion.strip()
                hipotesis_limpia = hipotesis.strip()
                sujeto_limpio = posible_sujeto.strip()
                contexto_limpio = contexto.strip()
                objetivo_limpio = objetivo.strip()
                proc_limpio = proc.strip()

                categorias_lista = []
                for nombre, criterio in [(cat_1, crit_1), (cat_2, crit_2), (cat_3, crit_3)]:
                    nombre_limpio = nombre.strip()
                    criterio_limpio = criterio.strip()
                    if nombre_limpio or criterio_limpio:
                        categorias_lista.append((nombre_limpio, criterio_limpio))

                categorias_texto = "\n".join(
                    f"- {nombre}: {criterio}" for nombre, criterio in categorias_lista
                )

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

                if len(objetivo_limpio) < 15:
                    problemas.append("El objetivo de observación todavía es demasiado breve.")

                if not categorias_lista:
                    problemas.append("Debes definir al menos una categoría inicial de observación.")

                for i, (nombre, criterio) in enumerate(categorias_lista, start=1):
                    if not nombre:
                        problemas.append(f"La categoría {i} necesita un nombre.")
                    if len(criterio) < 20:
                        problemas.append(f"La categoría {i} necesita un criterio observable más claro.")

                if len(proc_limpio) < 40:
                    problemas.append("El procedimiento mínimo debe ser más claro y replicable.")

                texto_control = (categorias_texto + " " + objetivo_limpio).lower()
                palabras_fenomeno = [
                    p for p in fenomeno_limpio.lower().replace(",", " ").replace(".", " ").split()
                    if len(p) > 5
                ]

                if palabras_fenomeno and not any(p in texto_control for p in palabras_fenomeno[:4]):
                    problemas.append("No se ve con claridad cómo tus categorías u objetivo responden al fenómeno definido.")

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
                        "mediacion": "Video obligatorio",
                    }

                    st.session_state.grupo_actual["entregas"]["f2_protocolo"] = {
                        "caso_unico": sujeto_limpio,
                        "edad_caso": "---",
                        "contexto_caso": contexto_limpio,
                        "puente_pre": "",
                        "objetivo": objetivo_limpio,
                        "instrumento": "Registro en video",
                        "baremos": "",
                        "categorias": categorias_texto,
                        "procedimiento": proc_limpio,
                    }

                    st.session_state.grupo_actual["perfil_grupal"]["identidad_puntos"]["desarrollo"] += 10
                    ganar_xp(mision=200)
                    st.success("✅ Diseño observacional inicial sellado. En la Semana 2 podrás concentrarte en el trabajo de campo y el informe de observación.")
                    st.balloons()
                    st.rerun()

def render_semana_2():
    st.title("🧠 Semana 2: Observación del desarrollo y análisis del caso")
    st.info(
        "En esta fase realizas la observación, entregas tu informe completo por fuera de la app y aquí registras una lectura guiada de ese informe: evidencias, categorías, consideración del desarrollo y conclusiones."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🗣️ Expediente 06: Dimensiones del lenguaje infantil"):
        st.markdown(
            """
            **La evolución de la forma y el sentido:**
            Al observar el habla infantil, notarás grandes diferencias respecto al modelo adulto. Estas no son fallas, sino **estrategias naturales de aproximación**:
            * **Fonético-Fonológico:** Los niños usan *procesos de simplificación*, como reducir sílabas (decir "pato" por "zapato") o asimilar sonidos.
            * **Léxico-Semántico:** Experimentan la *sobreextensión* (usar una palabra para referirse a otras con características similares, ej. decirle "perro" a una vaca) y *sobrerrestricción*.
            * **Morfosintáctico:** Evolucionan desde la *holofrase* hasta el habla telegráfica.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s2_sobreext",
            pregunta="Si observas que un niño de 18 meses le dice 'guau guau' a un caballo, ¿qué fenómeno lingüístico estás presenciando?",
            opciones=[
                "Selecciona...",
                "Un proceso de simplificación fonológica",
                "Una sobreextensión semántica",
                "Un error de atención conjunta",
                "Una sobrerrestricción semántica",
            ],
            respuesta_correcta="Una sobreextensión semántica",
            feedback_correcto="Correcto. Aquí no ves un 'error' aislado, sino una estrategia de categorización.",
            feedback_incorrecto="Respuesta registrada. Revisa la dimensión léxico-semántica: la sobreextensión ocurre cuando una palabra se aplica a otros referentes por semejanza.",
            xp_epistemico=15,
        )

    with st.expander("⚠️ Expediente 07: Hitos del desarrollo y el riesgo de patologizar"):
        st.markdown(
            """
            **Observar ≠ Diagnosticar.**
            Los referentes del desarrollo son trayectorias generales, no normas rígidas. En psicolingüística, el objetivo es **describir recursos, estrategias y comunicabilidad**, no comparar al niño con un ideal adulto para detectar déficit.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s2_patolog",
            pregunta="Si grabas a un niño de 2 años y medio diciendo 'ota auto' (otro auto), tu rol metodológico debe ser:",
            opciones=[
                "Selecciona...",
                "Diagnosticar un retraso del lenguaje por falta de concordancia gramatical.",
                "Registrarlo como un dato de consolidación morfosintáctica sin patologizar.",
                "Remitir a los baremos de desarrollo para vigilar posibles signos de alerta",
            ],
            respuesta_correcta="Registrarlo como un dato de consolidación morfosintáctica sin patologizar.",
            feedback_correcto="Correcto. Tu tarea aquí es describir procesos, no cerrar un juicio clínico.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia entre descripción psicolingüística y diagnóstico clínico: este curso busca observar procesos sin patologizar.",
            xp_epistemico=15,
        )

    with st.expander("👶 Expediente 08: Antes de la palabra: Precursores de la comunicación"):
        st.markdown(
            """
            **La comunicación precede al lenguaje verbal.**

            Antes de que aparezcan las primeras palabras, ya existen formas de comunicación intencional. Algunos precursores importantes son el contacto ocular, la sonrisa social, la atención conjunta y los señalamientos.

            Los señalamientos pueden cumplir distintas funciones:
            * **Protoimperativos:** el bebé señala para pedir algo o lograr que el adulto actúe.
            * **Protodeclarativos:** el bebé señala para compartir atención o interés sobre algo.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s2_precursores",
            pregunta="Si un bebé de 10 meses señala un juguete fuera de su alcance y mira alternadamente al juguete y al adulto para que se lo alcance, está realizando:",
            opciones=[
                "Selecciona...",
                "Un señalamiento protodeclarativo",
                "Un señalamiento protoimperativo",
                "Una atención conjunta pasiva",
            ],
            respuesta_correcta="Un señalamiento protoimperativo",
            feedback_correcto="Correcto. El bebé usa el señalamiento para solicitar la acción del adulto.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia: el protoimperativo busca que el adulto actúe; el protodeclarativo busca compartir atención o interés.",
            xp_epistemico=15,
        )

    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    proto = st.session_state.grupo_actual["entregas"].get("f2_protocolo")
    informe_existente = st.session_state.grupo_actual["entregas"].get("f2_informe")

    st.markdown("## 🎯 Misión 2: Trabajo de campo e informe de observación")

    if not pre or not proto:
        st.warning("Debes sellar el diseño observacional inicial en la Semana 1 antes de registrar el informe de observación.")
        return

    st.markdown("### 🧾 Diseño recuperado de la Semana 1")
    st.write(f"**Fenómeno:** {pre.get('fenomeno', '---')}")
    st.write(f"**{pre.get('tipo_compromiso', 'Hipótesis')}:** {pre.get('hipotesis', '---')}")
    st.write(f"**Caso previsto:** {proto.get('caso_unico', '---')} ({proto.get('edad_caso', '---')})")
    st.write(f"**Contexto:** {proto.get('contexto_caso', '---')}")
    st.write(f"**Instrumento:** {proto.get('instrumento', '---')}")
    st.write(f"**Marco de referencia:** {proto.get('baremos', '---')}")
    st.write(f"**Categorías iniciales:** {proto.get('categorias', '---')}")
    st.caption("Este diseño orienta el informe, pero puede ajustarse si el trabajo de campo mostró algo relevante.")

    if informe_existente:
        st.success("✅ Ya tienes un informe de observación registrado.")
        st.markdown("### 📊 Síntesis registrada")
        st.write(f"**Informe completo:** {informe_existente.get('link', '---')}")
        st.write(f"**Evidencia empírica:** {informe_existente.get('evidencia', '---')[:400]}...")
        st.write(f"**Perfil lingüístico:** {informe_existente.get('perfil', '---')[:400]}...")
        st.write(f"**Decisión frente a hipótesis/pregunta:** {informe_existente.get('decision', '---')}")
        st.write(f"**Conclusiones:** {informe_existente.get('conclusiones', '---')[:400]}...")
        st.caption("Este registro será retomado en la Semana 3 para el diseño del juguete de estimulación lingüística.")

        with st.expander("🕵️ Expediente 09: El silencio de los datos"):
            st.markdown(
                """
                **Has entregado tu primer reporte empírico.**

                Seguramente notaste que el niño no produjo todo lo que esperabas. Describir el habla infantil implica reflexionar sobre las formas presentes, pero también sobre las formas ausentes.

                ¿Cuántos datos son suficientes para aseverar que un niño no ha adquirido una forma? A veces, una palabra o sonido simplemente no aparece porque el contexto comunicativo de esa tarde no lo requirió.
                """
            )

            resolver_expediente_opcion_unica(
                expediente_id="s2_silencio_datos",
                pregunta="Si en tu registro de campo de 30 minutos el niño observado no produjo ninguna frase de dos palabras, la conclusión analítica más prudente es:",
                opciones=[
                    "Selecciona...",
                    "Dictaminar que el niño tiene un retraso en el desarrollo morfosintáctico.",
                    "Reconocer que la ausencia del dato en esa muestra no demuestra la falta de competencia; puede ser una forma emergente o que el contexto no lo elicitó.",
                ],
                respuesta_correcta="Reconocer que la ausencia del dato en esa muestra no demuestra la falta de competencia; puede ser una forma emergente o que el contexto no lo elicitó.",
                feedback_correcto="Correcto. La ausencia de una forma en una muestra limitada no permite concluir déficit.",
                feedback_incorrecto="Respuesta registrada. Revisa la cautela metodológica: que algo no aparezca en una muestra breve no significa que el niño no pueda producirlo.",
                xp_epistemico=15,
            )

        return
    
    st.divider()
    st.markdown("## 📎 Informe completo")
    st.caption(
        "El informe puede estar en Word, PDF, Drive, Canva u otro formato. La app no reemplaza el documento: registra su lectura metodológica."
    )

    with st.form("f2_informe_observacion"):
        link_informe = st.text_input(
            "Enlace al informe completo o carpeta de evidencias"
        )

        st.markdown("### 1. Evidencia empírica")
        evidencia = st.text_area(
            "Escribe 2–3 ejemplos reales del habla, gestos, interacción o conducta comunicativa observada. Procura conservar la forma en que apareció el dato.",
            placeholder="Ejemplo: dice 'guau guau' para referirse a un caballo; señala el objeto y mira al adulto; dice 'ota auto' al pedir otro carro..."
        )

        st.markdown("### 2. Organización según el protocolo")
        categorias_uso = st.text_area(
            "¿Cómo organizaste esos datos según las categorías iniciales de la Semana 1? También puedes explicar si alguna categoría tuvo que ajustarse."
        )

        st.markdown("### 3. Consideración sobre el desarrollo")
        consideracion_desarrollo = st.text_area(
            "Interpreta lo observado a la luz del desarrollo del lenguaje. No diagnostiques: describe recursos, estrategias, trayectorias esperables o aspectos que requieren cautela."
        )

        st.markdown("### 4. Perfil lingüístico observado")
        perfil = st.text_area(
            "Describe el perfil comunicativo y lingüístico del niño a partir de los datos: recursos disponibles, formas de interacción, producción, comprensión, gestos, juego o uso funcional del lenguaje."
        )

        decision = st.selectbox(
            "5. ¿Qué ocurrió con tu hipótesis o pregunta inicial?",
            ["Selecciona...", "Se confirma", "Se ajusta parcialmente", "No se sostiene con los datos", "La observación abrió una pregunta nueva"],
        )

        justificacion = st.text_area(
            "6. Justifica tu decisión usando datos concretos del informe."
        )

        cautela = st.text_area(
            "7. ¿Qué evitaste sobrerinterpretar o patologizar en tu análisis?"
        )

        conclusiones = st.text_area(
            "8. Conclusiones del informe de observación. Sintetiza qué aprendiste del caso y qué implicaciones tiene para comprender el desarrollo del lenguaje."
        )

        evidencia_link = st.text_input(
            "Enlace opcional a evidencias complementarias: fotos, capturas, tablas, audios o videos"
        )

        enviar_informe = st.form_submit_button("Sellar informe de observación")

        if enviar_informe:
            problemas = []

            if not link_informe.strip():
                problemas.append("Debes adjuntar el informe completo o un enlace a la carpeta de evidencias.")
            if len(evidencia.strip()) < 50:
                problemas.append("Incluye ejemplos empíricos más claros y concretos.")
            if len(categorias_uso.strip()) < 60:
                problemas.append("Debes explicar cómo organizaste los datos según tus categorías.")
            if len(consideracion_desarrollo.strip()) < 80:
                problemas.append("La consideración sobre el desarrollo necesita mayor elaboración.")
            if len(perfil.strip()) < 100:
                problemas.append("El perfil lingüístico observado todavía es demasiado breve.")
            if decision == "Selecciona...":
                problemas.append("Debes tomar una decisión frente a tu hipótesis o pregunta inicial.")
            if len(justificacion.strip()) < 80:
                problemas.append("La justificación debe apoyarse mejor en los datos observados.")
            if len(cautela.strip()) < 50:
                problemas.append("Debes explicitar mejor la cautela interpretativa o no patologizante.")
            if len(conclusiones.strip()) < 80:
                problemas.append("Las conclusiones necesitan mayor desarrollo.")

            categorias_previas = proto.get("categorias", "").lower().strip()
            if categorias_previas:
                primeras_palabras = [
                    p for p in categorias_previas.replace("-", " ").replace(":", " ").split()
                    if len(p) > 5
                ][:8]
                texto_categoria = (categorias_uso + " " + perfil + " " + justificacion).lower()
                if primeras_palabras and not any(p.lower() in texto_categoria for p in primeras_palabras):
                    st.warning(
                        "La relación con las categorías iniciales no es evidente. Puedes continuar, pero revisa si debes explicitar mejor el puente con la Semana 1."
                    )

            if problemas:
                for p in problemas:
                    st.error(p)
            else:
                st.session_state.grupo_actual["entregas"]["f2_informe"] = {
                    "link": link_informe.strip(),
                    "evidencia": evidencia.strip(),
                    "categorias": categorias_uso.strip(),
                    "consideracion_desarrollo": consideracion_desarrollo.strip(),
                    "perfil": perfil.strip(),
                    "decision": decision,
                    "justificacion": justificacion.strip(),
                    "cautela": cautela.strip(),
                    "conclusiones": conclusiones.strip(),
                    "evidencia_link": evidencia_link.strip(),
                }

                ganar_xp(mision=200, epistemico=25)
                save_group_data(st.session_state.grupo_actual)

                st.success("✅ Informe de observación sellado. Has convertido el trabajo de campo en análisis psicolingüístico.")
                st.balloons()
                st.rerun()

def render_semana_3():
    st.title("🧸 Semana 3: Aplicación del análisis – Diseño de un juguete")
    st.info(
        "En esta fase traduces los hallazgos del informe de observación en una propuesta aplicada: un juguete de estimulación lingüística fundamentado en el caso."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🪁 Expediente 10: El juego como motor cognitivo y la ZDP"):
        st.markdown(
            """
            **El juguete como herramienta cultural.**
            Según distintas teorías del desarrollo, el juego no es un complemento, sino un medio de reorganización cognitiva.
            * **Piaget:** Permite la asimilación y acomodación de la realidad.
            * **Vygotsky:** El juguete puede funcionar como andamiaje en la **Zona de Desarrollo Próximo (ZDP)**.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s3_zdp",
            pregunta="Si diseñas un juguete que el niño no puede resolver por sí solo, pero sí con apoyo o con la estructura del objeto, estás operando en:",
            opciones=[
                "Selecciona...",
                "La etapa preoperacional estricta",
                "La Zona de Desarrollo Próximo (ZDP)",
                "El condicionamiento operante mediante refuerzos positivos",
            ],
            respuesta_correcta="La Zona de Desarrollo Próximo (ZDP)",
            feedback_correcto="Correcto. Aquí el objeto no solo entretiene: estructura una posibilidad de desarrollo.",
            feedback_incorrecto="Respuesta registrada. Revisa la ZDP: se refiere a aquello que el niño puede lograr con apoyo, mediación o andamiaje.",
            xp_epistemico=15,
        )

    with st.expander("♻️ Expediente 11: Diseño Adaptativo, Identidad y Economía Circular"):
        st.markdown(
            """
            **Sustentabilidad y pertinencia cultural.**
            El diseño adaptativo exige considerar seguridad, ergonomía y contexto. También puede incorporar materiales y referencias locales para darle al objeto mayor pertinencia cultural.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s3_eco",
            pregunta="¿Por qué puede ser preferible usar recursos de la región en lugar de materiales genéricos para tu prototipo?",
            opciones=[
                "Selecciona...",
                "Para estandarizar el producto y asegurar que cumpla con normas internacionales de exportación masiva",
                "Para reducir tiempo de fabricación y costos logísticos",
                "Para dotar al objeto de pertinencia cultural y aprovechar materiales disponibles",
            ],
            respuesta_correcta="Para dotar al objeto de pertinencia cultural y aprovechar materiales disponibles",
            feedback_correcto="Correcto. El diseño también comunica contexto e identidad.",
            feedback_incorrecto="Respuesta registrada. Revisa la idea de pertinencia cultural: el objeto no solo funciona, también dialoga con el contexto del niño.",
            xp_epistemico=15,
        )

    with st.expander("🧩 Expediente 12: El juguete como ancla para la Atención Conjunta"):
        st.markdown(
            """
            **El juguete no enseña por sí solo; la interacción sí.**

            Según E. Clark (2009), la adquisición del lenguaje requiere interacción. Para que la comunicación sea efectiva, el adulto y el niño deben compartir un foco de atención conjunta.

            En estas interacciones tempranas, los adultos suelen **anclar** sus contribuciones a objetos físicamente presentes en el entorno.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s3_atencion_conjunta",
            pregunta="Si diseñas un juguete asumiendo que el niño lo usará completamente solo y aislado, ¿qué mecanismo esencial para la adquisición del lenguaje estás omitiendo?",
            opciones=[
                "Selecciona...",
                "La modificación de la estructura sintáctica.",
                "La atención conjunta triádica y la co-presencia física.",
                "El desarrollo fonológico autónomo.",
            ],
            respuesta_correcta="La atención conjunta triádica y la co-presencia física.",
            feedback_correcto="Correcto. El juguete funciona como mediador dentro de una interacción compartida.",
            feedback_incorrecto="Respuesta registrada. Revisa la atención conjunta: el aprendizaje lingüístico temprano ocurre en interacción con otros y con objetos compartidos.",
            xp_epistemico=15,
        )

    st.markdown("## 🎯 Misión 3: Diseño de un juguete de estimulación lingüística y cognitiva")

    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    proto = st.session_state.grupo_actual["entregas"].get("f2_protocolo")
    informe = st.session_state.grupo_actual["entregas"].get("f2_informe")
    juguete_existente = st.session_state.grupo_actual["entregas"].get("f3_juguete")

    if not pre or not proto:
        st.warning("Debes completar primero el diseño observacional inicial de la Semana 1.")
        return

    if not informe:
        st.warning("Debes sellar primero el informe de observación en la Semana 2 para habilitar el diseño del juguete.")
        return

    st.markdown("### 🧾 Memoria del proceso")
    st.write(f"**Fenómeno inicial:** {pre.get('fenomeno', '---')}")
    st.write(f"**{pre.get('tipo_compromiso', 'Hipótesis')}:** {pre.get('hipotesis', '---')}")
    st.write(f"**Caso observado:** {proto.get('caso_unico', '---')} ({proto.get('edad_caso', '---')})")
    st.write(f"**Categorías iniciales:** {proto.get('categorias', '---')}")

    st.markdown("### 📊 Hallazgos recuperados del informe")
    st.write(f"**Decisión frente a hipótesis/pregunta:** {informe.get('decision', '---')}")
    st.write(f"**Perfil lingüístico observado:** {informe.get('perfil', '---')[:500]}...")
    st.write(f"**Consideración sobre el desarrollo:** {informe.get('consideracion_desarrollo', '---')[:500]}...")
    st.write(f"**Conclusiones:** {informe.get('conclusiones', '---')[:500]}...")
    st.caption("El juguete debe derivarse de estos hallazgos. No es una idea libre: es una respuesta aplicada al caso observado.")

    st.divider()
    st.markdown("### 🧸 Producto: Juguete de estimulación lingüística (15%)")

    if juguete_existente:
        st.success("✅ Ya tienes un juguete adaptativo registrado.")
        st.write(f"**Nombre:** {juguete_existente.get('nombre', '---')}")
        st.write(f"**Rasgo observado que lo inspira:** {juguete_existente.get('rasgo_inspirador', '---')}")
        st.write(f"**Justificación de caso:** {juguete_existente.get('just_caso', '---')[:300]}...")
        st.write(f"**Justificación pedagógica:** {juguete_existente.get('just_pedag', '---')[:300]}...")
        st.write(f"**Enlace:** {juguete_existente.get('link', '---')}")

        with st.expander("🚀 Expediente 13: El límite del diseño y la agencia infantil"):
            st.markdown(
                """
                **¡Diseño completado!**

                Has traducido tus hallazgos clínicos en un juguete de estimulación fundamentado en la teoría. Sin embargo, el desarrollo cognitivo nos advierte algo crucial: en el juego, los niños tienen agencia.

                Un niño puede tomar tu sofisticado juguete, diseñado meticulosamente para estimular relaciones semánticas espaciales, e ignorar su propósito para usarlo como un sombrero o un teléfono.

                **El diseño del adulto propone, pero la mente infantil dispone.**
                """
            )

            resolver_expediente_opcion_unica(
                expediente_id="s3_agencia_infantil",
                pregunta="Si al entregarle tu juguete al niño notas que ignora por completo las reglas lingüísticas que diseñaste y comienza a usar el objeto para una representación simbólica totalmente diferente, tu postura reflexiva como investigador debe ser:",
                opciones=[
                    "Selecciona...",
                    "Interrumpir el juego libre para enseñarle la forma \"correcta\" de usar el juguete, forzando la actividad para que tu diseño no fracase.",
                    "Valorar y registrar este uso divergente como un dato riquísimo de su capacidad de sustitución simbólica, respetando su agencia sin patologizar el hecho de que no siga reglas.",
                    "Asumir que el juguete estuvo mal diseñado desde el principio y que el niño presenta un déficit en el seguimiento de instrucciones.",
                ],
                respuesta_correcta="Valorar y registrar este uso divergente como un dato riquísimo de su capacidad de sustitución simbólica, respetando su agencia sin patologizar el hecho de que no siga reglas.",
                feedback_correcto="Correcto. El uso divergente también es un dato sobre agencia, juego simbólico y desarrollo cognitivo.",
                feedback_incorrecto="Respuesta registrada. Revisa la idea de agencia infantil: el niño no solo ejecuta instrucciones adultas; también transforma el objeto mediante el juego simbólico.",
                xp_epistemico=15,
            )

        return
    
    with st.form("f3_juguete"):
        nombre_j = st.text_input("Nombre del juguete")
        rasgo_inspirador = st.text_input(
            "¿Qué rasgo, recurso o patrón observado en el niño inspiró directamente este diseño?"
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
            diseno_ergo = st.text_area(
                "Diseño y ergonomía: seguridad, uso, adecuación a la edad y etapa de desarrollo"
            )
            sustentabilidad = st.text_area(
                "Materiales, contexto y/o pertinencia cultural"
            )

        link_j = st.text_input("Enlace a ficha visual, boceto o evidencia del prototipo (Drive/Canva/etc.)")

        enviar_juguete = st.form_submit_button("Entregar diseño de juguete")

        if enviar_juguete:
            problemas = []

            if not nombre_j.strip():
                problemas.append("Debes nombrar el juguete.")
            if not rasgo_inspirador.strip():
                problemas.append("Debes indicar qué hallazgo del informe inspiró el diseño.")
            if len(just_caso.strip()) < 80:
                problemas.append("La justificación de caso necesita mayor desarrollo.")
            if len(just_pedag.strip()) < 60:
                problemas.append("Debes fundamentar mejor la dimensión pedagógica.")
            if len(diseno_ergo.strip()) < 60:
                problemas.append("Debes describir mejor el diseño, la seguridad y la adecuación a la etapa.")
            if not link_j.strip():
                problemas.append("Debes adjuntar un enlace a la evidencia visual del diseño.")

            perfil_obs = (
                informe.get("perfil", "") + " " +
                informe.get("evidencia", "") + " " +
                informe.get("consideracion_desarrollo", "") + " " +
                informe.get("conclusiones", "")
            ).lower()

            palabras_clave = [
                p for p in rasgo_inspirador.lower().replace(",", " ").replace(".", " ").split()
                if len(p) > 4
            ]

            if palabras_clave and not any(p in perfil_obs for p in palabras_clave):
                st.warning(
                    "La relación entre el rasgo inspirador y el informe no es evidente. Puedes continuar, pero conviene explicitar mejor ese vínculo en la justificación de caso."
                )

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
                st.session_state.grupo_actual["perfil_grupal"]["identidad_puntos"]["aplicada"] += 15
                save_group_data(st.session_state.grupo_actual)

                st.success("✅ Juguete registrado. Has traducido un hallazgo observacional en una propuesta aplicada.")
                st.balloons()
                st.rerun()
                
def render_semana_4():
    st.title("🧩 Semana 4: Modelos Cognitivos y Diseño Experimental")
    st.info("En esta fase dejas la observación naturalista y pasas a aislar procesos mentales en condiciones controladas.")

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("🔄 Expediente 14: Producción vs. Comprensión"):
        st.markdown(
            """
            * **Comprensión:** Del estímulo al significado.
            * **Producción:** De la intención al habla.
            """
        )
        resolver_expediente_opcion_unica(
            expediente_id="s4_comp",
            pregunta="Si mides el tiempo de reconocimiento de una palabra, estás estudiando:",
            opciones=[
                "Selecciona...",
                "Producción",
                "Adquisición",
                "Comprensión",
            ],
            respuesta_correcta="Comprensión",
            feedback_correcto="Correcto.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia: la comprensión va del estímulo lingüístico al significado; la producción va de la intención al habla.",
            xp_epistemico=10,
        )

    with st.expander("🏛️ Expediente 15: Modelos de procesamiento"):
        st.markdown(
            """
            * **Modular:** Serial, encapsulado.
            * **Interactivo:** Paralelo, con influencia mutua.
            """
        )
        resolver_expediente_opcion_unica(
            expediente_id="s4_mod",
            pregunta="Si el contexto ayuda a reconocer letras, apoyas un modelo:",
            opciones=[
                "Selecciona...",
                "Influencia mutua",
                "Modular/Autónomo",
                "Interactivo/Conexionista",
            ],
            respuesta_correcta="Interactivo/Conexionista",
            feedback_correcto="Correcto.",
            feedback_incorrecto="Respuesta registrada. Revisa los modelos interactivos: permiten influencia mutua entre niveles de procesamiento.",
            xp_epistemico=15,
        )

    with st.expander("🛡️ Expediente 16: El Blindaje Experimental: Variables de Confusión"):
        st.markdown(
            """
            **El control del caos.**

            En un experimento verdadero debes garantizar que el cambio en la Variable Dependiente (VD) fue causado exclusivamente por tu Variable Independiente (VI). Cualquier otra circunstancia es ruido que amenaza tu validez interna y debe ser controlada.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s4_confusion",
            pregunta="Si en tu experimento comparas el tiempo de reacción ante palabras frecuentes vs. poco frecuentes, pero resulta que todas las palabras frecuentes eran cortas y las poco frecuentes eran muy largas, la 'longitud de la palabra' se ha convertido en:",
            opciones=[
                "Selecciona...",
                "Una variable de control aleatorizada con éxito.",
                "Una segunda variable dependiente del experimento.",
                "Una variable de confusión que arruina la validez interna.",
            ],
            respuesta_correcta="Una variable de confusión que arruina la validez interna.",
            feedback_correcto="Correcto. Una variable que cambia junto con la VI amenaza la validez interna del experimento.",
            feedback_incorrecto="Respuesta registrada. Revisa la variable de confusión: es una variable no controlada que covaría con la VI y amenaza la interpretación causal.",
            xp_epistemico=15,
        )

    st.divider()
    st.markdown("## 🎯 Misión 4: Diseño Experimental (25%)")

    pre = st.session_state.grupo_actual["entregas"].get("f1_pre_registro")
    informe = st.session_state.grupo_actual["entregas"].get("f3_informe")
    diseno_existente = st.session_state.grupo_actual["entregas"].get("f4_diseno_exp")

    if pre and informe:
        st.markdown("### 🧾 Memoria del proceso")
        st.write(f"**Fenómeno inicial:** {pre.get('fenomeno','---')}")
        st.write(f"**Decisión sobre hipótesis:** {informe.get('decision_hipotesis','---')}")

    if diseno_existente:
        st.success("✅ Ya tienes un diseño experimental registrado.")
        st.write(f"**Tipo:** {diseno_existente.get('tipo', '---')}")
        st.write(f"**Hipótesis:** {diseno_existente.get('hipotesis', '---')}")
        st.write(f"**VI:** {diseno_existente.get('vi', '---')}")
        st.write(f"**VD:** {diseno_existente.get('vd', '---')}")
        st.write(f"**Variables de control:** {diseno_existente.get('control', '---')}")
        st.write(f"**Ruido anticipado:** {diseno_existente.get('ruido', '---')}")

        with st.expander("⚖️ Expediente 17: La amenaza de la Mortalidad Diferencial"):
            st.markdown(
                """
                **¡Diseño sellado y blindado!**

                Ahora debes salir a recolectar datos con al menos 10 informantes reales. Sin embargo, el trabajo con humanos es impredecible. ¿Qué pasa si algunos de tus informantes se aburren o frustran a la mitad de la prueba y la abandonan? En metodología, la pérdida de sujetos es peligrosa.
                """
            )

            resolver_expediente_opcion_unica(
                expediente_id="s4_confusion",
                pregunta="Si en tu experimento comparas el tiempo de reacción ante palabras frecuentes vs. poco frecuentes, pero resulta que todas las palabras frecuentes eran cortas y las poco frecuentes eran muy largas, la 'longitud de la palabra' se ha convertido en:",
                opciones=[
                    "Selecciona...",
                    "Una variable de control aleatorizada con éxito.",
                    "Una segunda variable dependiente del experimento.",
                    "Una variable de confusión que arruina la validez interna.",
                ],
                respuesta_correcta="Una variable de confusión que arruina la validez interna.",
                feedback_correcto="Correcto. Una variable que cambia junto con la VI amenaza la validez interna del experimento.",
                feedback_incorrecto="Respuesta registrada. Revisa la variable de confusión: es una variable no controlada que covaría con la VI y amenaza la interpretación causal.",
                xp_epistemico=15,
            )

        return

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
    st.title("📊 Semana 5: Informe de Experimento")
    st.info(
        "Has llegado a la cumbre de tu entrenamiento, Investigador Junior. Es hora de enfrentar los datos empíricos reales, gestionar el caos metodológico y defender tus hallazgos."
    )

    st.markdown("## 🧠 Expedientes de Caso")

    with st.expander("⏱️ Expediente 18: ¿Procesos o Productos? (On-line vs. Off-line)"):
        st.markdown(
            """
            **¿Cuándo medir la comprensión?**
            * **Medidas posteriores (Off-line):** Como el recuerdo libre o el reconocimiento. Apuntan al producto final o la representación mental resultante después de que la comprensión ha tenido lugar.
            * **Medidas en curso (On-line o cronométricas):** Como el registro de movimientos oculares, la ventana móvil o la decisión léxica. Permiten investigar los subprocesos en el momento en que operan, asumiendo que un mayor tiempo de reacción (milisegundos) implica una mayor carga de procesamiento.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s5_online",
            pregunta="Si tu objetivo es medir exactamente en qué milisegundo el cerebro del lector detecta una anomalía sintáctica al leer una oración, debes usar:",
            opciones=[
                "Selecciona...",
                "Una técnica Off-line (Prueba de memoria al final del texto)",
                "Análisis proposicional",
                "Una técnica On-line (Registro de movimientos oculares o potenciales evocados)",
            ],
            respuesta_correcta="Una técnica On-line (Registro de movimientos oculares o potenciales evocados)",
            feedback_correcto="¡Exacto! Necesitas capturar el proceso mental en tiempo real.",
            feedback_incorrecto="Respuesta registrada. Revisa la diferencia: las técnicas on-line capturan el procesamiento en tiempo real.",
            xp_epistemico=15,
        )

    with st.expander("🌪️ Expediente 19: El Ruido Experimental"):
        st.markdown(
            """
            **La incertidumbre en los datos empíricos:**
            En un experimento real, a veces los tiempos de reacción son inconsistentes. Esto puede ocurrir porque:
            1. Tu técnica interrumpió el proceso natural de lectura (confusión entre la activación lingüística y las exigencias de la propia tarea experimental).
            2. Variables de confusión no controladas (fatiga, distracciones, diferencias individuales).
            El buen científico no oculta el ruido, lo audita y lo explica.
            """
        )

        resolver_expediente_opcion_unica(
            expediente_id="s5_ruido",
            pregunta="Si un participante tarda 4000 milisegundos en una tarea de decisión léxica donde el promedio es de 600 ms, la acción más ética metodológicamente es:",
            opciones=[
                "Selecciona...",
                "Eliminar el dato en silencio para que la hipótesis cuadre perfecta",
                "Modificar la hipótesis original a posteriori para que coincida con este dato atípico",
                "Auditar el valor atípico (outlier), justificar estadísticamente su exclusión y reportarlo",
            ],
            respuesta_correcta="Auditar el valor atípico (outlier), justificar estadísticamente su exclusión y reportarlo",
            feedback_correcto="Excelente criterio ético y metodológico. La ciencia exige transparencia.",
            feedback_incorrecto="Respuesta registrada. Revisa el manejo de outliers: no se eliminan sin justificación ni se acomodan hipótesis.",
            xp_epistemico=15,
        )

    with st.expander("⚠️ Expediente 20: Simulación de Incertidumbre"):
        st.warning(
            "¡Alerta en el Laboratorio! El software de decisión léxica ha arrojado los siguientes tiempos de reacción (TR) para la condición experimental. Hay una anomalía evidente."
        )

        datos_simulados = {
            "Sujeto": [3, 4, 5, 6, 7],
            "TR (Milisegundos)": [580, 610, 4000, 595, 620],
            "Respuesta": ["Correcta", "Correcta", "Incorrecta", "Correcta", "Correcta"],
        }
        st.table(datos_simulados)

        from utils_expedientes import evaluar_calidad_respuesta_abierta

        # Estado
        grupo = st.session_state.grupo_actual
        respuestas = grupo.setdefault("perfil_grupal", {}).setdefault("respuestas_expedientes", {})

        expediente_id = "s5_simulacion_ruido"

        # Si ya respondió → bloquear edición
        if expediente_id in respuestas:
            respuesta_guardada = respuestas[expediente_id]["respuesta"]
            st.info("Ya registraste este análisis en la bitácora de laboratorio.")
            st.markdown(f"**Tu respuesta:** {respuesta_guardada}")
        else:
            interpretacion = st.text_area(
                "Bitácora de Laboratorio: ¿Cómo manejas el 'outlier' del Sujeto 5 en tu análisis? ¿Qué pudo haber causado este ruido metodológico? (Pista: utiliza conceptos como 'variable de confusión' o 'amenaza a la validez')",
                key="s5_expediente_18_outlier",
            )

            if st.button("Registrar Análisis Crítico del Ruido", key="btn_s5_expediente_18"):

                resultado = evaluar_calidad_respuesta_abierta(
                    interpretacion,
                    conceptos_clave=[
                        "outlier",
                        "valor atípico",
                        "variable de confusión",
                        "validez",
                        "fatiga",
                        "distracción",
                        "ruido",
                        "error",
                        "sesgo",
                        "tiempo de reacción",
                    ],
                    min_caracteres=120,
                    min_palabras=20,
                    min_conceptos=2,
                )

                if resultado["valida"]:
                    # Guardar respuesta
                    respuestas[expediente_id] = {
                        "respuesta": interpretacion,
                        "miembro": st.session_state.miembro_actual,
                    }

                    # Identidad (como ya hacías)
                    grupo["perfil_grupal"]["identidad_puntos"]["experimental"] += 15

                    # XP
                    ganar_xp(epistemico=20)

                    # Marcar caso resuelto
                    grupo.setdefault("casos_resueltos", []).append(expediente_id)

                    save_group_data(grupo)

                    st.success("Rigor metodológico validado. Sabes interrogar al ruido.")
                    st.rerun()

                else:
                    st.error("Tu respuesta aún no cumple con los criterios metodológicos mínimos.")
                    for problema in resultado["problemas"]:
                        st.warning(f"• {problema}")

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
    
        informe_final = st.session_state.grupo_actual["entregas"].get("f5_informe_final")

    if informe_final:
        st.divider()

        with st.expander("🚀 Expediente 21: El dilema de la Generalización (Validez Externa)"):
            st.markdown(
                """
                **¡Has finalizado tu entrenamiento!**

                Has completado el ciclo científico desde la observación infantil en ambientes naturales hasta la experimentación en adultos bajo condiciones de laboratorio. Lograste aislar variables y controlar el ruido empírico. Pero la ciencia rigurosa tiene un precio: el dilema del control.
                """
            )

            resolver_expediente_opcion_unica(
                expediente_id="s5_generalizacion",
                pregunta="Si tu experimento de lectura fue extremadamente controlado (aislaste al sujeto frente a una pantalla negra, leyendo sílaba por sílaba en milisegundos), obtuviste una alta validez interna. Sin embargo, metodológicamente, ¿qué has sacrificado a cambio?",
                opciones=[
                    "Selecciona...",
                    "La fiabilidad y precisión estadística de los datos recogidos.",
                    "La capacidad de eliminar las variables de confusión (como el ruido ambiente).",
                    "La validez externa, es decir, la posibilidad de generalizar esos resultados a una situación de lectura normal y cotidiana.",
                ],
                respuesta_correcta="La validez externa, es decir, la posibilidad de generalizar esos resultados a una situación de lectura normal y cotidiana.",
                feedback_correcto="Correcto. Al aumentar el control experimental, suele reducirse la generalización a contextos cotidianos.",
                feedback_incorrecto="Respuesta registrada. Revisa la relación entre validez interna y externa.",
                xp_epistemico=15,
            )

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

