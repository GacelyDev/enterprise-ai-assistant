import os
import csv
from pathlib import Path
from datetime import datetime
from src.analytics.extractor import load_sessions, get_quantitative_metrics
from src.analytics.metrics import evaluate_session_impact

def main():
    print("\n==================================================")
    print("--- 📊 Analizador de Impacto y Métricas RAG ---")
    print("==================================================\n")
    
    sessions_dir = os.getenv("SESSIONS_DIR", "/app/data/sessions")
    
    # Ensure the 'analytics' subfolder exists inside data directory
    output_dir = Path("/app/data/analytics")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "reporte_impacto_rag.csv"
    
    print(f"Buscando historiales en: {sessions_dir}")
    sessions = load_sessions(sessions_dir)
    
    if not sessions:
        print("❌ No se encontraron sesiones grabadas en el directorio.")
        return

    print(f"✅ {len(sessions)} sesiones encontradas. Iniciando análisis LLM y cuantitativo...\n")
    
    report_data = []
    
    # Process each recorded session
    for session in sessions:
        sess_id = session["session_id"]
        history = session["history"]
        
        # Extract extended quantitative metrics
        quant_metrics = get_quantitative_metrics(history)
        
        # Extract qualitative impact metrics using the LLM model
        print(f"Procesando sesión [{sess_id}]...")
        qual_metrics = evaluate_session_impact(history)
        
        # Consolidate row data including quantitative and qualitative fields
        row = {
            "ID Sesion": sess_id,
            "Turnos Usuario": quant_metrics["turnos_usuario"],
            "Turnos AI": quant_metrics["turnos_ai"],
            "Total Mensajes": quant_metrics["total_mensajes"],
            "Palabras Usuario": quant_metrics["palabras_usuario_total"],
            "Palabras AI": quant_metrics["palabras_ai_total"],
            "Palabras Totales": quant_metrics["palabras_totales"],
            "Prom. Palabras/Msg User": quant_metrics["promedio_palabras_por_mensaje_usuario"],
            "Prom. Palabras/Msg AI": quant_metrics["promedio_palabras_por_mensaje_ai"],
            "Tema Principal": qual_metrics["tema_principal"],
            "Resuelto": qual_metrics["resuelto"],
            "Sentimiento": qual_metrics["sentimiento"]
        }
        report_data.append(row)

    # Print a detailed formatted table to console including averages
    print("\n" + "="*135)
    print(f"{'ID SESION':<12} | {'TURNOS(U/AI)':<12} | {'PALABRAS(U/AI)':<16} | {'PROV.PAL(U/AI)':<16} | {'TEMA PRINCIPAL':<20} | {'RESUELTO':<9} | {'SENTIMIENTO'}")
    print("=" * 135)
    
    for row in report_data:
        turnos = f"{row['Turnos Usuario']}/{row['Turnos AI']}"
        palabras = f"{row['Palabras Usuario']}/{row['Palabras AI']}"
        promedios = f"{row['Prom. Palabras/Msg User']}/{row['Prom. Palabras/Msg AI']}"
        print(f"{row['ID Sesion']:<12} | {turnos:<12} | {palabras:<16} | {promedios:<16} | {str(row['Tema Principal'])[:18]:<20} | {row['Resuelto']:<9} | {row['Sentimiento']}")
    
    print("=" * 135)

    # Export report data to CSV format
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = report_data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in report_data:
                writer.writerow(row)
                
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n✅ Análisis completado con éxito a las {timestamp}.")
        print(f"📁 Reporte CSV guardado en: {output_csv}\n")
        
    except Exception as e:
        print(f"\n❌ Error al intentar guardar el archivo CSV: {e}")

if __name__ == "__main__":
    main()