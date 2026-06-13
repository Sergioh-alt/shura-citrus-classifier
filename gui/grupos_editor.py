"""
Editor de Grupos de Clasificación para GUI
Permite crear, editar y eliminar grupos personalizados
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.grupos_manager import GruposManager, GrupoClasificacion


class GruposEditorWindow:
    """
    Ventana para administrar grupos de clasificación personalizados.
    """
    
    def __init__(self, parent):
        """
        Args:
            parent: Ventana padre
        """
        self.window = tk.Toplevel(parent)
        self.window.title("Administración de Grupos de Clasificación")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        # Gestor de grupos
        self.grupos_manager = GruposManager()
        
        # Variables del formulario
        self.crear_variables()
        
        # UI
        self.create_ui()
        
        # Cargar grupos en la lista
        self.actualizar_lista()
    
    def crear_variables(self):
        """Crear variables de tkinter para el formulario"""
        self.var_nombre = tk.StringVar()
        self.var_prioridad = tk.IntVar(value=999)
        self.var_salida = tk.IntVar(value=1)
        self.var_descripcion = tk.StringVar()
        
        # Criterios
        self.var_acidez_min = tk.DoubleVar(value=0.0)
        self.var_acidez_max = tk.DoubleVar(value=8.0)
        self.var_tonalidad_min = tk.DoubleVar(value=0.0)
        self.var_tonalidad_max = tk.DoubleVar(value=180.0)
        self.var_rugosidad_max = tk.DoubleVar(value=100.0)
        self.var_defectos_max = tk.DoubleVar(value=20.0)
        self.var_vida_util_min = tk.IntVar(value=0)
        
        # Checkboxes para activar/desactivar criterios
        self.check_acidez = tk.BooleanVar(value=True)
        self.check_tonalidad = tk.BooleanVar(value=True)
        self.check_rugosidad = tk.BooleanVar(value=True)
        self.check_defectos = tk.BooleanVar(value=True)
        self.check_vida_util = tk.BooleanVar(value=False)
    
    def create_ui(self):
        """Crear interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Grupos de Clasificación Personalizados", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 10))
        
        # Panel dividido: lista (izq) + formulario (der)
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo: Lista de grupos
        self.create_lista_panel(paned)
        
        # Panel derecho: Formulario
        self.create_formulario_panel(paned)
    
    def create_lista_panel(self, parent):
        """Crear panel de lista de grupos"""
        lista_frame = ttk.Frame(parent, padding="5")
        parent.add(lista_frame, weight=1)
        
        # Título
        ttk.Label(lista_frame, text="Grupos Existentes", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # TreeView para lista
        columns = ('Prioridad', 'Salida')
        self.tree = ttk.Treeview(lista_frame, columns=columns, show='tree headings', height=15)
        
        self.tree.heading('#0', text='Nombre')
        self.tree.heading('Prioridad', text='Prioridad')
        self.tree.heading('Salida', text='Salida')
        
        self.tree.column('#0', width=180)
        self.tree.column('Prioridad', width=70, anchor='center')
        self.tree.column('Salida', width=50, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selección
        self.tree.bind('<<TreeviewSelect>>', self.on_seleccionar_grupo)
        
        # Botones
        btn_frame = ttk.Frame(lista_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="➕ Nuevo", command=self.nuevo_grupo).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Eliminar", command=self.eliminar_grupo).pack(side=tk.LEFT, padx=2)
    
    def create_formulario_panel(self, parent):
        """Crear panel de formulario"""
        form_frame = ttk.Frame(parent, padding="10")
        parent.add(form_frame, weight=2)
        
        # Scroll para el formulario
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Información básica
        ttk.Label(scrollable_frame, text="Información del Grupo", 
                 font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        row = 1
        
        # Nombre
        ttk.Label(scrollable_frame, text="Nombre:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scrollable_frame, textvariable=self.var_nombre, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Descripción
        ttk.Label(scrollable_frame, text="Descripción:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(scrollable_frame, textvariable=self.var_descripcion, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Prioridad
        ttk.Label(scrollable_frame, text="Prioridad (1=más alta):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(scrollable_frame, from_=1, to=999, textvariable=self.var_prioridad, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Salida física
        ttk.Label(scrollable_frame, text="Salida Física (1-6):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(scrollable_frame, from_=1, to=6, textvariable=self.var_salida, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Separador
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Criterios de clasificación
        ttk.Label(scrollable_frame, text="Criterios de Clasificación", 
                 font=('Segoe UI', 11, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Acidez
        self.create_criterio_range(scrollable_frame, row, "Acidez (%)", 
                                   self.check_acidez, self.var_acidez_min, self.var_acidez_max, 0, 8)
        row += 2
        
        # Tonalidad
        self.create_criterio_range(scrollable_frame, row, "Tonalidad (grados)", 
                                   self.check_tonalidad, self.var_tonalidad_min, self.var_tonalidad_max, 0, 180)
        row += 2
        
        # Rugosidad
        self.create_criterio_single(scrollable_frame, row, "Rugosidad Máxima", 
                                    self.check_rugosidad, self.var_rugosidad_max, 0, 200)
        row += 1
        
        # Defectos
        self.create_criterio_single(scrollable_frame, row, "Defectos Máximos (%)", 
                                    self.check_defectos, self.var_defectos_max, 0, 50)
        row += 1
        
        # Vida útil
        self.create_criterio_single(scrollable_frame, row, "Vida Útil Mínima (días)", 
                                    self.check_vida_util, self.var_vida_util_min, 0, 60, is_int=True)
        row += 1
        
        # Botones de acción
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="💾 Guardar", command=self.guardar_grupo, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.limpiar_formulario).pack(side=tk.LEFT, padx=5)
        
        # Empaquetar canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_criterio_range(self, parent, row, label, check_var, var_min, var_max, min_val, max_val):
        """Crear criterio con rango mín-máx"""
        check = ttk.Checkbutton(parent, text=label, variable=check_var)
        check.grid(row=row, column=0, sticky=tk.W, pady=5)
        
        frame = ttk.Frame(parent)
        frame.grid(row=row+1, column=0, columnspan=2, sticky=tk.W, padx=20)
        
        ttk.Label(frame, text="Mín:").pack(side=tk.LEFT)
        ttk.Scale(frame, from_=min_val, to=max_val, variable=var_min, 
                 orient=tk.HORIZONTAL, length=150).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame, textvariable=var_min, width=6).pack(side=tk.LEFT)
        
        ttk.Label(frame, text="Máx:").pack(side=tk.LEFT, padx=(15, 0))
        ttk.Scale(frame, from_=min_val, to=max_val, variable=var_max, 
                 orient=tk.HORIZONTAL, length=150).pack(side=tk.LEFT, padx=5)
        ttk.Label(frame, textvariable=var_max, width=6).pack(side=tk.LEFT)
    
    def create_criterio_single(self, parent, row, label, check_var, var, min_val, max_val, is_int=False):
        """Crear criterio con valor único"""
        check = ttk.Checkbutton(parent, text=label, variable=check_var)
        check.grid(row=row, column=0, sticky=tk.W, pady=5)
        
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, sticky=tk.W)
        
        ttk.Scale(frame, from_=min_val, to=max_val, variable=var, 
                 orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5)
        
        if is_int:
            label_text = tk.Label(frame, text=f"{int(var.get())}", width=6)
            var.trace_add('write', lambda *args: label_text.config(text=f"{int(var.get())}"))
        else:
            label_text = ttk.Label(frame, textvariable=var, width=6)
        
        label_text.pack(side=tk.LEFT)
    
    def actualizar_lista(self):
        """Actualizar TreeView con grupos actuales"""
        # Limpiar
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agregar grupos
        for grupo in sorted(self.grupos_manager.grupos, key=lambda g: g.prioridad):
            self.tree.insert('', 'end', text=grupo.nombre, 
                           values=(grupo.prioridad, grupo.salida_fisica),
                           tags=(grupo.nombre,))
    
    def on_seleccionar_grupo(self, event):
        """Evento al seleccionar un grupo de la lista"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        nombre_grupo = self.tree.item(item, 'text')
        
        # Buscar grupo
        grupo = self.grupos_manager.obtener_grupo(nombre_grupo)
        if grupo:
            self.cargar_grupo_en_formulario(grupo)
    
    def cargar_grupo_en_formulario(self, grupo: GrupoClasificacion):
        """Cargar datos de un grupo en el formulario"""
        # Información básica
        self.var_nombre.set(grupo.nombre)
        self.var_prioridad.set(grupo.prioridad)
        self.var_salida.set(grupo.salida_fisica)
        self.var_descripcion.set(grupo.descripcion)
        
        # Criterios
        criterios = grupo.criterios
        
        # Acidez
        if 'acidez_min' in criterios or 'acidez_max' in criterios:
            self.check_acidez.set(True)
            self.var_acidez_min.set(criterios.get('acidez_min', 0.0))
            self.var_acidez_max.set(criterios.get('acidez_max', 8.0))
        else:
            self.check_acidez.set(False)
        
        # Tonalidad
        if 'tonalidad_min' in criterios or 'tonalidad_max' in criterios:
            self.check_tonalidad.set(True)
            self.var_tonalidad_min.set(criterios.get('tonalidad_min', 0.0))
            self.var_tonalidad_max.set(criterios.get('tonalidad_max', 180.0))
        else:
            self.check_tonalidad.set(False)
        
        # Rugosidad
        if 'rugosidad_max' in criterios:
            self.check_rugosidad.set(True)
            self.var_rugosidad_max.set(criterios.get('rugosidad_max', 100.0))
        else:
            self.check_rugosidad.set(False)
        
        # Defectos
        if 'defectos_max' in criterios:
            self.check_defectos.set(True)
            self.var_defectos_max.set(criterios.get('defectos_max', 20.0))
        else:
            self.check_defectos.set(False)
        
        # Vida útil
        if 'vida_util_min' in criterios:
            self.check_vida_util.set(True)
            self.var_vida_util_min.set(criterios.get('vida_util_min', 0))
        else:
            self.check_vida_util.set(False)
    
    def nuevo_grupo(self):
        """Crear nuevo grupo (limpiar formulario)"""
        self.limpiar_formulario()
        self.var_nombre.set("Nuevo Grupo")
    
    def limpiar_formulario(self):
        """Limpiar formulario"""
        self.var_nombre.set("")
        self.var_prioridad.set(999)
        self.var_salida.set(1)
        self.var_descripcion.set("")
        
        self.var_acidez_min.set(0.0)
        self.var_acidez_max.set(8.0)
        self.var_tonalidad_min.set(0.0)
        self.var_tonalidad_max.set(180.0)
        self.var_rugosidad_max.set(100.0)
        self.var_defectos_max.set(20.0)
        self.var_vida_util_min.set(0)
        
        self.check_acidez.set(False)
        self.check_tonalidad.set(False)
        self.check_rugosidad.set(False)
        self.check_defectos.set(False)
        self.check_vida_util.set(False)
    
    def guardar_grupo(self):
        """Guardar grupo (crear o actualizar)"""
        nombre = self.var_nombre.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre del grupo es obligatorio")
            return
        
        # Construir criterios
        criterios = {}
        
        if self.check_acidez.get():
            criterios['acidez_min'] = self.var_acidez_min.get()
            criterios['acidez_max'] = self.var_acidez_max.get()
        
        if self.check_tonalidad.get():
            criterios['tonalidad_min'] = self.var_tonalidad_min.get()
            criterios['tonalidad_max'] = self.var_tonalidad_max.get()
        
        if self.check_rugosidad.get():
            criterios['rugosidad_max'] = self.var_rugosidad_max.get()
        
        if self.check_defectos.get():
            criterios['defectos_max'] = self.var_defectos_max.get()
        
        if self.check_vida_util.get():
            criterios['vida_util_min'] = int(self.var_vida_util_min.get())
        
        # Verificar si ya existe
        grupo_existente = self.grupos_manager.obtener_grupo(nombre)
        
        if grupo_existente:
            # Actualizar
            grupo_existente.prioridad = self.var_prioridad.get()
            grupo_existente.salida_fisica = self.var_salida.get()
            grupo_existente.descripcion = self.var_descripcion.get()
            grupo_existente.criterios = criterios
        else:
            # Crear nuevo
            nuevo_grupo = GrupoClasificacion(
                nombre=nombre,
                criterios=criterios,
                prioridad=self.var_prioridad.get(),
                salida_fisica=self.var_salida.get(),
                descripcion=self.var_descripcion.get()
            )
            self.grupos_manager.grupos.append(nuevo_grupo)
        
        # Guardar a archivo
        if self.grupos_manager.guardar_grupos():
            messagebox.showinfo("Éxito", f"Grupo '{nombre}' guardado correctamente")
            self.actualizar_lista()
        else:
            messagebox.showerror("Error", "No se pudo guardar el grupo")
    
    def eliminar_grupo(self):
        """Eliminar grupo seleccionado"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un grupo para eliminar")
            return
        
        item = selection[0]
        nombre_grupo = self.tree.item(item, 'text')
        
        respuesta = messagebox.askyesno("Confirmar", 
                                       f"¿Está seguro de eliminar el grupo '{nombre_grupo}'?")
        
        if respuesta:
            if self.grupos_manager.eliminar_grupo(nombre_grupo):
                messagebox.showinfo("Éxito", f"Grupo '{nombre_grupo}' eliminado")
                self.actualizar_lista()
                self.limpiar_formulario()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el grupo")
