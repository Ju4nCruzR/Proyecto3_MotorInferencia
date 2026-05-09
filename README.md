# Proyecto 3 - Motor de Inferencia Medica

Sistema experto de diagnostico medico basado en el algoritmo de Encadenamiento hacia Adelante (Forward Chaining) sobre una base de conocimiento en logica proposicional (Clausulas de Horn).

Desarrollado como proyecto aplicativo para el curso de Introduccion a la Inteligencia Artificial de la Pontificia Universidad Javeriana.

---

## Integrantes

- Juan Sebastian Cruz Rojas
- Juan Diego Soler Doria
- Santiago Andres Rayo Hernandez

**Profesor:** Ing. Julio Omar Palacio Nino, M.Sc.

---

## Descripcion del problema

El sistema resuelve el problema de consecuencia logica KB |= alpha:

- **KB (Base de Conocimiento):** conjunto de reglas de la forma P1 AND P2 AND ... AND Pn -> Q (Clausulas de Horn).
- **Hechos (Delta):** sintomas iniciales observados en el paciente.
- **Objetivo (alpha):** diagnostico medico que se desea verificar.

El motor determina si el objetivo se deriva logicamente de los hechos iniciales aplicando las reglas de la KB mediante encadenamiento hacia adelante.

---

## Estructura del proyecto

    Proyecto3_MotorInferencia/
    │
    ├── base_conocimiento.json   # Base de conocimiento con 55 reglas medicas
    ├── requirements.txt         # Dependencias del proyecto
    ├── README.md                # Este archivo
    │
    └── src/
        ├── motor_inferencia.py  # Motor de inferencia (Forward Chaining)
        └── interfaz.py          # Interfaz web Flask

---

## Requisitos

- Python 3.10 o superior
- pip

---

## Instalacion y ejecucion

1. Clonar el repositorio

    git clone https://github.com/Ju4nCruzR/Proyecto3_MotorInferencia.git
    cd Proyecto3_MotorInferencia

2. Instalar dependencias

    pip install -r requirements.txt

3. Ejecutar el motor desde consola (prueba rapida)

    python src/motor_inferencia.py

4. Ejecutar la interfaz web

    python src/interfaz.py

Luego abrir el navegador en: http://127.0.0.1:5000

---

## Uso de la interfaz

1. Seleccionar los sintomas del paciente en el panel izquierdo.
2. Escribir el diagnostico a verificar en el campo "Hipotesis a verificar".
3. Hacer clic en "Ejecutar motor".
4. El sistema muestra el veredicto (TRUE / FALSE), los hechos inferidos durante el proceso y la traza completa de reglas activadas.

---

## Base de conocimiento

El archivo base_conocimiento.json contiene 55 reglas organizadas en dominios:

Dominio                   | Ejemplos de diagnosticos
--------------------------|------------------------------------------------
Respiratorio              | Neumonia, Bronquitis, Crisis Asmatica
Infeccioso sistemico      | Gripe, Mononucleosis, Tuberculosis Pulmonar
Vectorial / tropical      | Dengue, Malaria, Zika, Chikungunya
Hepatico / abdominal      | Hepatitis A, Hepatitis B, Apendicitis Aguda
Neurologico / vascular    | Meningitis, ACV Isquemico, ACV Hemorragico
Metabolico                | Diabetes Tipo 1, Diabetes Tipo 2, Cetoacidosis
Urinario                  | Pielonefritis, Cistitis Hemorragica
Alergico / inmunologico   | Anafilaxia, Artritis Reumatoide
Oncologico                | Linfoma, Neoplasia Pulmonar

Todas las reglas cumplen las restricciones del enunciado:
- Clausulas de Horn (multiples antecedentes, un unico consecuente positivo).
- Sin ciclos.
- Sin reglas aisladas (todas conectadas con los sintomas de entrada).

---

## Ejemplo de ejecucion

Sintomas: Fiebre, Tos, Dificultad_Respiratoria
Hipotesis: Neumonia

Resultado: KB |= Neumonia -> True

Traza de inferencia:
  [R01] Fiebre, Tos -> Infeccion_Respiratoria
  [R02] Infeccion_Respiratoria, Dificultad_Respiratoria -> Neumonia

---

## Algoritmo implementado

El algoritmo de Forward Chaining sigue este flujo:

1. Cargar los sintomas iniciales en la memoria de trabajo.
2. Iterar sobre todas las reglas de la KB.
3. Si los antecedentes de una regla son subconjunto de la memoria de trabajo y el consecuente es nuevo, agregarlo y registrar la activacion en la traza.
4. Si el consecuente inferido es el objetivo, terminar con exito (True).
5. Si una iteracion completa no produce ningun hecho nuevo (punto fijo), terminar sin haber encontrado el objetivo (False).