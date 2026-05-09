# =============================================================================
# interfaz.py
# =============================================================================
# Modulo de interfaz web del sistema experto de diagnostico medico.
# Implementa un servidor Flask que expone el motor de inferencia a traves
# de una API REST y sirve una interfaz visual para que el usuario pueda
# seleccionar sintomas, ejecutar el motor y visualizar los resultados
# junto con la traza de inferencia paso a paso.
#
# Rutas disponibles:
#   GET  /              -> pagina principal con la interfaz
#   GET  /api/sintomas  -> lista de todos los sintomas disponibles en la KB
#   POST /api/inferir   -> ejecuta el motor y retorna el resultado con traza
# =============================================================================

import sys
import os
import json
from flask import Flask, request, jsonify, render_template_string

# Se agrega la raiz del proyecto al path para poder importar el motor
# independientemente de desde donde se ejecute este archivo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.motor_inferencia import MotorInferencia

app = Flask(__name__)

# Ruta al archivo de la base de conocimiento, relativa a la raiz del proyecto
RUTA_KB = os.path.join(os.path.dirname(__file__), '..', 'base_conocimiento.json')

# Se instancia el motor una sola vez al arrancar el servidor para no
# recargar el archivo JSON en cada peticion
motor = MotorInferencia(RUTA_KB)


def obtener_sintomas_disponibles():
    """
    Recorre todas las reglas de la KB y extrae los terminos que aparecen
    como antecedentes. Estos son los sintomas que el usuario puede ingresar,
    a diferencia de los consecuentes que son hechos inferidos por el motor.
    """
    sintomas = set()
    for regla in motor.reglas:
        for antecedente in regla.antecedentes:
            sintomas.add(antecedente)
    return sorted(list(sintomas))


# =============================================================================
# Plantilla HTML de la interfaz
# Se define aqui mismo para mantener el proyecto en un solo archivo por modulo
# y no requerir una carpeta templates separada
# =============================================================================
PLANTILLA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema Experto de Diagnostico Medico</title>
    <style>
        /* ------------------------------------------------------------------ */
        /* Variables y reset general                                           */
        /* ------------------------------------------------------------------ */
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap');

        :root {
            --bg:         #0a0e1a;
            --bg-card:    #111827;
            --bg-hover:   #1a2235;
            --accent:     #00d4ff;
            --accent-dim: #0099bb;
            --success:    #00e5a0;
            --danger:     #ff4d6d;
            --warning:    #ffd166;
            --text:       #e8eaf0;
            --text-muted: #8892a4;
            --border:     #1e2d40;
            --radius:     8px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'DM Mono', monospace;
            min-height: 100vh;
        }

        /* ------------------------------------------------------------------ */
        /* Encabezado                                                          */
        /* ------------------------------------------------------------------ */
        header {
            border-bottom: 1px solid var(--border);
            padding: 28px 48px;
            display: flex;
            align-items: baseline;
            gap: 16px;
        }

        header h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 1.6rem;
            color: var(--accent);
            letter-spacing: 0.5px;
        }

        header span {
            font-size: 0.75rem;
            color: var(--text-muted);
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* ------------------------------------------------------------------ */
        /* Layout principal                                                    */
        /* ------------------------------------------------------------------ */
        main {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 0;
            height: calc(100vh - 81px);
        }

        /* ------------------------------------------------------------------ */
        /* Panel izquierdo: seleccion de sintomas                              */
        /* ------------------------------------------------------------------ */
        .panel-sintomas {
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .panel-header {
            padding: 20px 24px 12px;
            border-bottom: 1px solid var(--border);
        }

        .panel-header h2 {
            font-size: 0.7rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .buscador {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 8px 12px;
            color: var(--text);
            font-family: 'DM Mono', monospace;
            font-size: 0.8rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .buscador:focus { border-color: var(--accent); }

        .lista-sintomas {
            flex: 1;
            overflow-y: auto;
            padding: 8px 12px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .item-sintoma {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 7px 10px;
            border-radius: var(--radius);
            cursor: pointer;
            transition: background 0.15s;
            font-size: 0.78rem;
            color: var(--text-muted);
            user-select: none;
        }

        .item-sintoma:hover { background: var(--bg-hover); color: var(--text); }

        .item-sintoma.seleccionado {
            background: rgba(0, 212, 255, 0.08);
            color: var(--accent);
        }

        .item-sintoma .checkbox {
            width: 14px;
            height: 14px;
            border: 1px solid var(--border);
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: all 0.15s;
        }

        .item-sintoma.seleccionado .checkbox {
            background: var(--accent);
            border-color: var(--accent);
        }

        .item-sintoma.seleccionado .checkbox::after {
            content: '';
            width: 6px;
            height: 4px;
            border-left: 2px solid #000;
            border-bottom: 2px solid #000;
            transform: rotate(-45deg) translateY(-1px);
            display: block;
        }

        /* ------------------------------------------------------------------ */
        /* Panel derecho: configuracion y resultado                            */
        /* ------------------------------------------------------------------ */
        .panel-resultado {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .configuracion {
            padding: 24px 36px;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 16px;
            align-items: flex-end;
        }

        .campo {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex: 1;
        }

        .campo label {
            font-size: 0.65rem;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .campo input {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 9px 14px;
            color: var(--text);
            font-family: 'DM Mono', monospace;
            font-size: 0.82rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .campo input:focus { border-color: var(--accent); }

        .btn-inferir {
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: var(--radius);
            padding: 10px 28px;
            font-family: 'DM Mono', monospace;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: background 0.2s, transform 0.1s;
            white-space: nowrap;
        }

        .btn-inferir:hover { background: var(--accent-dim); }
        .btn-inferir:active { transform: scale(0.97); }

        .btn-limpiar {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 10px 20px;
            font-family: 'DM Mono', monospace;
            font-size: 0.8rem;
            cursor: pointer;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .btn-limpiar:hover { border-color: var(--text-muted); color: var(--text); }

        /* ------------------------------------------------------------------ */
        /* Area de resultados                                                  */
        /* ------------------------------------------------------------------ */
        .area-resultado {
            flex: 1;
            overflow-y: auto;
            padding: 28px 36px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        /* Estado inicial */
        .estado-inicial {
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            color: var(--text-muted);
        }

        .estado-inicial .icono {
            font-size: 2.5rem;
            opacity: 0.3;
        }

        .estado-inicial p {
            font-size: 0.78rem;
            letter-spacing: 1px;
        }

        /* Tarjeta de veredicto */
        .veredicto {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 20px 24px;
            border-radius: var(--radius);
            margin-bottom: 28px;
            border: 1px solid;
        }

        .veredicto.exito {
            background: rgba(0, 229, 160, 0.06);
            border-color: var(--success);
        }

        .veredicto.fracaso {
            background: rgba(255, 77, 109, 0.06);
            border-color: var(--danger);
        }

        .veredicto .indicador {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .veredicto.exito .indicador { background: var(--success); box-shadow: 0 0 10px var(--success); }
        .veredicto.fracaso .indicador { background: var(--danger); box-shadow: 0 0 10px var(--danger); }

        .veredicto .texto h3 {
            font-family: 'DM Serif Display', serif;
            font-size: 1.1rem;
            margin-bottom: 4px;
        }

        .veredicto.exito .texto h3 { color: var(--success); }
        .veredicto.fracaso .texto h3 { color: var(--danger); }

        .veredicto .texto p {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Seccion de traza */
        .seccion-titulo {
            font-size: 0.65rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }

        .paso-traza {
            display: grid;
            grid-template-columns: 60px 1fr 16px 1fr;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: var(--radius);
            margin-bottom: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            font-size: 0.75rem;
            transition: border-color 0.2s;
        }

        .paso-traza:hover { border-color: var(--accent-dim); }

        .paso-traza .id-regla {
            color: var(--warning);
            font-weight: 500;
        }

        .paso-traza .antecedentes {
            color: var(--text-muted);
        }

        .paso-traza .flecha {
            color: var(--border);
            text-align: center;
        }

        .paso-traza .consecuente {
            color: var(--accent);
            font-weight: 500;
        }

        /* Chips de sintomas seleccionados */
        .chips-container {
            padding: 10px 24px;
            border-top: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            min-height: 44px;
            align-items: center;
        }

        .chip {
            background: rgba(0, 212, 255, 0.1);
            color: var(--accent);
            border: 1px solid rgba(0, 212, 255, 0.25);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 0.7rem;
            cursor: pointer;
            transition: all 0.15s;
        }

        .chip:hover {
            background: rgba(255, 77, 109, 0.1);
            color: var(--danger);
            border-color: rgba(255, 77, 109, 0.25);
        }

        .chips-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            letter-spacing: 1px;
            margin-right: 4px;
        }

        /* Seccion de todos los diagnosticos inferidos */
        .diagnosticos-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 28px;
        }

        .tag-diagnostico {
            background: rgba(0, 229, 160, 0.08);
            color: var(--success);
            border: 1px solid rgba(0, 229, 160, 0.2);
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 0.72rem;
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-muted);
            font-size: 0.78rem;
        }

        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

    </style>
</head>
<body>

<header>
    <h1>Sistema Experto de Diagnostico Medico</h1>
    <span>Forward Chaining &mdash; Logica Proposicional</span>
</header>

<main>

    <!-- Panel izquierdo: sintomas -->
    <div class="panel-sintomas">
        <div class="panel-header">
            <h2>Sintomas del paciente</h2>
            <input
                class="buscador"
                type="text"
                id="buscador"
                placeholder="Buscar sintoma..."
                oninput="filtrarSintomas(this.value)"
            >
        </div>
        <div class="lista-sintomas" id="listaSintomas">
            <!-- Se llena dinamicamente desde la API -->
        </div>
        <div class="chips-container" id="chipsContainer">
            <span class="chips-label">Seleccionados:</span>
        </div>
    </div>

    <!-- Panel derecho: configuracion y resultado -->
    <div class="panel-resultado">
        <div class="configuracion">
            <div class="campo">
                <label>Hipotesis a verificar</label>
                <input
                    type="text"
                    id="inputObjetivo"
                    placeholder="ej. Neumonia"
                    list="sugerenciasObjetivo"
                >
                <datalist id="sugerenciasObjetivo"></datalist>
            </div>
            <button class="btn-inferir" onclick="ejecutarInferencia()">Ejecutar</button>
            <button class="btn-limpiar" onclick="limpiarTodo()">Limpiar</button>
        </div>
        <div class="area-resultado" id="areaResultado">
            <div class="estado-inicial">
                <div class="icono">&#9636;</div>
                <p>Selecciona sintomas y define una hipotesis para ejecutar el motor.</p>
            </div>
        </div>
    </div>

</main>

<script>
    // Lista completa de sintomas cargada desde la API
    let todosSintomas = [];
    // Conjunto de sintomas actualmente seleccionados por el usuario
    let sintomasSeleccionados = new Set();

    // Al cargar la pagina se obtienen los sintomas disponibles desde la KB
    document.addEventListener('DOMContentLoaded', () => {
        cargarSintomas();
        cargarSugerenciasObjetivo();
    });

    // Obtiene la lista de sintomas desde el endpoint de la API
    function cargarSintomas() {
        fetch('/api/sintomas')
            .then(r => r.json())
            .then(data => {
                todosSintomas = data.sintomas;
                renderizarSintomas(todosSintomas);
            });
    }

    // Carga los posibles objetivos (consecuentes de la KB) para el datalist
    function cargarSugerenciasObjetivo() {
        fetch('/api/consecuentes')
            .then(r => r.json())
            .then(data => {
                const dl = document.getElementById('sugerenciasObjetivo');
                data.consecuentes.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c;
                    dl.appendChild(opt);
                });
            });
    }

    // Dibuja los items de sintoma en la lista del panel izquierdo
    function renderizarSintomas(lista) {
        const contenedor = document.getElementById('listaSintomas');
        contenedor.innerHTML = '';
        lista.forEach(s => {
            const div = document.createElement('div');
            div.className = 'item-sintoma' + (sintomasSeleccionados.has(s) ? ' seleccionado' : '');
            div.dataset.sintoma = s;
            div.innerHTML = `<div class="checkbox"></div><span>${s.replace(/_/g, ' ')}</span>`;
            div.addEventListener('click', () => toggleSintoma(s, div));
            contenedor.appendChild(div);
        });
    }

    // Activa o desactiva un sintoma al hacer clic
    function toggleSintoma(sintoma, elemento) {
        if (sintomasSeleccionados.has(sintoma)) {
            sintomasSeleccionados.delete(sintoma);
            elemento.classList.remove('seleccionado');
        } else {
            sintomasSeleccionados.add(sintoma);
            elemento.classList.add('seleccionado');
        }
        actualizarChips();
    }

    // Actualiza los chips de sintomas seleccionados en la parte inferior del panel
    function actualizarChips() {
        const contenedor = document.getElementById('chipsContainer');
        contenedor.innerHTML = '<span class="chips-label">Seleccionados:</span>';
        sintomasSeleccionados.forEach(s => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = s.replace(/_/g, ' ');
            // Al hacer clic en un chip se deselecciona el sintoma
            chip.addEventListener('click', () => {
                sintomasSeleccionados.delete(s);
                actualizarChips();
                renderizarSintomas(todosSintomas);
            });
            contenedor.appendChild(chip);
        });
    }

    // Filtra los sintomas visibles segun el texto del buscador
    function filtrarSintomas(texto) {
        const filtrados = todosSintomas.filter(s =>
            s.toLowerCase().replace(/_/g, ' ').includes(texto.toLowerCase())
        );
        renderizarSintomas(filtrados);
    }

    // Envia la peticion al motor y muestra el resultado
    function ejecutarInferencia() {
        const objetivo = document.getElementById('inputObjetivo').value.trim();
        const sintomas = Array.from(sintomasSeleccionados);

        if (sintomas.length === 0) {
            mostrarError('Debes seleccionar al menos un sintoma.');
            return;
        }
        if (!objetivo) {
            mostrarError('Debes ingresar una hipotesis a verificar.');
            return;
        }

        // Se muestra indicador de carga mientras el motor procesa
        document.getElementById('areaResultado').innerHTML =
            '<div class="loading"><div class="spinner"></div><span>Ejecutando motor de inferencia...</span></div>';

        fetch('/api/inferir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sintomas: sintomas, objetivo: objetivo })
        })
        .then(r => r.json())
        .then(data => mostrarResultado(data))
        .catch(() => mostrarError('Error al conectar con el motor.'));
    }

    // Construye y muestra el panel de resultados con veredicto y traza
    function mostrarResultado(data) {
        const area = document.getElementById('areaResultado');
        const exito = data.resultado;

        let html = '';

        // Veredicto principal
        html += `
        <div class="veredicto ${exito ? 'exito' : 'fracaso'}">
            <div class="indicador"></div>
            <div class="texto">
                <h3>${exito ? 'Hipotesis confirmada' : 'Hipotesis no derivable'}</h3>
                <p>
                    ${exito
                        ? `KB |= <strong>${data.objetivo}</strong> es consecuencia logica de los sintomas dados.`
                        : `No fue posible derivar <strong>${data.objetivo}</strong> con las reglas disponibles y los sintomas dados.`
                    }
                </p>
            </div>
        </div>`;

        // Diagnosticos intermedios inferidos
        if (data.diagnosticos_inferidos && data.diagnosticos_inferidos.length > 0) {
            html += `<p class="seccion-titulo">Hechos inferidos durante el proceso</p>`;
            html += `<div class="diagnosticos-grid">`;
            data.diagnosticos_inferidos.forEach(d => {
                html += `<span class="tag-diagnostico">${d.replace(/_/g, ' ')}</span>`;
            });
            html += `</div>`;
        }

        // Traza de activacion de reglas
        if (data.traza && data.traza.length > 0) {
            html += `<p class="seccion-titulo">Traza de inferencia &mdash; ${data.traza.length} regla(s) activada(s)</p>`;
            data.traza.forEach(paso => {
                const ants = paso.antecedentes.map(a => a.replace(/_/g, ' ')).join(' AND ');
                const cons = paso.consecuente.replace(/_/g, ' ');
                html += `
                <div class="paso-traza">
                    <span class="id-regla">${paso.regla}</span>
                    <span class="antecedentes">${ants}</span>
                    <span class="flecha">&#8594;</span>
                    <span class="consecuente">${cons}</span>
                </div>`;
            });
        } else {
            html += `<p class="seccion-titulo">No se activo ninguna regla</p>`;
        }

        area.innerHTML = html;
    }

    function mostrarError(mensaje) {
        document.getElementById('areaResultado').innerHTML =
            `<div class="veredicto fracaso">
                <div class="indicador"></div>
                <div class="texto"><h3>Error</h3><p>${mensaje}</p></div>
            </div>`;
    }

    function limpiarTodo() {
        sintomasSeleccionados.clear();
        document.getElementById('inputObjetivo').value = '';
        actualizarChips();
        renderizarSintomas(todosSintomas);
        document.getElementById('areaResultado').innerHTML = `
            <div class="estado-inicial">
                <div class="icono">&#9636;</div>
                <p>Selecciona sintomas y define una hipotesis para ejecutar el motor.</p>
            </div>`;
    }
</script>

</body>
</html>
"""


@app.route('/')
def index():
    """Sirve la pagina principal de la interfaz."""
    return render_template_string(PLANTILLA_HTML)


@app.route('/api/sintomas')
def api_sintomas():
    """
    Retorna la lista de todos los sintomas disponibles en la KB.
    Estos corresponden a los terminos que aparecen como antecedentes
    en al menos una regla.
    """
    sintomas = obtener_sintomas_disponibles()
    return jsonify({"sintomas": sintomas})


@app.route('/api/consecuentes')
def api_consecuentes():
    """
    Retorna la lista de todos los consecuentes de la KB.
    Se usan como sugerencias para el campo de hipotesis en la interfaz.
    """
    consecuentes = sorted(list(set(r.consecuente for r in motor.reglas)))
    return jsonify({"consecuentes": consecuentes})


@app.route('/api/inferir', methods=['POST'])
def api_inferir():
    """
    Recibe sintomas y objetivo, ejecuta el motor de inferencia y retorna
    el resultado junto con la traza de activacion de reglas y los
    diagnosticos intermedios inferidos durante el proceso.
    """
    datos = request.get_json()
    sintomas = datos.get('sintomas', [])
    objetivo = datos.get('objetivo', '')

    if not sintomas or not objetivo:
        return jsonify({"error": "Parametros incompletos"}), 400

    # Se ejecuta el motor con el objetivo especifico
    resultado = motor.ejecutar_inferencia(sintomas, objetivo)
    traza = motor.obtener_traza()

    # Se ejecuta nuevamente sin objetivo para obtener todos los hechos inferidos
    inferidos, _ = motor.obtener_todos_los_diagnosticos(sintomas)

    return jsonify({
        "resultado": resultado,
        "objetivo": objetivo,
        "traza": traza,
        "diagnosticos_inferidos": sorted(list(inferidos))
    })


if __name__ == '__main__':
    # debug=False para produccion; True para desarrollo local
    app.run(debug=True, port=5000)