# Psycholinguistics Lab (Psicoling App)

Plataforma gamificada para la enseñanza de la psicolingüística en pregrado, desarrollada en Streamlit.

Proyecto diseñado para el curso **Psicolingüística (código 928013)** del pregrado en Psicología de la **Universidad de Antioquia**.

Desarrollado por:

**Víctor Julián Vallejo Zapata**  
Psicólogo, Magíster y PhD en Lingüística – Universidad de Antioquia

## Propósito

- Transformar la enseñanza de la psicolingüística desde un modelo expositivo hacia un modelo:
  - activo
  - investigativo
  - basado en decisiones
  - centrado en el estudiante

- Promover que los estudiantes construyan conocimiento a través de un ciclo completo de investigación psicolingüística.

- Articular teoría, análisis del lenguaje y metodología científica en un mismo entorno de aprendizaje.

## Enfoque pedagógico

- Aprendizaje orientado a proyectos.
- Simulación del método científico.
- Integración de:
  - psicolingüística del desarrollo
  - procesamiento del lenguaje
  - metodología de investigación

- Énfasis en:
  - observación del lenguaje como construcción teórica
  - no patologización del lenguaje infantil
  - relación entre lenguaje, cognición y contexto

## Estructura del curso en la plataforma

El curso se organiza en cinco fases secuenciales:

### Fase 1 – Pre-registro

- Definición del fenómeno lingüístico.
- Formulación de hipótesis o pregunta.
- Delimitación del caso.

**Entregable:**

- Pre-registro del fenómeno lingüístico.

### Fase 2 – Protocolo de observación

- Operacionalización del fenómeno.
- Definición de categorías observables.
- Diseño de instrumento y procedimiento.

**Entregable:**

- Protocolo de observación del lenguaje.

### Fase 3 – Observación y análisis

- Recolección de datos reales.
- Sistematización del perfil lingüístico.
- Interpretación de resultados.

**Entregables:**

- Informe de observación.
- Diseño de un juguete de estimulación lingüística.

### Fase 4 – Diseño experimental

- Formulación de hipótesis experimental.
- Definición de variables.
- Diseño de tarea experimental.

**Entregable:**

- Protocolo experimental.

### Fase 5 – Informe experimental

- Análisis de datos.
- Evaluación de hipótesis.
- Discusión metodológica.

**Entregable:**

- Informe de experimento.

## Ciclo de aprendizaje

El proceso integra tres niveles:

- Observación del lenguaje:
  - pre-registro
  - protocolo de observación
  - informe de observación

- Traducción aplicada:
  - diseño de juguete de estimulación lingüística

- Experimentación:
  - protocolo experimental
  - informe de experimento

## Sistema de gamificación

- XP de misión:
  - progreso evaluativo del curso

- XP epistémico:
  - calidad del razonamiento

- Desarrollo de identidad investigativa:
  - experimental
  - desarrollo del lenguaje
  - aplicada

La gamificación organiza el proceso de aprendizaje; no es decorativa.

## Trabajo colaborativo

- Trabajo principalmente grupal.
- Grupos con ID único.
- Múltiples integrantes por grupo.
- Seguimiento individual dentro del grupo.
- Producción colectiva de entregables.

## Seguimiento docente

La plataforma incluye una consola que permite:

- Visualizar grupos activos.
- Acceder a entregas por fase.
- Monitorear progreso y XP.
- Realizar seguimiento evaluativo.
- Exportar datos.

## Arquitectura técnica

- `app.py`: enrutamiento principal.
- `ui_estudiante.py`: interfaz de estudiante.
- `ui_docente.py`: consola docente.
- `modelo_estado.py`: gestión de estado.
- `logica.py`: sistema de XP.
- `persistencia.py`: almacenamiento.
- `storage_gsheets.py`: integración con Google Sheets.

## Estado actual del proyecto

- Plataforma funcional en fase avanzada.
- Flujo completo de estudiante implementado.
- Sistema de persistencia operativo.
- Consola docente activa.
- Arquitectura modular estable.

Actualmente en:

- validación técnica
- pruebas de consistencia
- preparación para pruebas de usabilidad

## Proyección

- Implementación en cursos universitarios.
- Escalamiento como herramienta EdTech.
- Adaptación a otros cursos universitarios.

## Idea central

Psycholinguistics Lab no enseña psicolingüística como contenido.

Enseña psicolingüística como práctica.

## Estado de desarrollo

- Versión: 0.1 (prototipo funcional)
- Tipo: MVP (Minimum Viable Product)

Esta versión constituye la primera implementación integral del sistema y la primera experiencia del autor en el desarrollo de una aplicación completa.

Se espera iterar sobre esta base mediante validación con usuarios y mejoras progresivas.
