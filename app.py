import streamlit as st
import subprocess
import os
import sys
import json
from pathlib import Path

# --- Configuración General ---
st.set_page_config(
    page_title="SteelTrace CSRD Pipeline",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir la ruta base del proyecto y asegurar el CWD
ROOT_DIR = Path(__file__).parent.resolve()
os.chdir(ROOT_DIR)

DATA_PATH = ROOT_DIR / "data" / "samples"
OUTPUT_PATH = ROOT_DIR 
SAMPLE_FILES = [f.name for f in DATA_PATH.glob("*.json")]

# Listado de scripts del pipeline en orden de ejecución
PIPELINE_SCRIPTS = [
    "mcp_ingest.py",      # 1. Ingesta y Normalización
    "shacl_validate.py",  # 2. Validación Semántica
    "raga_compute.py",    # 3. Cálculo de RAGA
    "eee_gate.py",        # 4. Evaluación de Riesgos (EEE Gate)
    "xbrl_generate.py",   # 5. Generación XBRL
    "evidence_build.py",  # 6. Construcción de la Evidencia (Merkle Tree)
    "hitl_kappa.py",      # 7. Evaluación HITL
    "package_release.py"  # 8. Empaquetado final
]

# --- Utilidades ---

def load_file_content(file_path: Path):
    """Carga y retorna el contenido de un archivo como texto o JSON."""
    try:
        # Nota: Usamos read_text para la visualización en Streamlit.
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception as e:
        return f"Error al leer {file_path.name}: {e}"

def run_script_and_capture_output(script_name):
    """
    Ejecuta un script del pipeline usando sys.executable para asegurar el entorno.
    """
    script_path = ROOT_DIR / "scripts" / script_name
    
    # 1. Mostrar la información de ejecución
    with st.spinner(f"Ejecutando script: **{script_name}**..."):
        st.code(f"Comando: {sys.executable} {script_name}", language="bash")

        try:
            # CORRECCIÓN CLAVE: Usar sys.executable
            result = subprocess.run(
                [sys.executable, str(script_path)], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=60 # Aumentado el timeout por seguridad
            )
            st.success(f"✅ Ejecución de **{script_name}** completada con éxito.")
            st.info("Salida del script (STDOUT):")
            st.code(result.stdout, language="text")
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Ejecución de **{script_name}** FALLIDA con código de retorno {e.returncode}.")
            st.text("STDOUT:")
            st.code(e.stdout, language="text")
            st.text("STDERR (El error principal):")
            st.code(e.stderr, language="text")
            return None
            
        except FileNotFoundError:
            st.error(f"❌ Error: No se encontró el script **{script_name}**.")
            return None
        except subprocess.TimeoutExpired:
            st.error(f"❌ Error: El script **{script_name}** excedió el tiempo límite de ejecución.")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado al ejecutar **{script_name}**: {e}")
            return None


# --- Interfaz de Streamlit ---

def main():
    st.title("⚙️ SteelTrace: Pipeline de Procesamiento CSRD")
    st.markdown("Guía interactiva para la consultora: inspección de datos y ejecución paso a paso del pipeline de trazabilidad y gobernanza.")

    # Pestañas principales
    data_tab, pipeline_tab = st.tabs(["📂 1. Datos de Entrada (Data Inspection)", "⚙️ 2. Pipeline Interactivo (Ejecución y Artefactos)"])

    # ----------------------------------------
    # PESTAÑA 1: DATOS DE ENTRADA
    # ----------------------------------------
    with data_tab:
        st.header("Inspección de Archivos de Muestra")
        st.markdown("Los archivos JSON en `data/samples/` son la fuente de datos (E1, S1, G1).")
        
        st.sidebar.header("Archivos de Muestra")
        selected_file_name = st.sidebar.selectbox(
            "Selecciona un archivo JSON:",
            SAMPLE_FILES,
            index=0
        )
        
        if selected_file_name:
            file_path = DATA_PATH / selected_file_name
            st.subheader(f"Contenido de: `{selected_file_name}`")
            
            content = load_file_content(file_path)
            if content:
                try:
                    st.json(json.loads(content))
                except:
                    st.code(content, language="json")

            with st.expander("Ver Contrato/Schema Relacionado (`contracts/`):"):
                if "energy" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "erp_energy.schema.json"
                elif "hr" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "hr_people.schema.json"
                elif "ethics" in selected_file_name:
                    schema_path = ROOT_DIR / "contracts" / "ethics_cases.schema.json"
                else:
                    schema_path = None
                
                if schema_path and schema_path.exists():
                    st.code(load_file_content(schema_path), language="json")
                else:
                    st.warning(f"Esquema no disponible.")


    # ----------------------------------------
    # PESTAÑA 2: PIPELINE INTERACTIVO
    # ----------------------------------------
    with pipeline_tab:
        st.header("Ejecución Paso a Paso del Pipeline de Gobernanza")
        st.markdown("Presiona los botones en orden para generar los artefactos de cumplimiento.")

        # Estado para guardar logs
        if 'execution_logs' not in st.session_state:
            st.session_state.execution_logs = {}

        # --- ORQUESTADOR: Ejecución de Scripts ---
        
        for i, script in enumerate(PIPELINE_SCRIPTS):
            st.subheader(f"Paso {i+1}: {script}")
            
            # Botón para la ejecución individual
            if st.button(f"▶️ Ejecutar {script}", key=f"run_btn_{i}", type="secondary"):
                output = run_script_and_capture_output(script)
                st.session_state.execution_logs[script] = output
        
        st.divider()

        # --- VISUALIZACIÓN DE ARTEFACTOS GENERADOS ---
        st.header("Artefactos de Salida Clave")
        st.markdown("Revisa los reportes generados después de ejecutar los pasos.")

        # 1. Reporte DQ y Linaje (Paso 1)
        with st.expander("✅ Ingesta/Data Quality (DQ) y Linaje"):
            st.json(load_file_content(OUTPUT_PATH / "data" / "dq_report.json"))
            st.code(load_file_content(OUTPUT_PATH / "data" / "lineage.jsonl"), language="json")

        # 2. Validación Semántica (Paso 2)
        with st.expander("✅ Validación SHACL y Grafo RDF (Trazabilidad Semántica)"):
            st.code(load_file_content(OUTPUT_PATH / "ontology" / "validation.log"), language="markdown")
            st.code(load_file_content(OUTPUT_PATH / "ontology" / "linaje.ttl")[:1000], language="turtle")

        # 3. KPIs y Explicación RAGA (Paso 3)
        with st.expander("✅ RAGA: KPIs y Explicaciones (Hipótesis/Evidencia)"):
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.json(load_file_content(OUTPUT_PATH / "raga" / "kpis.json"))
            with col_k2:
                st.json(load_file_content(OUTPUT_PATH / "raga" / "explain.json"))

        # 4. Decisión del EEE-Gate (Paso 4)
        with st.expander("✅ EEE-Gate: Decisión de Publicación"):
            st.json(load_file_content(OUTPUT_PATH / "ops" / "gate_report.json"))

        # 5. Evidencias y XBRL (Pasos 5 & 6)
        with st.expander("✅ Evidencias (Merkle) y XBRL (Salida Verificable)"):
            st.code(load_file_content(OUTPUT_PATH / "evidence" / "evidence_manifest.json"), language="json")
            st.code(load_file_content(OUTPUT_PATH / "xbrl" / "validation.log"))

        # 6. HITL Kappa (Paso 7)
        with st.expander("✅ HITL: Acuerdo Inter-Evaluador (Kappa de Cohen)"):
            st.json(load_file_content(OUTPUT_PATH / "ops" / "hitl_kappa.json"))

        # 7. Paquete Final (Paso 8)
        with st.expander("📦 Paquete de Auditoría ZIP"):
             st.code("El paquete final ZIP se crea en release/audit/ (Ver logs del último paso)")


# Ejecutar la aplicación principal
if __name__ == "__main__":
    main()
