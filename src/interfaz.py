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
#   GET  /               -> pagina principal con la interfaz
#   GET  /api/sintomas   -> lista de todos los sintomas disponibles en la KB
#   GET  /api/consecuentes -> lista de todos los consecuentes de la KB
#   POST /api/inferir    -> ejecuta el motor y retorna el resultado con traza
# =============================================================================

import sys
import os
import json
from flask import Flask, request, jsonify, render_template_string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.motor_inferencia import MotorInferencia

app = Flask(__name__)

RUTA_KB = os.path.join(os.path.dirname(__file__), '..', 'base_conocimiento.json')

motor = MotorInferencia(RUTA_KB)


def obtener_sintomas_disponibles():
    sintomas = set()
    for regla in motor.reglas:
        for antecedente in regla.antecedentes:
            sintomas.add(antecedente)
    return sorted(list(sintomas))


PLANTILLA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema Experto de Diagnostico Medico</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&display=swap');

        :root {
            --bg:          #f4f6fb;
            --bg-card:     #ffffff;
            --bg-hover:    #eef1fb;
            --bg-sidebar:  #ffffff;
            --accent:      #4f6ef7;
            --accent-dim:  #3a57d4;
            --accent-soft: #eef0fe;
            --success:     #0ea96e;
            --success-soft:#e6f7f1;
            --danger:      #e53e5a;
            --danger-soft: #fdedf0;
            --warning:     #f59e0b;
            --text:        #1a1d2e;
            --text-muted:  #6b7280;
            --text-light:  #9ca3af;
            --border:      #e4e8f2;
            --radius:      10px;
            --radius-lg:   14px;
            --shadow-sm:   0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
            --shadow-md:   0 4px 12px rgba(0,0,0,0.08);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            font-size: 14px;
        }

        /* ---- Encabezado ---- */
        header {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 0 36px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-sm);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-dot {
            width: 32px;
            height: 32px;
            background: var(--accent);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 15px;
            font-weight: 600;
            flex-shrink: 0;
        }

        header h1 {
            font-size: 15px;
            font-weight: 600;
            color: var(--text);
            letter-spacing: -0.2px;
        }

        .header-badge {
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 11px;
            font-weight: 500;
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.3px;
        }

        /* ---- Layout ---- */
        main {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: calc(100vh - 60px);
        }

        /* ---- Panel izquierdo ---- */
        .panel-sintomas {
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .panel-header {
            padding: 18px 16px 12px;
            border-bottom: 1px solid var(--border);
        }

        .panel-header h2 {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .buscador-wrap {
            position: relative;
        }

        .buscador-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
            font-size: 14px;
            pointer-events: none;
        }

        .buscador {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 8px 12px 8px 32px;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .buscador:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(79,110,247,0.1);
        }

        .contador-seleccionados {
            padding: 8px 16px;
            font-size: 12px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            background: var(--bg);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .contador-badge {
            background: var(--accent);
            color: white;
            font-size: 11px;
            font-weight: 600;
            padding: 1px 8px;
            border-radius: 20px;
            min-width: 22px;
            text-align: center;
        }

        .lista-sintomas {
            flex: 1;
            overflow-y: auto;
            padding: 6px 8px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .item-sintoma {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 7px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.12s;
            font-size: 13px;
            color: var(--text-muted);
            user-select: none;
        }

        .item-sintoma:hover {
            background: var(--bg-hover);
            color: var(--text);
        }

        .item-sintoma.seleccionado {
            background: var(--accent-soft);
            color: var(--accent);
        }

        .checkbox {
            width: 16px;
            height: 16px;
            border: 1.5px solid var(--border);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: all 0.15s;
            background: white;
        }

        .item-sintoma.seleccionado .checkbox {
            background: var(--accent);
            border-color: var(--accent);
        }

        .item-sintoma.seleccionado .checkbox::after {
            content: '';
            width: 8px;
            height: 5px;
            border-left: 2px solid white;
            border-bottom: 2px solid white;
            transform: rotate(-45deg) translateY(-1px);
            display: block;
        }

        /* ---- Panel derecho ---- */
        .panel-resultado {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg);
        }

        .configuracion {
            padding: 16px 28px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 12px;
            align-items: flex-end;
            box-shadow: var(--shadow-sm);
        }

        .campo {
            display: flex;
            flex-direction: column;
            gap: 5px;
            flex: 1;
        }

        .campo label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .campo input {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 9px 14px;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .campo input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(79,110,247,0.1);
        }

        .btn-inferir {
            background: var(--accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 10px 24px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            letter-spacing: 0.3px;
            transition: background 0.2s, transform 0.1s, box-shadow 0.2s;
            box-shadow: 0 2px 8px rgba(79,110,247,0.3);
            white-space: nowrap;
        }

        .btn-inferir:hover {
            background: var(--accent-dim);
            box-shadow: 0 4px 12px rgba(79,110,247,0.4);
        }

        .btn-inferir:active { transform: scale(0.97); }

        .btn-limpiar {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 10px 18px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .btn-limpiar:hover {
            border-color: var(--text-muted);
            color: var(--text);
            background: var(--bg-hover);
        }

        /* ---- Chips ---- */
        .chips-bar {
            padding: 8px 28px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
            min-height: 42px;
        }

        .chips-label {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-light);
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-right: 4px;
        }

        .chip {
            background: var(--accent-soft);
            color: var(--accent);
            border: 1px solid rgba(79,110,247,0.2);
            border-radius: 20px;
            padding: 3px 10px 3px 10px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .chip:hover {
            background: var(--danger-soft);
            color: var(--danger);
            border-color: rgba(229,62,90,0.2);
        }

        .chip-x {
            font-size: 11px;
            opacity: 0.6;
        }

        /* ---- Area de resultados ---- */
        .area-resultado {
            flex: 1;
            overflow-y: auto;
            padding: 28px 36px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }

        .estado-inicial {
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            color: var(--text-light);
            text-align: center;
        }

        .estado-inicial .icono-grande {
            width: 56px;
            height: 56px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 6px;
            box-shadow: var(--shadow-sm);
        }

        .estado-inicial p {
            font-size: 13px;
            max-width: 300px;
            line-height: 1.6;
        }

        /* ---- Veredicto ---- */
        .veredicto {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            padding: 20px 24px;
            border-radius: var(--radius-lg);
            margin-bottom: 24px;
            border: 1px solid;
            box-shadow: var(--shadow-sm);
        }

        .veredicto.exito {
            background: var(--success-soft);
            border-color: rgba(14,169,110,0.25);
        }

        .veredicto.fracaso {
            background: var(--danger-soft);
            border-color: rgba(229,62,90,0.25);
        }

        .veredicto-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .veredicto.exito .veredicto-icon {
            background: rgba(14,169,110,0.15);
            color: var(--success);
        }

        .veredicto.fracaso .veredicto-icon {
            background: rgba(229,62,90,0.15);
            color: var(--danger);
        }

        .veredicto .texto h3 {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .veredicto.exito .texto h3 { color: var(--success); }
        .veredicto.fracaso .texto h3 { color: var(--danger); }

        .veredicto .texto p {
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        .veredicto .texto p strong {
            color: var(--text);
            font-weight: 600;
        }

        /* ---- Secciones ---- */
        .seccion-titulo {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .seccion-count {
            background: var(--bg-hover);
            color: var(--accent);
            font-size: 10px;
            font-weight: 600;
            padding: 1px 8px;
            border-radius: 20px;
        }

        /* ---- Tags de diagnosticos ---- */
        .diagnosticos-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 28px;
        }

        .tag-diagnostico {
            background: var(--success-soft);
            color: var(--success);
            border: 1px solid rgba(14,169,110,0.2);
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 500;
        }

        /* ---- Traza ---- */
        .paso-traza {
            display: grid;
            grid-template-columns: 56px 1fr 20px 1fr;
            align-items: center;
            gap: 12px;
            padding: 11px 16px;
            border-radius: var(--radius);
            margin-bottom: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            font-size: 13px;
            transition: border-color 0.15s, box-shadow 0.15s;
            box-shadow: var(--shadow-sm);
        }

        .paso-traza:hover {
            border-color: rgba(79,110,247,0.3);
            box-shadow: 0 2px 8px rgba(79,110,247,0.08);
        }

        .id-regla {
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 5px;
            text-align: center;
        }

        .antecedentes { color: var(--text-muted); font-size: 12px; }
        .flecha { color: var(--text-light); text-align: center; font-size: 14px; }
        .consecuente { color: var(--accent); font-weight: 600; font-size: 12px; }

        /* ---- Loading ---- */
        .loading {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-muted);
            font-size: 13px;
            padding: 40px 0;
            justify-content: center;
        }

        .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .sin-resultados {
            text-align: center;
            color: var(--text-light);
            font-size: 13px;
            padding: 24px 0;
        }
    </style>
</head>
<body>

<header>
    <div class="header-left">
        <div class="logo-dot">Dx</div>
        <h1>Sistema Experto de Diagnostico Medico</h1>
    </div>
    <span class="header-badge">Forward Chaining</span>
</header>

<main>

    <div class="panel-sintomas">
        <div class="panel-header">
            <h2>Sintomas del paciente</h2>
            <div class="buscador-wrap">
                <span class="buscador-icon">&#128269;</span>
                <input
                    class="buscador"
                    type="text"
                    id="buscador"
                    placeholder="Buscar sintoma..."
                    oninput="filtrarSintomas(this.value)"
                >
            </div>
        </div>
        <div class="contador-seleccionados">
            <span>Seleccionados</span>
            <span class="contador-badge" id="contadorBadge">0</span>
        </div>
        <div class="lista-sintomas" id="listaSintomas"></div>
    </div>

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
            <button class="btn-inferir" onclick="ejecutarInferencia()">Ejecutar motor</button>
            <button class="btn-limpiar" onclick="limpiarTodo()">Limpiar</button>
        </div>

        <div class="chips-bar" id="chipsBar">
            <span class="chips-label">Sintomas:</span>
            <span style="font-size:12px; color: var(--text-light);" id="chipsVacio">Ninguno seleccionado</span>
        </div>

        <div class="area-resultado" id="areaResultado">
            <div class="estado-inicial">
                <div class="icono-grande">&#129657;</div>
                <p>Selecciona los sintomas del paciente y define una hipotesis para ejecutar el motor de inferencia.</p>
            </div>
        </div>
    </div>

</main>

<script>
    let todosSintomas = [];
    let sintomasSeleccionados = new Set();

    document.addEventListener('DOMContentLoaded', () => {
        cargarSintomas();
        cargarSugerenciasObjetivo();
    });

    function cargarSintomas() {
        fetch('/api/sintomas')
            .then(r => r.json())
            .then(data => {
                todosSintomas = data.sintomas;
                renderizarSintomas(todosSintomas);
            });
    }

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

    function renderizarSintomas(lista) {
        const contenedor = document.getElementById('listaSintomas');
        contenedor.innerHTML = '';

        if (lista.length === 0) {
            contenedor.innerHTML = '<p class="sin-resultados">No se encontraron sintomas.</p>';
            return;
        }

        lista.forEach(s => {
            const div = document.createElement('div');
            div.className = 'item-sintoma' + (sintomasSeleccionados.has(s) ? ' seleccionado' : '');
            div.dataset.sintoma = s;
            div.innerHTML = `<div class="checkbox"></div><span>${s.replace(/_/g, ' ')}</span>`;
            div.addEventListener('click', () => toggleSintoma(s, div));
            contenedor.appendChild(div);
        });
    }

    function toggleSintoma(sintoma, elemento) {
        if (sintomasSeleccionados.has(sintoma)) {
            sintomasSeleccionados.delete(sintoma);
            elemento.classList.remove('seleccionado');
        } else {
            sintomasSeleccionados.add(sintoma);
            elemento.classList.add('seleccionado');
        }
        actualizarChips();
        actualizarContador();
    }

    function actualizarContador() {
        document.getElementById('contadorBadge').textContent = sintomasSeleccionados.size;
    }

    function actualizarChips() {
        const bar = document.getElementById('chipsBar');
        const vacio = document.getElementById('chipsVacio');
        bar.innerHTML = '<span class="chips-label">Sintomas:</span>';

        if (sintomasSeleccionados.size === 0) {
            bar.innerHTML += '<span style="font-size:12px; color: var(--text-light);" id="chipsVacio">Ninguno seleccionado</span>';
            return;
        }

        sintomasSeleccionados.forEach(s => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.innerHTML = `${s.replace(/_/g, ' ')} <span class="chip-x">x</span>`;
            chip.addEventListener('click', () => {
                sintomasSeleccionados.delete(s);
                actualizarChips();
                actualizarContador();
                renderizarSintomas(todosSintomas);
            });
            bar.appendChild(chip);
        });
    }

    function filtrarSintomas(texto) {
        const filtrados = todosSintomas.filter(s =>
            s.toLowerCase().replace(/_/g, ' ').includes(texto.toLowerCase())
        );
        renderizarSintomas(filtrados);
    }

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

    function mostrarResultado(data) {
        const area = document.getElementById('areaResultado');
        const exito = data.resultado;

        let html = '';

        html += `
        <div class="veredicto ${exito ? 'exito' : 'fracaso'}">
            <div class="veredicto-icon">${exito ? '&#10003;' : '&#10007;'}</div>
            <div class="texto">
                <h3>${exito ? 'Hipotesis confirmada' : 'Hipotesis no derivable'}</h3>
                <p>
                    ${exito
                        ? `KB |= <strong>${data.objetivo}</strong> es consecuencia logica de los sintomas dados.`
                        : `No fue posible derivar <strong>${data.objetivo}</strong> con las reglas disponibles y los sintomas ingresados.`
                    }
                </p>
            </div>
        </div>`;

        if (data.diagnosticos_inferidos && data.diagnosticos_inferidos.length > 0) {
            html += `<p class="seccion-titulo">Hechos inferidos durante el proceso <span class="seccion-count">${data.diagnosticos_inferidos.length}</span></p>`;
            html += `<div class="diagnosticos-grid">`;
            data.diagnosticos_inferidos.forEach(d => {
                html += `<span class="tag-diagnostico">${d.replace(/_/g, ' ')}</span>`;
            });
            html += `</div>`;
        }

        if (data.traza && data.traza.length > 0) {
            html += `<p class="seccion-titulo">Traza de inferencia <span class="seccion-count">${data.traza.length} regla(s) activada(s)</span></p>`;
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
        document.getElementById('areaResultado').innerHTML = `
            <div class="veredicto fracaso">
                <div class="veredicto-icon">&#10007;</div>
                <div class="texto"><h3>Error</h3><p>${mensaje}</p></div>
            </div>`;
    }

    function limpiarTodo() {
        sintomasSeleccionados.clear();
        document.getElementById('inputObjetivo').value = '';
        actualizarChips();
        actualizarContador();
        renderizarSintomas(todosSintomas);
        document.getElementById('areaResultado').innerHTML = `
            <div class="estado-inicial">
                <div class="icono-grande">&#129657;</div>
                <p>Selecciona los sintomas del paciente y define una hipotesis para ejecutar el motor de inferencia.</p>
            </div>`;
    }
</script>

</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(PLANTILLA_HTML)


@app.route('/api/sintomas')
def api_sintomas():
    sintomas = obtener_sintomas_disponibles()
    return jsonify({"sintomas": sintomas})


@app.route('/api/consecuentes')
def api_consecuentes():
    consecuentes = sorted(list(set(r.consecuente for r in motor.reglas)))
    return jsonify({"consecuentes": consecuentes})


@app.route('/api/inferir', methods=['POST'])
def api_inferir():
    datos = request.get_json()
    sintomas = datos.get('sintomas', [])
    objetivo = datos.get('objetivo', '')

    if not sintomas or not objetivo:
        return jsonify({"error": "Parametros incompletos"}), 400

    resultado = motor.ejecutar_inferencia(sintomas, objetivo)
    traza = motor.obtener_traza()
    inferidos, _ = motor.obtener_todos_los_diagnosticos(sintomas)

    return jsonify({
        "resultado": resultado,
        "objetivo": objetivo,
        "traza": traza,
        "diagnosticos_inferidos": sorted(list(inferidos))
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)