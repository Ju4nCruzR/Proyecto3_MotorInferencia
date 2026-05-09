# =============================================================================
# motor_inferencia.py
# =============================================================================
# Modulo principal del sistema experto de diagnostico medico.
# Implementa el algoritmo de Encadenamiento hacia Adelante (Forward Chaining)
# sobre una base de conocimiento externa en formato JSON.
#
# El motor carga un conjunto de reglas logicas (Clausulas de Horn), recibe
# sintomas iniciales como hechos conocidos y determina si un diagnostico
# objetivo se deriva logicamente de dichos hechos aplicando las reglas
# disponibles hasta alcanzar un punto fijo.
#
# Estructura del proyecto:
#   - base_conocimiento.json : reglas logicas del dominio medico
#   - src/motor_inferencia.py : logica del motor (este archivo)
#   - src/interfaz.py         : interfaz web para interaccion con el usuario
# =============================================================================

import json


class Regla:
    """
    Representa una regla logica de la forma:
        antecedente_1 AND antecedente_2 AND ... AND antecedente_n -> consecuente
    Corresponde a una Clausula de Horn con un unico consecuente positivo.
    """

    def __init__(self, id_regla, antecedentes, consecuente):
        self.id_regla = id_regla
        # Se usa un conjunto para que la verificacion de subconjunto sea eficiente
        self.antecedentes = set(antecedentes)
        self.consecuente = consecuente

    def __str__(self):
        partes = " AND ".join(sorted(self.antecedentes))
        return f"{self.id_regla}: {partes} -> {self.consecuente}"


class MotorInferencia:
    """
    Motor de inferencia basado en Encadenamiento hacia Adelante.
    Mantiene una memoria de trabajo con los hechos conocidos y aplica
    las reglas de la base de conocimiento de forma iterativa hasta
    derivar el objetivo o alcanzar un punto fijo.
    """

    def __init__(self, ruta_kb):
        self.reglas = self.cargar_kb(ruta_kb)
        self.memoria_trabajo = set()
        # La traza guarda el historial de reglas activadas durante la inferencia
        self.traza = []

    def cargar_kb(self, ruta):
        """
        Lee el archivo JSON y construye la lista de objetos Regla.
        Si el archivo no existe o tiene un formato invalido, retorna una
        lista vacia y muestra el error por consola.
        """
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            reglas = [
                Regla(r.get('id'), r['antecedentes'], r['consecuente'])
                for r in datos['reglas']
            ]
            return reglas
        except Exception as e:
            print(f"Error al cargar la Base de Conocimiento: {e}")
            return []

    def ejecutar_inferencia(self, hechos_iniciales, objetivo):
        """
        Algoritmo de Encadenamiento hacia Adelante (Forward Chaining).

        Recibe los sintomas del paciente como hechos iniciales y un diagnostico
        objetivo a verificar. Aplica las reglas de la KB de forma iterativa
        hasta que el objetivo sea derivado (exito) o no se puedan inferir
        nuevos hechos (punto fijo, fracaso).

        Parametros:
            hechos_iniciales (list): sintomas observados en el paciente.
            objetivo (str): diagnostico que se desea verificar.

        Retorna:
            True  si KB |= objetivo (el objetivo es consecuencia logica).
            False si se alcanza el punto fijo sin haber derivado el objetivo.
        """

        # Se cargan los hechos iniciales en la memoria de trabajo
        self.memoria_trabajo = set(hechos_iniciales)
        self.traza = []

        # El ciclo continua mientras en la iteracion anterior se haya inferido
        # al menos un hecho nuevo. Cuando una iteracion completa no produce
        # ningun hecho nuevo, se alcanzo el punto fijo y el ciclo termina.
        hubo_cambios = True

        while hubo_cambios:
            # Al inicio de cada iteracion se asume que no habra cambios
            hubo_cambios = False

            for regla in self.reglas:
                # Se verifica si todos los antecedentes de la regla ya son
                # hechos conocidos en la memoria de trabajo
                if regla.antecedentes.issubset(self.memoria_trabajo):

                    # Solo se procesa si el consecuente aun no es conocido,
                    # para evitar registrar activaciones repetidas
                    if regla.consecuente not in self.memoria_trabajo:

                        # Se agrega el nuevo hecho a la memoria de trabajo
                        self.memoria_trabajo.add(regla.consecuente)

                        # Se marca que hubo cambio para que el ciclo continue
                        hubo_cambios = True

                        # Se registra la activacion en la traza de explicacion
                        self.traza.append({
                            "regla": regla.id_regla,
                            "antecedentes": list(regla.antecedentes),
                            "consecuente": regla.consecuente
                        })

                        # Si el hecho recien inferido es el objetivo, el
                        # algoritmo termina de inmediato con exito
                        if regla.consecuente == objetivo:
                            return True

        # Se llego al punto fijo sin haber derivado el objetivo
        return False

    def obtener_traza(self):
        """
        Retorna la traza de activaciones registrada durante la ultima
        ejecucion del motor. Cada entrada indica que regla se activo,
        cuales fueron sus antecedentes y que hecho nuevo fue inferido.
        """
        return self.traza

    def obtener_todos_los_diagnosticos(self, hechos_iniciales):
        """
        Ejecuta el motor sin un objetivo especifico y retorna todos los
        hechos que se pueden inferir a partir de los sintomas dados.
        Util para mostrar todos los diagnosticos posibles en la interfaz.
        """
        self.memoria_trabajo = set(hechos_iniciales)
        self.traza = []
        hubo_cambios = True

        while hubo_cambios:
            hubo_cambios = False
            for regla in self.reglas:
                if regla.antecedentes.issubset(self.memoria_trabajo):
                    if regla.consecuente not in self.memoria_trabajo:
                        self.memoria_trabajo.add(regla.consecuente)
                        hubo_cambios = True
                        self.traza.append({
                            "regla": regla.id_regla,
                            "antecedentes": list(regla.antecedentes),
                            "consecuente": regla.consecuente
                        })

        # Se retornan solo los hechos que no estaban en los sintomas iniciales,
        # es decir, los que fueron inferidos por el motor
        inferidos = self.memoria_trabajo - set(hechos_iniciales)
        return inferidos, self.traza


# =============================================================================
# Bloque de prueba directa
# Permite verificar el motor desde consola sin necesidad de la interfaz
# =============================================================================
if __name__ == "__main__":
    motor = MotorInferencia("base_conocimiento.json")

    sintomas = ["Fiebre", "Tos", "Dificultad_Respiratoria"]
    hipotesis = "Neumonia"

    print("--- Sistema Experto de Diagnostico Medico ---")
    print(f"Sintomas ingresados : {sintomas}")
    print(f"Hipotesis a verificar: {hipotesis}")

    resultado = motor.ejecutar_inferencia(sintomas, hipotesis)

    print(f"\nResultado: KB |= {hipotesis} -> {resultado}")

    if resultado:
        print("\nTraza de inferencia:")
        for paso in motor.obtener_traza():
            ants = ", ".join(paso["antecedentes"])
            print(f"  [{paso['regla']}] {ants} -> {paso['consecuente']}")