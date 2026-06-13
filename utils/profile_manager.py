"""
Manager de Perfiles de Configuración
Import/Export de configuraciones completas
"""

import json
import os
import zipfile
import shutil
from datetime import datetime
from typing import Dict, List


class ProfileManager:
    """
    Gestiona perfiles de configuración (config.json + grupos.json).
    """
    
    def __init__(self, config_path='config.json', grupos_path='grupos.json'):
        self.config_path = config_path
        self.grupos_path = grupos_path
        self.profiles_dir = 'perfiles'
        
        os.makedirs(self.profiles_dir, exist_ok=True)
    
    def exportar_perfil(self, nombre: str, descripcion: str = '', autor: str = '') -> str:
        """
        Exportar configuración actual como perfil.
        
        Returns:
            Ruta del archivo .zip creado
        """
        # Crear metadata
        metadata = {
            'nombre': nombre,
            'version': '1.0',
            'fecha_creacion': datetime.now().isoformat(),
            'descripcion': descripcion,
            'autor': autor
        }
        
        # Nombre de archivo
        filename = f"perfil_{nombre.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
        zip_path = os.path.join(self.profiles_dir, filename)
        
        # Crear ZIP
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Agregar archivos
            if os.path.exists(self.config_path):
                zf .write(self.config_path, 'config.json')
            
            if os.path.exists(self.grupos_path):
                zf.write(self.grupos_path, 'grupos.json')
            
            # Agregar metadata
            zf.writestr('metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))
            
            # README
            readme = f"""# Perfil: {nombre}

Descripción: {descripcion}
Autor: {autor}
Fecha: {metadata['fecha_creacion']}

## Contenido
- config.json: Configuración de umbrales y parámetros
- grupos.json: Definición de grupos de clasificación

## Uso
Importar este perfil desde el menú Archivo > Importar Perfil
"""
            zf.writestr('README.txt', readme)
        
        print(f"✓ Perfil exportado: {zip_path}")
        return zip_path
    
    def importar_perfil(self, zip_path: str, aplicar: bool = True) -> Dict:
        """
        Importar perfil desde archivo ZIP.
        
        Args:
            zip_path: Ruta al archivo .zip
            aplicar: Si True, aplica inmediatamente
        
        Returns:
            Metadata del perfil
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Archivo no encontrado: {zip_path}")
        
        # Crear directorio temporal
        temp_dir = 'temp_profile_import'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Extraer ZIP
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
            
            # Leer metadata
            metadata_path = os.path.join(temp_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {'nombre': 'Perfil sin nombre'}
            
            if aplicar:
                # Copiar archivos
                config_temp = os.path.join(temp_dir, 'config.json')
                grupos_temp = os.path.join(temp_dir, 'grupos.json')
                
                if os.path.exists(config_temp):
                    # Backup actual
                    if os.path.exists(self.config_path):
                        shutil.copy(self.config_path, f"{self.config_path}.backup")
                    shutil.copy(config_temp, self.config_path)
                
                if os.path.exists(grupos_temp):
                    if os.path.exists(self.grupos_path):
                        shutil.copy(self.grupos_path, f"{self.grupos_path}.backup")
                    shutil.copy(grupos_temp, self.grupos_path)
                
                print(f"✓ Perfil importado y aplicado: {metadata['nombre']}")
            
            return metadata
            
        finally:
            # Limpiar temporal
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def listar_perfiles(self) -> List[Dict]:
        """Listar perfiles disponibles"""
        perfiles = []
        
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.zip'):
                zip_path = os.path.join(self.profiles_dir, filename)
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        if 'metadata.json' in zf.namelist():
                            metadata_str = zf.read('metadata.json').decode('utf-8')
                            metadata = json.loads(metadata_str)
                            metadata['filename'] = filename
                            metadata['path'] = zip_path
                            perfiles.append(metadata)
                except:
                    pass
        
        return sorted(perfiles, key=lambda x: x.get('fecha_creacion', ''), reverse=True)
    
    def crear_perfiles_predefinidos(self):
        """Crear perfiles predefinidos de ejemplo"""
        # TODO: Implementar perfiles de ejemplo para diferentes mercados
        pass


if __name__ == "__main__":
    print("=== Test de Profile Manager ===\n")
    
    manager = ProfileManager()
    
    # Test exportar
    print("1. Exportando perfil actual...")
    zip_path = manager.exportar_perfil(
        nombre="Test Profile",
        descripcion="Perfil de prueba",
        autor="Sistema"
    )
    print(f"   ✓ Exportado: {zip_path}")
    
    # Test listar
    print("\n2. Listando perfiles...")
    perfiles = manager.listar_perfiles()
    print(f"   ✓ {len(perfiles)} perfiles encontrados")
    for p in perfiles:
        print(f"     - {p['nombre']} ({p.get('fecha_creacion', 'N/A')})")
    
    print("\n✅ Test completado")
