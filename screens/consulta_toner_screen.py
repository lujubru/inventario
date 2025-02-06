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
import win32print
import win32api
import win32print
import win32api
import os

KV = '''
<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<TonerRow>:
    orientation: 'horizontal'
    adaptive_height: True
    spacing: "2dp"
    MDLabel:
        text: root.articulo
        size_hint_x: 0.7
        font_size: "14sp"
    MDLabel:
        text: root.cantidad
        size_hint_x: 0.3
        font_size: "14sp"

<ConsultaTonerScreen>:
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
                        text: "Buscar Artículo"
                        icon: "magnify"
                        on_release: root.buscar_toner()
                    
                    MenuButton:
                        text: "Guardar PDF"
                        icon: "file-pdf-box"
                        on_release: root.guardar_pdf()
                    
                    MenuButton:
                        text: "Imprimir Stock Toners"
                        icon: "printer"
                        on_release: root.mostrar_impresoras()

                    MenuButton:
                        text: "Ir a Agregar Toner"
                        icon: "printer"
                        on_release: root.change_screen('agregar_toner')
                    
                    MenuButton:
                        text: "Ir a Ingresos Toner"
                        icon: "inbox-arrow-down"
                        on_release: root.change_screen('ingresos_toner')
                    
                    MenuButton:
                        text: "Ir a Egresos Toner"
                        icon: "inbox-arrow-up"
                        on_release: root.change_screen('egresos_toner')
                    
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
                title: "Consulta de Stock"
                elevation: 4
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: "8dp"
                spacing: "4dp"
                
                MDTextField:
                    id: busqueda_input
                    hint_text: "Buscar artículo"
                    on_text_validate: root.buscar_toner()
                    size_hint_y: None
                    height: "40dp"
                
                MDBoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: "30dp"
                    MDLabel:
                        text: "Artículo"
                        bold: True
                        size_hint_x: 0.7
                        font_size: "16sp"
                    MDLabel:
                        text: "Cantidad"
                        bold: True
                        size_hint_x: 0.3
                        font_size: "16sp"
                
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    MDList:
                        id: toners_grid
                        spacing: "1dp"
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

class TonerRow(MDBoxLayout):
    articulo = StringProperty()
    cantidad = StringProperty()

class ConsultaTonerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_enter(self):
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_toners()

    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if not permisos or 'consulta_toner' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de consulta de stock')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_toners(self):
        toners = fetch_data("SELECT nombre, cantidad FROM toners")
        self.ids.toners_grid.clear_widgets()
        for toner in toners:
            self.ids.toners_grid.add_widget(TonerRow(articulo=str(toner[0]), cantidad=str(toner[1])))

    def buscar_toner(self):
        busqueda = self.ids.busqueda_input.text.lower()
        toners = fetch_data("SELECT nombre, cantidad FROM toners")
        self.ids.toners_grid.clear_widgets()
        for toner in toners:
            if busqueda in toner[0].lower():
                self.ids.toners_grid.add_widget(TonerRow(articulo=str(toner[0]), cantidad=str(toner[1])))

    def guardar_pdf(self):
        toners = fetch_data("SELECT nombre, cantidad FROM toners")
        headers = ['Artículo', 'Cantidad']
        user_documents_dir = Path.home() / "Documents"
        file_path = user_documents_dir / 'toners.pdf'
        generar_pdf(str(file_path), toners, headers)
        self.ids.message.text = f'PDF guardado como {file_path}'

    def mostrar_impresoras(self):
        impresoras = [impresora[2] for impresora in win32print.EnumPrinters(2)]
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(MDLabel(text="Seleccione una impresora:"))
        for impresora in impresoras:
            btn = Button(text=impresora, size_hint_y=None, height=44)
            btn.bind(on_release=lambda x, printer=impresora: self.imprimir_stock(printer))
            content.add_widget(btn)
        
        popup = Popup(title="Impresoras disponibles", content=content, size_hint=(0.8, 0.9))
        popup.open()

    def imprimir_stock(self, impresora):
        toners = fetch_data("SELECT nombre, cantidad FROM toners")
        headers = ['Artículo', 'Cantidad']
        user_documents_dir = Path.home() / "Documents"
        file_path = user_documents_dir / 'stock_temp.pdf'
        generar_pdf(str(file_path), toners, headers)
        
        try:
            win32print.SetDefaultPrinter(impresora)
            if impresora == "Microsoft Print to PDF":
                # Abrir el archivo PDF directamente
                os.startfile(str(file_path))
                self.ids.message.text = f'Archivo PDF abierto. Por favor, seleccione "Microsoft Print to PDF" como impresora.'
            else:
                # Intentar imprimir usando ShellExecute
                win32api.ShellExecute(0, "print", str(file_path), None, ".", 0)
                self.ids.message.text = f'Imprimiendo stock en {impresora}'
        except Exception as e:
            # Si falla, intentar abrir el archivo PDF directamente
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(str(file_path))
                elif os.name == 'posix':  # macOS y Linux
                    subprocess.call(('xdg-open', str(file_path)))
                self.ids.message.text = f'No se pudo imprimir directamente. Se ha abierto el archivo PDF.'
            except Exception as e2:
                self.ids.message.text = f'Error al imprimir: {str(e)}. También falló al abrir el PDF: {str(e2)}'

    def volver_menu_principal(self):
        self.manager.current = 'menu_principal'

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

    def logout(self):
        App.get_running_app().stop()
        Window.close()

Builder.load_string(KV)