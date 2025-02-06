from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.app import App
from database import execute_query, fetch_data
from datetime import datetime
from kivy.core.window import Window

KV = '''
<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<IngresosScreen>:
    MDBoxLayout:
        orientation: 'horizontal'
        md_bg_color: app.theme_cls.bg_dark
        
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.50
            md_bg_color: app.theme_cls.bg_dark
            padding: "8dp"
            spacing: "8dp"
            
            MDLabel:
                text: "Acciones"
                font_style: "H6"
                size_hint_y: None
                height: self.texture_size[1]
            
            ScrollView:
                MDList:
                    MenuButton:
                        text: "Registrar Ingreso"
                        icon: "plus-circle"
                        on_release: root.confirmar_ingreso()
                    
                    MenuButton:
                        text: "Ir a Egresos Hardware"
                        icon: "database-export"
                        on_release: root.change_screen('egresos')  

                    MenuButton:
                        text: "Ir a Agregar Artículo"
                        icon: "plus-circle"
                        on_release: root.change_screen('agregar_articulo')
                    
                    MenuButton:
                        text: "Ir a Egresos Hardware"
                        icon: "database-export"
                        on_release: root.change_screen('egresos')
                    
                    MenuButton:
                        text: "Ir a Consulta Stock Hardware"
                        icon: "clipboard-list"
                        on_release: root.change_screen('consulta_stock')
                    
                    MenuButton:
                        text: "Ir a Histórico Movimientos"
                        icon: "history"
                        on_release: root.change_screen('historico_movimientos')
                    
                    MenuButton:
                        text: "Volver al Menú Principal"
                        icon: "home"
                        on_release: root.manager.current = 'menu_principal'
                    
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
                title: "Registrar Ingreso"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: buscar_articulo
                        hint_text: "Buscar artículo"
                        on_text: root.filtrar_articulos(self.text)
                        on_text_validate: root.on_buscar_enter()
                    
                    MDTextField:
                        id: articulo
                        hint_text: "Seleccionar artículo"
                        on_focus: if self.focus: root.menu.open()
                    
                    MDTextField:
                        id: cantidad
                        hint_text: "Cantidad"
                        on_text_validate: root.on_cantidad_enter()
                        input_filter: 'int'
                    
                    MDLabel:
                        id: message
                        text: ""
                        theme_text_color: "Error"
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

class ConfirmacionPopup(Popup):
    def __init__(self, confirmar_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Confirmar'
        self.size_hint = (0.6, 0.4)
        content = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(MDLabel(text='¿Está seguro de que desea registrar este ingreso?'))
        buttons_layout = MDBoxLayout(orientation='horizontal', size_hint_y=0.2)
        btn_cancel = Button(text='Cancelar')
        btn_confirm = Button(text='Confirmar')
        btn_cancel.bind(on_press=self.dismiss)
        btn_confirm.bind(on_press=lambda x: self.confirmar(confirmar_callback))
        buttons_layout.add_widget(btn_cancel)
        buttons_layout.add_widget(btn_confirm)
        content.add_widget(buttons_layout)
        self.content = content

    def confirmar(self, callback):
        callback()
        self.dismiss()

class IngresosScreen(MDScreen):
    articulos = ListProperty([])
    menu = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_enter(self):
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_articulos()

    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if not permisos or 'ingresos' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de ingresos')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_articulos(self, filtro=''):
        articulos = fetch_data("SELECT nombre FROM articulos WHERE nombre LIKE ?", ('%' + filtro + '%',))
        menu_items = [
            {
                "text": articulo[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=articulo[0]: self.seleccionar_articulo(x),
            } for articulo in articulos
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.articulo,
            items=menu_items,
            width_mult=4,
        )

    def filtrar_articulos(self, filtro):
        self.actualizar_lista_articulos(filtro)

    def seleccionar_articulo(self, articulo):
        self.ids.articulo.text = articulo
        self.menu.dismiss()

    def confirmar_ingreso(self):
        popup = ConfirmacionPopup(confirmar_callback=self.registrar_ingreso)
        popup.open()

    def registrar_ingreso(self):
        articulo = self.ids.articulo.text
        cantidad = self.ids.cantidad.text
        if not articulo or not cantidad:
            self.ids.message.text = 'Por favor, complete todos los campos'
            return
        try:
            cantidad = int(cantidad)
        except ValueError:
            self.ids.message.text = 'La cantidad debe ser un número entero'
            return

        articulo_id = fetch_data("SELECT id FROM articulos WHERE nombre = ?", (articulo,))
        if not articulo_id:
            self.ids.message.text = 'Artículo no encontrado'
            return
        articulo_id = articulo_id[0][0]

        execute_query("UPDATE articulos SET cantidad = cantidad + ? WHERE id = ?", (cantidad, articulo_id))
        execute_query("INSERT INTO movimientos (articulo_id, tipo, cantidad, fecha) VALUES (?, ?, ?, ?)",
                      (articulo_id, 'ingreso', cantidad, datetime.now()))
        self.ids.message.text = 'Ingreso registrado correctamente'
        self.clear_fields()

    def on_buscar_enter(self):
        self.ids.articulo.focus = True

    def on_cantidad_enter(self):
        self.confirmar_ingreso()

    def clear_fields(self):
        self.ids.articulo.text = ''
        self.ids.cantidad.text = ''

    def logout(self):
        App.get_running_app().stop()
        Window.close()

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

Builder.load_string(KV)