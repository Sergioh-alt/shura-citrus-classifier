"""
Punto de entrada principal del Sistema de Clasificación de Limones
Permite ejecutar en modo GUI o CLI
"""

import sys
import argparse
from pathlib import Path

# Agregar directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from core.clasificador import ClasificadorLimones
from core.config_manager import ConfigManager
from export.data_exporter import DataExporter


def modo_cli(args):
    """
    Ejecuta el clasificador en modo línea de comandos.
    
    Args:
        args: Argumentos parseados de argparse
    """
    print("="*70)
    print(" Sistema de Clasificación de Limones - Modo CLI")
    print("="*70)
    
    # Crear config manager
    config = ConfigManager(args.config if args.config else "config.json")
    
    # Crear clasificador
    clasificador = ClasificadorLimones(
        ruta_imagen=args.imagen,
        config_manager=config,
        verbose=not args.quiet
    )
    
    # Procesar
    resultado = clasificador.procesar(mostrar_visualizacion=not args.no_show)
    
    if resultado:
        # Exportar si se solicitó
        if args.export_csv:
            datos = DataExporter.resultado_a_dict(clasificador, args.imagen)
            DataExporter.exportar_csv([datos], args.export_csv)
            print(f"✓ Resultados exportados a {args.export_csv}")
        
        if args.export_json:
            datos = DataExporter.resultado_a_dict(clasificador, args.imagen)
            DataExporter.exportar_json([datos], args.export_json)
            print(f"✓ Resultados exportados a {args.export_json}")


def modo_gui():
    """Ejecuta la aplicación en modo GUI."""
    try:
        import tkinter as tk
        from gui.app_limones import LemonClassifierApp
        
        root = tk.Tk()
        app = LemonClassifierApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"❌ Error: No se pudo iniciar la GUI. {e}")
        print("   Asegúrese de que tkinter esté instalado.")
        sys.exit(1)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Sistema de Clasificación de Limones para Exportación",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  Modo GUI (interfaz gráfica):
    python app.py

  Modo CLI (línea de comandos):
    python app.py --cli limon.jpg
    python app.py --cli limon.jpg --export-csv resultados.csv
    python app.py --cli limon.jpg --no-show --quiet --export-json datos.json

  Con configuración personalizada:
    python app.py --cli limon.jpg --config mi_config.json
        """
    )
    
    parser.add_argument('--cli', dest='imagen', metavar='IMAGEN',
                       help='Ejecutar en modo CLI con la imagen especificada')
    
    parser.add_argument('--config', metavar='ARCHIVO',
                       help='Archivo de configuración JSON personalizado')
    
    parser.add_argument('--export-csv', metavar='ARCHIVO',
                       help='Exportar resultados a CSV')
    
    parser.add_argument('--export-json', metavar='ARCHIVO',
                       help='Exportar resultados a JSON')
    
    parser.add_argument('--no-show', action='store_true',
                       help='No mostrar ventana de visualización (solo en modo CLI)')
    
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Modo silencioso, sin impresión de logs')
    
    parser.add_argument('--version', action='version', 
                       version='Sistema de Clasificación de Limones v2.0')
    
    args = parser.parse_args()
    
    # Decidir modo de ejecución
    if args.imagen:
        # Modo CLI
        if not Path(args.imagen).exists():
            print(f"❌ Error: El archivo '{args.imagen}' no existe")
            sys.exit(1)
        modo_cli(args)
    else:
        # Modo GUI por defecto
        modo_gui()


if __name__ == "__main__":
    main()
