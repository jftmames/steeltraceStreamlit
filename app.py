import streamlit as st
import json
from pathlib import Path
import subprocess
import os
import glob

# --- Configuración de Paths ---
# Asegura que el Directorio de Trabajo Actual (CWD) sea la raíz del repositorio
ROOT_DIR = Path(__file__).parent.resolve()
os.chdir(ROOT_DIR)

DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
SAMPLE_FILES = [f.name for f in DATA_PATH.glob("*.json")]

# --- Utilidades ---

def load_file_content(file_path: Path):
    """Carga y retorna el contenido de un archivo como texto o JSON."""
    try:
        if file_path.suffix.lower() == '.json' or file_path.suffix.lower() == '.jsonl':
            # Intenta cargar el contenido como texto para mostrarlo en un bloque de código
            return file_path.read_text(encoding="utf-8")
        else:
            # Para logs o otros formatos
            return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        st.warning(f"El archivo {file_path.name} aún no existe. Ejecuta el paso anterior.")
        return None
    except Exception as e:
        st.error(f"Error al leer {file_path.name}: {e}")
        return None

def run_script_and_capture_output(script_name):
    """Ejecuta un script del pipeline y captura el output."""
    script_path = ROOT_DIR / "scripts" / script_name
    st.info(f"Ejecutando: `python {script_name}`...")
    
    try:
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True, 
            text=True, 
            check=True, # Lanza CalledProcessError si el código de retorno no es cero
            timeout=10 # Tiempo límite de ejecución
        )
        st.success("✅ Ejecución completada con éxito.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Error en la ejecución de {script_name}")
        st.code(f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}", language="bash")
        return None
    except FileNotFoundError:
        st.error(f"❌ Script no encontrado en la ruta: {script_path}")
        return None

# --- Interfaz Streamlit ---
st.set_page_config(layout="wide", page_title="STEELTRACE™ CSRD+AI - PoC")

st.title("STEELTRACE™ CSRD+AI - Dashboard de Validación 🧪")
st.markdown("Guía interactiva para la consultora: inspección de datos y ejecución paso a paso del pipeline de trazabilidad y gobernanza.")

# Pestañas principales
data_tab, pipeline_tab = st.tabs(["📂 1. Datos de Entrada (Data Inspection)", "⚙️ 2. Pipeline Interactivo (Ejecución y Artefactos)"])

# ----------------------------------------
# PESTAÑA 1: DATOS DE ENTRADA
# ----------------------------------------
with data_tab:
    st.header("Inspección de Archivos de Muestra")
    st.markdown("Los archivos JSON en `data/samples/` son la fuente de datos (E1, S1, G1).")
    
    # Sidebar para selección de archivo
    st.sidebar.header("Archivos de Muestra")
    selected_file_name = st.sidebar.selectbox(
        "Selecciona un archivo JSON:",
        SAMPLE_FILES,
        index=0
    )
    
    if selected_file_name:
        file_path = DATA_PATH / selected_file_name
        st.subheader(f"Contenido de: `{selected_file_name}`")
        
        content = file_path.read_text(encoding='utf-8')
        try:
            # Si es JSON, mostrarlo como objeto interactivo
            st.json(json.loads(content))
        except:
            # Si no es JSON válido (o si la lectura falla), mostrarlo como código
            st.code(content, language="json")

        # Expander para ver los Contratos
        with st.expander("Ver Contrato/Schema Relacionado (`contracts/`):"):
            if "energy" in selected_file_name:
                schema_path = ROOT_DIR / "contracts" / "erp_energy.schema.json"
            elif "hr" in selected_file_name:
                schema_path = ROOT_DIR / "contracts" / "hr_people.schema.json"
            elif "ethics" in selected_file_name:
                schema_path = ROOT_DIR / "contracts" / "ethics_cases.schema.json"
            else:
                st.info("Esquema no encontrado.")
                schema_path = None
            
            if schema_path and schema_path.exists():
                st.code(load_file_content(schema_path), language="json")
            else:
                st.warning(f"Esquema {schema_path.name if schema_path else 'N/A'} no disponible.")


# ----------------------------------------
# PESTAÑA 2: PIPELINE INTERACTIVO
# ----------------------------------------
with pipeline_tab:
    st.header("Ejecución Paso a Paso del Pipeline de Gobernanza")
    st.markdown("Cada paso genera artefactos intermedios (logs, normalizados, KPIs).")
    
    # --- PASO 1: MCP - Ingestión y Data Quality ---
    st.subheader("1️⃣ MCP — Ingesta, Validación de Schema y DQ")
    if st.button("▶️ Ejecutar Ingestión/DQ (`mcp_ingest.py`)"):
        with st.spinner("Cargando, validando y normalizando los 3 datasets..."):
            output = run_script_and_capture_output("mcp_ingest.py")
            if output:
                with st.expander("Ver Logs del Script"):
                    st.code(output, language="python")
                
                st.markdown("---")
                st.success("Archivos Normalizados y de Reporte Generados:")
                
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    st.json(load_file_content(OUTPUT_PATH / "data" / "dq_report.json"))
                with col_n2:
                    st.code(load_file_content(OUTPUT_PATH / "data" / "lineage.jsonl"), language="json")

    # --- PASO 2: SHACL - Validación Semántica ---
    st.subheader("2️⃣ SHACL — Validación Semántica (Ontología + Trazabilidad RDF)")
    if st.button("▶️ Ejecutar SHACL (`shacl_validate.py`)"):
        with st.spinner("Creando grafo RDF y validando contra SHACL E1/S1/G1..."):
            output = run_script_and_capture_output("shacl_validate.py")
            if output:
                with st.expander("Ver Logs y Reporte de Conformidad"):
                    st.code(load_file_content(OUTPUT_PATH / "ontology" / "validation.log"), language="markdown")
                
                st.success("Linaje RDF (TTL) generado. Muestra de trazabilidad:")
                st.code(load_file_content(OUTPUT_PATH / "ontology" / "linaje.ttl")[:1000], language="turtle")


    # --- PASO 3: RAGA - Cálculo de KPIs y Explicaciones ---
    st.subheader("3️⃣ RAGA — KPIs E1/S1/G1 y Explicaciones (RAG)")
    if st.button("▶️ Ejecutar RAGA (`raga_compute.py`)"):
        with st.spinner("Calculando KPIs y generando explicaciones (hipótesis/evidencia/citas)..."):
            output = run_script_and_capture_output("raga_compute.py")
            if output:
                with st.expander("Ver Logs del Script"):
                    st.code(output)
                
                st.success("KPIs y Explicación Generados:")
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    st.json(load_file_content(OUTPUT_PATH / "raga" / "kpis.json"))
                with col_k2:
                    st.json(load_file_content(OUTPUT_PATH / "raga" / "explain.json"))


    # --- PASO 4: EEE-GATE - Decisión de Gobernanza ---
    st.subheader("4️⃣ EEE-Gate — Scoring (Epistémico/Explícito/Evidencia) y Decisión")
    if st.button("▶️ Ejecutar EEE-Gate (`eee_gate.py`)"):
        with st.spinner("Evaluando el EEE-Score y determinando Publish/Review/Block..."):
            output = run_script_and_capture_output("eee_gate.py")
            if output:
                with st.expander("Ver Logs del Script"):
                    st.code(output)
                
                st.success("Reporte de Gate Generado:")
                st.json(load_file_content(OUTPUT_PATH / "ops" / "gate_report.json"))
                
                st.info("La decisión final se basa en la validación de Artefactos de Evidencia (Paso 6).")


    # --- PASO 5 & 6: XBRL, Evidencias (Merkle) y Release Package ---
    st.subheader("5️⃣ y 6️⃣ XBRL y Evidencias (WORM/Merkle/TSA Simulada)")
    
    if st.button("▶️ Ejecutar XBRL y Evidencias Finales"):
        with st.spinner("Generando XBRL, construyendo el Merkle Tree y sellando las evidencias..."):
            # Generar XBRL
            xbrl_output = run_script_and_capture_output("xbrl_generate.py")
            # Construir Evidencias (Merkle Root)
            evidence_output = run_script_and_capture_output("evidence_build.py")
            # Generar Paquete de Release
            package_output = run_script_and_capture_output("package_release.py")

            with st.expander("Ver Manifiesto de Evidencias (WORM)"):
                st.code(load_file_content(OUTPUT_PATH / "evidence" / "evidence_manifest.json"), language="json")

            st.success("Artefactos Finales Generados:")
            st.code(package_output)
            
            # Muestra el resultado de la validación XBRL
            st.info("Validación XBRL (Schema) Reporte:")
            st.code(load_file_content(OUTPUT_PATH / "xbrl" / "validation.log"))
