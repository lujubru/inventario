from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.app import App
from kivy.properties import StringProperty
from database import fetch_data
from utils.pdf_generator import generar_pdf
from pathlib import Path
from kivy.core.window import Window

KV = '''
<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<MovimientoTonerRow>:
    orientation: 'horizontal'
    adaptive_height: True
    MDLabel:
        text: root.toner
        size_hint_x: 0.2
    MDLabel:
        text: root.tipo
        size_hint_x: 0.15
    MDLabel:
        text: root.cantidad
        size_hint_x: 0.1
    MDLabel:
        text: root.usuario
        size_hint_x: 0.15
    MDLabel:
        text: root.observaciones
        size_hint_x: 0.25
    MDLabel:
        text: root.fecha
        size_hint_x: 0.15

<HistoricoMovimientosTonerScreen>:
    MDBoxLayout:
        orientation: 'horizontal'
        md_bg_color: app.theme_cls.bg_dark
        
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.50
            md_bg_color: app.theme_cls.bg_dark
            padding: "4dp"
            spacing: "4dp"
            
            MDLabel:
                text: "Acciones"
                font_style: "H6"
                size_hint_y: None
                height: self.texture_size[1]
            
            ScrollView:
                MDList:
                    spacing: "2dp"
                    MenuButton:
                        text: "Buscar Movimiento Toner"
                        icon: "magnify"
                        on_release: root.buscar_movimiento_toner()
                    
                    MenuButton:
                        text: "Guardar PDF"
                        icon: "file-pdf-box"
                        on_release: root.guardar_pdf()   

                    MenuButton:
                        text: "Ir a Agregar Toner"
                        icon: "plus-circle"
                        on_release: root.change_screen('agregar_toner')
                    
                    MenuButton:
                        text: "Ir a Ingresos Toner"
                        icon: "database-import"
                        on_release: root.change_screen('ingresos_toner')
                    
                    MenuButton:
                        text: "Ir a Egresos Toner"
                        icon: "database-export"
                        on_release: root.change_screen('egresos_toner')
                    
                    MenuButton:
                        text: "Ir a Consulta Stock Toner"
                        icon: "clipboard-list"
                        on_release: root.change_screen('consulta_stock_toner')
                    
                    MenuButton:
                        text: "Volver al Menú Principal"
                        icon: "home"
                        on_release: root.volver_menu_principal()
                    
                    MenuButton:
                        text: "Cerrar Sesion"
                        icon: "logout"
                        on_release: root.change_screen('login')
                    
                    MenuButton:
                        text: "Salir"
                        icon: "logout"
                        on_release: root.logout()
        
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.75
            
            MDTopAppBar:
                title: "Histórico de Movimientos de Toner"
                elevation: 4
                height: "48dp"
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: "8dp"
                spacing: "4dp"
                
                MDTextField:
                    id: busqueda_input
                    hint_text: "Buscar movimiento de toner"
                    on_text_validate: root.buscar_movimiento_toner()
                    size_hint_y: None
                    height: "40dp"
                
                MDBoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: "40dp"
                    MDLabel:
                        text: "Toner"
                        bold: True
                        size_hint_x: 0.2
                    MDLabel:
                        text: "Tipo"
                        bold: True
                        size_hint_x: 0.15
                    MDLabel:
                        text: "Cantidad"
                        bold: True
                        size_hint_x: 0.1
                    MDLabel:
                        text: "Usuario"
                        bold: True
                        size_hint_x: 0.15
                    MDLabel:
                        text: "Observaciones"
                        bold: True
                        size_hint_x: 0.25
                    MDLabel:
                        text: "Fecha"
                        bold: True
                        size_hint_x: 0.15
                
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    MDList:
                        id: movimientos_toner_grid
                        spacing: "2dp"
                        padding: "0dp"
                
                MDLabel:
                    id: message
                    text: ""
                    theme_text_color: "Error"
                    size_hint_y: None
                    height: self.texture_size[1]
'''

class ErrorPopup(Popup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Error'
        self.size_hint = (0.6, 0.4)
        content = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(MDLabel(text=message))
        button = Button(text='Cerrar', size_hint=(1, 0.2))
        button.bind(on_press=self.dismiss)
        content.add_widget(button)
        self.content = content

class MovimientoTonerRow(MDBoxLayout):
    toner = StringProperty()
    tipo = StringProperty()
    cantidad = StringProperty()
    usuario = StringProperty()
    observaciones = StringProperty()
    fecha = StringProperty()

class HistoricoMovimientosTonerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_enter(self):
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_movimientos_toner()

    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if not permisos or 'historico_movimientos' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de histórico de movimientos de toner')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_movimientos_toner(self):
        movimientos = fetch_data("""
            SELECT t.nombre, mt.tipo, mt.cantidad, mt.usuario, mt.observaciones, mt.fecha
            FROM movimientos_toner mt 
            JOIN toners t ON mt.toner_id = t.id 
            ORDER BY mt.fecha DESC
        """)
        self.ids.movimientos_toner_grid.clear_widgets()
        for movimiento in movimientos:
            self.ids.movimientos_toner_grid.add_widget(MovimientoTonerRow(
                toner=str(movimiento[0]),
                tipo=str(movimiento[1]),
                cantidad=str(movimiento[2]),
                usuario=str(movimiento[3]),
                observaciones=str(movimiento[4]),
                fecha=str(movimiento[5])
            ))

    def buscar_movimiento_toner(self):
        busqueda = self.ids.busqueda_input.text
        movimientos = fetch_data("""
            SELECT t.nombre, mt.tipo, mt.cantidad, mt.usuario, mt.observaciones, mt.fecha
            FROM movimientos_toner mt 
            JOIN toners t ON mt.toner_id = t.id 
            WHERE t.nombre LIKE ? OR mt.tipo LIKE ? OR mt.observaciones LIKE ? OR mt.usuario LIKE ?
            ORDER BY mt.fecha DESC
        """, ('%'+busqueda+'%', '%'+busqueda+'%', '%'+busqueda+'%', '%'+busqueda+'%'))
        self.ids.movimientos_toner_grid.clear_widgets()
        for movimiento in movimientos:
            self.ids.movimientos_toner_grid.add_widget(MovimientoTonerRow(
                toner=str(movimiento[0]),
                tipo=str(movimiento[1]),
                cantidad=str(movimiento[2]),
                usuario=str(movimiento[3]),
                observaciones=str(movimiento[4]),
                fecha=str(movimiento[5])
            ))

    def guardar_pdf(self):
        movimientos = fetch_data("""
            SELECT t.nombre, mt.tipo, mt.cantidad, mt.usuario, mt.observaciones, mt.fecha
            FROM movimientos_toner mt 
            JOIN toners t ON mt.toner_id = t.id 
            ORDER BY mt.fecha DESC
        """)
        headers = ['Toner', 'Tipo', 'Cantidad', 'Usuario', 'Observaciones', 'Fecha']
        user_documents_dir = Path.home() / "Documents"
        file_path = user_documents_dir / 'movimientos_toner.pdf'
        generar_pdf(str(file_path), movimientos, headers)
        self.ids.message.text = f'PDF guardado como {file_path}'

    def volver_menu_principal(self):
        self.manager.current = 'menu_principal'

    def logout(self):
        App.get_running_app().stop()
        Window.close()

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

Builder.load_string(KV)