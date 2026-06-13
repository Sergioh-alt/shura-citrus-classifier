"""
Aplicación GUI para el Sistema de Clasificación de Limones
Interfaz moderna con tema oscuro — dark sidebar + metric cards
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
from PIL import Image, ImageTk
import cv2
import numpy as np
from pathlib import Path
import threading

from core.clasificador import ClasificadorLimones
from core.config_manager import ConfigManager


# ─── Paleta de colores ──────────────────────────────────────────────────────
C = {
    'bg':           '#0F1923',   # fondo principal
    'panel':        '#1A2332',   # sidebar / panels
    'card':         '#233044',   # cards de métricas
    'card_hover':   '#2C3D57',   # card hover
    'accent':       '#7ED321',   # verde lima (primario)
    'accent_dark':  '#5FA618',   # verde lima oscuro (hover)
    'accent2':      '#00B4D8',   # cyan (info)
    'danger':       '#E74C3C',   # rojo
    'warning':      '#F39C12',   # naranja
    'success':      '#27AE60',   # verde
    'text':         '#E8EAED',   # texto principal
    'subtext':      '#8E9BAE',   # texto secundario
    'border':       '#2C3D57',   # bordes
    'separator':    '#1E2D40',   # separadores
}


class LemonClassifierApp:
    """
    Aplicación principal con interfaz gráfica para clasificación de limones.
    Layout: Sidebar | Panel imagen (tabs) | Panel resultados
    """

    def __init__(self, root):
        self.root = root
        self.root.title("LemonVision — Sistema de Clasificación")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        self.root.configure(bg=C['bg'])

        # Gestores
        self.config = ConfigManager()
        self.clasificador = None

        # Estado
        self.imagen_actual = None
        self.resultado_actual = None
        self.ruta_imagen_actual = None

        # Fuentes
        self._setup_fonts()

        # Configurar estilos ttk
        self._setup_styles()

        # Crear menú
        self.create_menu()

        # Crear layout principal
        self.create_layout()
        self.create_statusbar()

        # Centrar ventana
        self._center_window()

    # ── Fuentes & estilos ──────────────────────────────────────────────────

    def _setup_fonts(self):
        self.font_title   = tkfont.Font(family='Segoe UI', size=14, weight='bold')
        self.font_heading = tkfont.Font(family='Segoe UI', size=10, weight='bold')
        self.font_normal  = tkfont.Font(family='Segoe UI', size=9)
        self.font_small   = tkfont.Font(family='Segoe UI', size=8)
        self.font_metric  = tkfont.Font(family='Segoe UI', size=18, weight='bold')
        self.font_badge   = tkfont.Font(family='Segoe UI', size=16, weight='bold')
        self.font_mono    = tkfont.Font(family='Consolas',  size=9)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (tabs)
        style.configure('Dark.TNotebook',
                        background=C['panel'],
                        borderwidth=0)
        style.configure('Dark.TNotebook.Tab',
                        background=C['card'],
                        foreground=C['subtext'],
                        padding=[12, 6],
                        font=('Segoe UI', 9))
        style.map('Dark.TNotebook.Tab',
                  background=[('selected', C['accent']), ('active', C['card_hover'])],
                  foreground=[('selected', '#000000'), ('active', C['text'])])

        # Frames
        style.configure('Dark.TFrame', background=C['bg'])
        style.configure('Panel.TFrame', background=C['panel'])
        style.configure('Card.TFrame', background=C['card'])

        # Labels
        style.configure('Dark.TLabel',
                        background=C['bg'], foreground=C['text'],
                        font=('Segoe UI', 9))
        style.configure('Panel.TLabel',
                        background=C['panel'], foreground=C['text'],
                        font=('Segoe UI', 9))
        style.configure('Card.TLabel',
                        background=C['card'], foreground=C['text'],
                        font=('Segoe UI', 9))
        style.configure('Sub.TLabel',
                        background=C['card'], foreground=C['subtext'],
                        font=('Segoe UI', 8))

        # Separator
        style.configure('Dark.TSeparator', background=C['border'])

        # Scrollbar
        style.configure('Dark.TScrollbar',
                        background=C['panel'],
                        troughcolor=C['bg'],
                        arrowcolor=C['subtext'],
                        borderwidth=0)

    # ── Menú ──────────────────────────────────────────────────────────────

    def create_menu(self):
        menubar = tk.Menu(self.root, bg=C['panel'], fg=C['text'],
                          activebackground=C['accent'], activeforeground='#000',
                          relief='flat', borderwidth=0)
        self.root.config(menu=menubar)

        archivo = tk.Menu(menubar, tearoff=0, bg=C['panel'], fg=C['text'],
                          activebackground=C['accent'], activeforeground='#000',
                          relief='flat')
        menubar.add_cascade(label='Archivo', menu=archivo)
        archivo.add_command(label='Abrir Imagen…',   command=self.abrir_imagen, accelerator='Ctrl+O')
        archivo.add_separator()
        archivo.add_command(label='Exportar PDF…',   command=self.exportar_pdf)
        archivo.add_command(label='Exportar CSV…',   command=self.exportar_csv)
        archivo.add_command(label='Exportar JSON…',  command=self.exportar_json)
        archivo.add_separator()
        archivo.add_command(label='Salir',           command=self.root.quit)

        herramientas = tk.Menu(menubar, tearoff=0, bg=C['panel'], fg=C['text'],
                               activebackground=C['accent'], activeforeground='#000',
                               relief='flat')
        menubar.add_cascade(label='Herramientas', menu=herramientas)
        herramientas.add_command(label='Configuración…',           command=self.abrir_configuracion)
        herramientas.add_command(label='⭐ Grupos Personalizados…', command=self.abrir_editor_grupos)
        herramientas.add_command(label='🏭 Modo Industrial…',       command=self.abrir_modo_industrial)
        herramientas.add_separator()
        herramientas.add_command(label='Procesamiento por Lotes…', command=self.procesamiento_lotes)

        ayuda = tk.Menu(menubar, tearoff=0, bg=C['panel'], fg=C['text'],
                        activebackground=C['accent'], activeforeground='#000',
                        relief='flat')
        menubar.add_cascade(label='Ayuda', menu=ayuda)
        ayuda.add_command(label='Manual de Usuario', command=self.mostrar_ayuda)
        ayuda.add_command(label='Acerca de…',        command=self.mostrar_acerca_de)

        self.root.bind('<Control-o>', lambda e: self.abrir_imagen())
        self.root.bind('<Control-s>', lambda e: self.exportar_pdf())
        self.root.bind('<F5>',        lambda e: self.reclasificar())

    # ── Layout principal ──────────────────────────────────────────────────

    def create_layout(self):
        """Crear layout de 3 columnas: sidebar | imagen | resultados"""
        outer = tk.Frame(self.root, bg=C['bg'])
        outer.pack(fill=tk.BOTH, expand=True)

        # Header
        self._create_header(outer)

        # Contenedor central
        center = tk.Frame(outer, bg=C['bg'])
        center.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # 1) Sidebar
        self._create_sidebar(center)

        # 2) Panel central (imagen + tabs)
        self._create_image_panel(center)

        # 3) Panel de resultados
        self._create_results_panel(center)

    def _create_header(self, parent):
        header = tk.Frame(parent, bg=C['panel'], height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Logo + título
        lbl_logo = tk.Label(header, text='🍋', bg=C['panel'],
                            font=tkfont.Font(size=20))
        lbl_logo.pack(side=tk.LEFT, padx=(16, 4), pady=8)

        tk.Label(header, text='LemonVision',
                 bg=C['panel'], fg=C['accent'],
                 font=tkfont.Font(family='Segoe UI', size=15, weight='bold')
                 ).pack(side=tk.LEFT, pady=8)

        tk.Label(header, text='v2.0  Sistema de Clasificación de Limones',
                 bg=C['panel'], fg=C['subtext'],
                 font=tkfont.Font(family='Segoe UI', size=9)
                 ).pack(side=tk.LEFT, padx=(8, 0), pady=8)

        # Indicador de estado
        self.header_state_dot = tk.Label(header, text='●', bg=C['panel'],
                                         fg=C['subtext'],
                                         font=tkfont.Font(size=14))
        self.header_state_dot.pack(side=tk.RIGHT, padx=(0, 8), pady=8)

        self.header_state_lbl = tk.Label(header, text='Listo',
                                         bg=C['panel'], fg=C['subtext'],
                                         font=tkfont.Font(family='Segoe UI', size=9))
        self.header_state_lbl.pack(side=tk.RIGHT, pady=8)

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=C['panel'], width=190)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=8)
        sidebar.pack_propagate(False)

        def sidebar_btn(text, icon, command, accent=False):
            fg   = '#000000' if accent else C['text']
            bg   = C['accent'] if accent else C['card']
            hbg  = C['accent_dark'] if accent else C['card_hover']
            btn = tk.Button(sidebar, text=f'{icon}  {text}',
                            bg=bg, fg=fg, relief='flat', anchor='w',
                            font=self.font_normal, cursor='hand2',
                            padx=12, pady=10, command=command)
            btn.pack(fill=tk.X, pady=2, padx=8)
            btn.bind('<Enter>', lambda e: btn.config(bg=hbg))
            btn.bind('<Leave>', lambda e: btn.config(bg=bg))
            return btn

        def sidebar_sep():
            tk.Frame(sidebar, bg=C['separator'], height=1).pack(
                fill=tk.X, padx=8, pady=8)

        def sidebar_label(text):
            tk.Label(sidebar, text=text.upper(), bg=C['panel'],
                     fg=C['subtext'],
                     font=tkfont.Font(family='Segoe UI', size=7, weight='bold')
                     ).pack(anchor='w', padx=14, pady=(6, 2))

        # Espacio superior
        tk.Frame(sidebar, bg=C['panel'], height=8).pack()

        sidebar_label('Análisis')
        sidebar_btn('Cargar Imagen',  '📁', self.abrir_imagen, accent=True)
        sidebar_btn('Clasificar',     '🔍', self.clasificar_imagen)

        sidebar_sep()

        sidebar_label('Herramientas')
        sidebar_btn('Grupos',         '⭐', self.abrir_editor_grupos)
        sidebar_btn('Modo Industrial','🏭', self.abrir_modo_industrial)
        sidebar_btn('Lotes',          '📦', self.procesamiento_lotes)

        sidebar_sep()

        sidebar_label('Exportar')
        sidebar_btn('PDF',            '📄', self.exportar_pdf)
        sidebar_btn('CSV',            '📊', self.exportar_csv)
        sidebar_btn('JSON',           '🗂', self.exportar_json)

        sidebar_sep()

        sidebar_btn('Configuración',  '⚙️', self.abrir_configuracion)
        sidebar_btn('Ayuda',          '❓', self.mostrar_ayuda)

        # Info imagen al fondo
        tk.Frame(sidebar, bg=C['separator'], height=1).pack(fill=tk.X, padx=8, pady=(12, 8))
        tk.Label(sidebar, text='IMAGEN ACTUAL', bg=C['panel'], fg=C['subtext'],
                 font=tkfont.Font(family='Segoe UI', size=7, weight='bold')
                 ).pack(anchor='w', padx=14)

        self.sidebar_info = tk.Label(
            sidebar, text='—\nSin imagen cargada',
            bg=C['panel'], fg=C['subtext'],
            font=self.font_small, justify='left', wraplength=170)
        self.sidebar_info.pack(anchor='w', padx=14, pady=(4, 4))

    # ── Panel de imagen ──────────────────────────────────────────────────

    def _create_image_panel(self, parent):
        img_frame = tk.Frame(parent, bg=C['bg'])
        img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8)

        # Notebook de tabs
        self.notebook = ttk.Notebook(img_frame, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # tab helper
        def add_tab(label):
            f = tk.Frame(self.notebook, bg=C['bg'])
            self.notebook.add(f, text=label)
            c = tk.Canvas(f, bg=C['bg'], highlightthickness=0)
            c.pack(fill=tk.BOTH, expand=True)
            return c

        self.canvas_original   = add_tab('  Original  ')
        self.canvas_cromatico  = add_tab('  Cromático  ')
        self.canvas_morfologico= add_tab('  Morfológico  ')
        self.canvas_resultado  = add_tab('  Resultado  ')

        self._mostrar_placeholder()

    def _mostrar_placeholder(self):
        for canvas in [self.canvas_original, self.canvas_cromatico,
                       self.canvas_morfologico, self.canvas_resultado]:
            canvas.delete('all')
            # Dibujamos el mensaje después de que el canvas tenga tamaño
            canvas.after(200, lambda c=canvas: c.create_text(
                c.winfo_width() // 2 or 350,
                c.winfo_height() // 2 or 250,
                text='📷  Cargue una imagen para comenzar\n\nUse el botón  "📁 Cargar Imagen"  o presione  Ctrl+O',
                font=self.font_normal, fill=C['subtext'],
                justify='center'))

    # ── Panel de resultados ──────────────────────────────────────────────

    def _create_results_panel(self, parent):
        results = tk.Frame(parent, bg=C['panel'], width=240)
        results.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        results.pack_propagate(False)

        def section_label(text):
            tk.Label(results, text=text.upper(), bg=C['panel'], fg=C['subtext'],
                     font=tkfont.Font(family='Segoe UI', size=7, weight='bold')
                     ).pack(anchor='w', padx=14, pady=(12, 4))

        # ── Badge de clasificación
        section_label('Clasificación')
        badge_frame = tk.Frame(results, bg=C['card'], bd=0)
        badge_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

        self.badge_cat = tk.Label(badge_frame, text='—',
                                  bg=C['card'], fg=C['subtext'],
                                  font=self.font_badge, pady=12)
        self.badge_cat.pack()

        self.badge_sub = tk.Label(badge_frame, text='Sin clasificar',
                                  bg=C['card'], fg=C['subtext'],
                                  font=self.font_small)
        self.badge_sub.pack(pady=(0, 10))

        # ── Separador
        tk.Frame(results, bg=C['separator'], height=1).pack(fill=tk.X, padx=10, pady=4)

        # ── Métricas con progress bars
        section_label('Métricas')
        self.metric_frames = {}
        metrics = [
            ('tonalidad',  'Tonalidad',  '°',  0, 180, C['accent2']),
            ('rugosidad',  'Rugosidad',  '',   0, 1,   C['warning']),
            ('defectos',   'Defectos',   '%',  0, 20,  C['danger']),
        ]
        for key, label, unit, mn, mx, color in metrics:
            frame = self._make_metric_card(results, label, unit, mn, mx, color)
            self.metric_frames[key] = frame

        # ── Vida útil
        tk.Frame(results, bg=C['separator'], height=1).pack(fill=tk.X, padx=10, pady=8)
        section_label('Vida Útil')
        self.lbl_vida_card = tk.Frame(results, bg=C['card'])
        self.lbl_vida_card.pack(fill=tk.X, padx=10)
        self.lbl_vida_util = tk.Label(self.lbl_vida_card, text='—',
                                      bg=C['card'], fg=C['subtext'],
                                      font=self.font_metric, pady=8)
        self.lbl_vida_util.pack()
        tk.Label(self.lbl_vida_card, text='días estimados',
                 bg=C['card'], fg=C['subtext'], font=self.font_small
                 ).pack(pady=(0, 8))

        # ── Justificación
        tk.Frame(results, bg=C['separator'], height=1).pack(fill=tk.X, padx=10, pady=8)
        section_label('Justificación')
        self.lbl_just = tk.Label(results, text='—',
                                 bg=C['panel'], fg=C['subtext'],
                                 font=self.font_small,
                                 wraplength=215, justify='left')
        self.lbl_just.pack(anchor='w', padx=14, pady=(0, 8))

    def _make_metric_card(self, parent, label, unit, mn, mx, bar_color):
        """Card de métrica con barra de progreso canvas"""
        card = tk.Frame(parent, bg=C['card'])
        card.pack(fill=tk.X, padx=10, pady=3)

        header = tk.Frame(card, bg=C['card'])
        header.pack(fill=tk.X, padx=10, pady=(8, 2))

        tk.Label(header, text=label, bg=C['card'], fg=C['subtext'],
                 font=self.font_small).pack(side=tk.LEFT)

        val_lbl = tk.Label(header, text=f'—{unit}', bg=C['card'], fg=C['text'],
                           font=self.font_heading)
        val_lbl.pack(side=tk.RIGHT)

        # Canvas barra de progreso
        bar_bg = tk.Canvas(card, bg=C['bg'], height=6,
                           highlightthickness=0, bd=0)
        bar_bg.pack(fill=tk.X, padx=10, pady=(0, 8))
        bar_fill = bar_bg.create_rectangle(0, 0, 0, 6, fill=bar_color, outline='')

        return {
            'card': card,
            'val_lbl': val_lbl,
            'bar_bg': bar_bg,
            'bar_fill': bar_fill,
            'unit': unit, 'mn': mn, 'mx': mx, 'color': bar_color
        }

    def _update_metric_card(self, key, value):
        m = self.metric_frames[key]
        u = m['unit']
        m['val_lbl'].config(text=f'{value:.2f}{u}', fg=C['text'])

        # Actualizar barra
        m['bar_bg'].update_idletasks()
        w = m['bar_bg'].winfo_width()
        mn, mx = m['mn'], m['mx']
        ratio = max(0, min(1, (value - mn) / (mx - mn) if mx != mn else 0))
        m['bar_bg'].coords(m['bar_fill'], 0, 0, int(w * ratio), 6)

    # ── Barra de estado ───────────────────────────────────────────────────

    def create_statusbar(self):
        bar = tk.Frame(self.root, bg=C['panel'], height=24)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self.status_lbl = tk.Label(bar, text='Listo — Sin imagen cargada',
                                   bg=C['panel'], fg=C['subtext'],
                                   font=self.font_small, anchor='w')
        self.status_lbl.pack(side=tk.LEFT, padx=12)

        tk.Label(bar, text='LemonVision v2.0',
                 bg=C['panel'], fg=C['border'],
                 font=self.font_small).pack(side=tk.RIGHT, padx=12)

    def _set_status(self, text, color=None):
        self.status_lbl.config(text=text, fg=color or C['subtext'])

    def _set_header_state(self, text, color):
        self.header_state_lbl.config(text=text, fg=color)
        self.header_state_dot.config(fg=color)

    # ── Lógica de imagen ──────────────────────────────────────────────────

    def abrir_imagen(self):
        filetypes = (('Imágenes', '*.jpg *.jpeg *.png *.bmp'), ('Todos', '*.*'))
        filename = filedialog.askopenfilename(
            title='Seleccionar imagen de limón', filetypes=filetypes)
        if filename:
            self.ruta_imagen_actual = filename
            self._cargar_y_mostrar_imagen(filename)

    def _cargar_y_mostrar_imagen(self, ruta):
        try:
            img_bgr = cv2.imread(ruta)
            if img_bgr is None:
                messagebox.showerror('Error', 'No se pudo cargar la imagen')
                return
            self.imagen_actual = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            self._mostrar_en_canvas(self.imagen_actual, self.canvas_original)

            # Placeholders en otros tabs
            for canvas in [self.canvas_cromatico, self.canvas_morfologico, self.canvas_resultado]:
                canvas.delete('all')
                canvas.create_text(
                    canvas.winfo_width() // 2 or 350,
                    canvas.winfo_height() // 2 or 250,
                    text="Presione  '🔍 Clasificar'  para analizar",
                    font=self.font_normal, fill=C['subtext'], justify='center')

            # Actualizar info
            h, w, ch = self.imagen_actual.shape
            kb = Path(ruta).stat().st_size / 1024
            nombre = Path(ruta).name
            self.sidebar_info.config(
                text=f'{nombre}\n{w}×{h} px  |  {kb:.0f} KB',
                fg=C['text'])
            self._set_status(f'Imagen cargada: {nombre}  |  {w}×{h} px  |  {kb:.0f} KB')
            self._set_header_state('Imagen cargada', C['accent2'])

        except Exception as e:
            messagebox.showerror('Error', f'Error al cargar imagen: {e}')

    def _mostrar_en_canvas(self, img_array, canvas):
        pil_img = Image.fromarray(img_array)
        canvas.update_idletasks()
        cw = canvas.winfo_width()  or 600
        ch = canvas.winfo_height() or 400
        pil_img.thumbnail((cw - 10, ch - 10), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        canvas.delete('all')
        canvas.create_image(cw // 2, ch // 2, image=photo)
        canvas.image = photo

    # ── Clasificación ─────────────────────────────────────────────────────

    def clasificar_imagen(self):
        if self.imagen_actual is None:
            messagebox.showwarning('Advertencia', 'Primero cargue una imagen')
            return
        self._set_status('Clasificando imagen…', C['warning'])
        self._set_header_state('Procesando…', C['warning'])
        self.root.config(cursor='watch')
        self.root.update()
        threading.Thread(target=self._clasificar_thread, daemon=True).start()

    def _clasificar_thread(self):
        try:
            self.clasificador = ClasificadorLimones(config_manager=self.config, verbose=False)
            self.clasificador.cargar_desde_array(self.imagen_actual)
            self.resultado_actual = self.clasificador.procesar(mostrar_visualizacion=False)
            self.root.after(0, self._actualizar_resultados_gui)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Error', f'Error al clasificar: {e}'))
        finally:
            self.root.after(0, lambda: self.root.config(cursor=''))

    def _actualizar_resultados_gui(self):
        if self.resultado_actual is None:
            return

        clasificacion = self.clasificador.clasificacion
        vector        = self.clasificador.vector_caracteristicas

        cat       = clasificacion['categoria']
        cumple    = clasificacion['cumple_exportacion']
        vida_util = clasificacion['vida_util']
        just      = clasificacion['justificacion']

        # Badge
        badge_color = C['success'] if cumple else C['warning']
        self.badge_cat.config(text=cat, fg=badge_color)
        estado_txt = '✔ Apto para exportación' if cumple else '✗ No apto para exportación'
        self.badge_sub.config(text=estado_txt,
                              fg=badge_color)

        # Métricas (vector = [tonalidad, rugosidad, defectos])
        self._update_metric_card('tonalidad', vector[0])
        self._update_metric_card('rugosidad', vector[1])
        self._update_metric_card('defectos',  vector[2])

        # Vida útil
        vida_str = vida_util.split()[0] if isinstance(vida_util, str) and vida_util else '?'
        self.lbl_vida_util.config(text=vida_str, fg=badge_color)

        # Justificación
        self.lbl_just.config(text=just, fg=C['subtext'])

        # Estado
        self._set_status(f'Clasificación completada: {cat}', C['accent'])
        self._set_header_state(cat, badge_color)

        messagebox.showinfo('Clasificación', f'Resultado: {cat}\n{estado_txt}')

    # ── Acciones ──────────────────────────────────────────────────────────

    def reclasificar(self):
        if self.imagen_actual is not None:
            self.clasificar_imagen()

    def abrir_configuracion(self):
        ConfigDialog(self.root, self.config, self.reclasificar)

    def abrir_editor_grupos(self):
        from gui.grupos_editor import GruposEditorWindow
        GruposEditorWindow(self.root)

    def abrir_modo_industrial(self):
        try:
            from gui.industrial_mode import ModoIndustrial
            ModoIndustrial(self.root)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo abrir Modo Industrial:\n{e}')

    def procesamiento_lotes(self):
        messagebox.showinfo('Próximamente', 'Función de procesamiento por lotes en desarrollo')

    def exportar_pdf(self):
        if self.resultado_actual is None:
            messagebox.showwarning('Advertencia', 'Primero clasifique una imagen')
            return
        messagebox.showinfo('Próximamente', 'Exportación a PDF en desarrollo')

    def exportar_csv(self):
        if self.resultado_actual is None:
            messagebox.showwarning('Advertencia', 'Primero clasifique una imagen')
            return
        messagebox.showinfo('Próximamente', 'Exportación a CSV en desarrollo')

    def exportar_json(self):
        if self.resultado_actual is None:
            messagebox.showwarning('Advertencia', 'Primero clasifique una imagen')
            return
        messagebox.showinfo('Próximamente', 'Exportación a JSON en desarrollo')

    def mostrar_ayuda(self):
        messagebox.showinfo('Ayuda', (
            'Sistema de Clasificación de Limones\n\n'
            '1. Cargar Imagen: botón 📁 o Ctrl+O\n'
            '2. Clasificar: botón 🔍\n'
            '3. Grupos Personalizados: botón ⭐ (ventana independiente)\n'
            '4. Exportar: botones PDF / CSV / JSON\n\n'
            'Atajos:\n'
            '  Ctrl+O  — Abrir imagen\n'
            '  Ctrl+S  — Exportar PDF\n'
            '  F5      — Reclasificar'))

    def mostrar_acerca_de(self):
        messagebox.showinfo('Acerca de', (
            'LemonVision v2.0\n'
            'Sistema Automatizado de Clasificación de Limones\n\n'
            'Basado en Álgebra Lineal y Visión por Computadora\n'
            '© 2026 — Sistema de Clasificación Agroindustrial'))

    # ── Utilidades ────────────────────────────────────────────────────────

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')


# ═══════════════════════════════════════════════════════════════════════════════
# Diálogo de Configuración
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigDialog:
    """Diálogo de parámetros con tema oscuro"""

    def __init__(self, parent, config_manager, callback_reclasificar):
        self.config   = config_manager
        self.callback = callback_reclasificar

        dlg = tk.Toplevel(parent)
        dlg.title('Configuración de Parámetros')
        dlg.geometry('480x420')
        dlg.configure(bg=C['bg'])
        dlg.transient(parent)
        dlg.grab_set()
        self.dlg = dlg

        self._build()

    def _build(self):
        d = self.dlg

        # Header
        hdr = tk.Frame(d, bg=C['panel'])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text='⚙️  Parámetros de Clasificación',
                 bg=C['panel'], fg=C['text'],
                 font=tkfont.Font(family='Segoe UI', size=12, weight='bold'),
                 pady=14).pack(padx=16, anchor='w')

        body = tk.Frame(d, bg=C['bg'])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        def section(text):
            tk.Label(body, text=text, bg=C['bg'], fg=C['accent'],
                     font=tkfont.Font(family='Segoe UI', size=9, weight='bold')
                     ).pack(anchor='w', pady=(12, 4))

        def slider_row(label, var, from_, to, suffix=''):
            row = tk.Frame(body, bg=C['bg'])
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label, bg=C['bg'], fg=C['text'],
                     font=tkfont.Font(family='Segoe UI', size=9), width=28, anchor='w'
                     ).pack(side=tk.LEFT)
            sl = tk.Scale(row, from_=from_, to=to, variable=var,
                          orient=tk.HORIZONTAL, length=200,
                          bg=C['panel'], fg=C['text'], troughcolor=C['card'],
                          highlightthickness=0, bd=0,
                          activebackground=C['accent'], resolution=0.1)
            sl.pack(side=tk.LEFT)
            lbl = tk.Label(row, textvariable=var if suffix == '' else None,
                           bg=C['bg'], fg=C['accent'],
                           font=tkfont.Font(family='Segoe UI', size=9), width=7)
            lbl.pack(side=tk.LEFT, padx=4)

            if suffix:
                def _upd(*_):
                    lbl.config(text=f'{var.get():.1f}{suffix}')
                var.trace_add('write', _upd)
                _upd()
            return sl

        section('Rugosidad')
        self.rugosidad_var = tk.DoubleVar(value=self.config.get_rugosidad_umbral())
        slider_row('Umbral de Rugosidad (Exportación)', self.rugosidad_var, 10, 100)

        section('Defectos')
        self.defectos_var = tk.DoubleVar(value=self.config.get_defectos_maximo())
        slider_row('Porcentaje máximo de defectos', self.defectos_var, 1, 20, '%')

        section('Tonalidad')
        tk.Label(body,
                 text='Verde: 35–85° | Pintón: 20–34° | Amarillo: 0–19°\nEdite config.json para cambiar los rangos.',
                 bg=C['bg'], fg=C['subtext'],
                 font=tkfont.Font(family='Segoe UI', size=8),
                 justify='left').pack(anchor='w', padx=4, pady=4)

        # Botones
        btn_row = tk.Frame(d, bg=C['panel'])
        btn_row.pack(fill=tk.X, side=tk.BOTTOM)

        def dark_btn(parent, text, cmd, accent=False):
            bg = C['accent'] if accent else C['card']
            fg = '#000' if accent else C['text']
            hbg = C['accent_dark'] if accent else C['card_hover']
            b = tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg, relief='flat',
                          font=tkfont.Font(family='Segoe UI', size=9),
                          padx=14, pady=8, cursor='hand2')
            b.pack(side=tk.RIGHT, padx=6, pady=10)
            b.bind('<Enter>', lambda e: b.config(bg=hbg))
            b.bind('<Leave>', lambda e: b.config(bg=bg))

        dark_btn(btn_row, 'Cancelar', self.dlg.destroy)
        dark_btn(btn_row, 'Guardar y Aplicar', self._guardar, accent=True)

        def _restaurar():
            self.config.create_default_config()
            self.rugosidad_var.set(self.config.get_rugosidad_umbral())
            self.defectos_var.set(self.config.get_defectos_maximo())
        b_res = tk.Button(btn_row, text='Restaurar defaults', command=_restaurar,
                          bg=C['bg'], fg=C['subtext'], relief='flat',
                          font=tkfont.Font(family='Segoe UI', size=9),
                          padx=10, pady=8, cursor='hand2')
        b_res.pack(side=tk.LEFT, padx=10, pady=10)

    def _guardar(self):
        self.config.set_rugosidad_umbral(self.rugosidad_var.get())
        self.config.set_defectos_maximo(self.defectos_var.get())
        self.config.save()
        messagebox.showinfo('Éxito', 'Configuración guardada')
        self.dlg.destroy()
        if self.callback:
            if messagebox.askyesno('Reclasificar',
                                   '¿Reclasificar la imagen actual con la nueva configuración?'):
                self.callback()


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = LemonClassifierApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
