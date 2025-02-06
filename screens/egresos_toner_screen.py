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

<EgresosTonerScreen>:
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
                        text: "Registrar Egreso de Toner"
                        icon: "minus-circle"
                        on_release: root.confirmar_egreso()
                    
                    MenuButton:
                        text: "Agregar Toner"
                        icon: "printer"
                        on_release: root.change_screen('agregar_toner')
                    
                    MenuButton:
                        text: "Ir a Ingresos Toner"
                        icon: "inbox-arrow-down"
                        on_release: root.change_screen('ingresos_toner')
                    
                    MenuButton:
                        text: "Ir a Consulta Toner"
                        icon: "magnify"
                        on_release: root.change_screen('consulta_toner')
                    
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
                title: "Registrar Egreso de Toner"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: buscar_toner
                        hint_text: "Buscar toner"
                        on_text: root.filtrar_toners(self.text)
                        on_text_validate: root.on_buscar_enter()
                    
                    MDTextField:
                        id: toner
                        hint_text: "Seleccionar toner"
                        on_focus: if self.focus: root.menu.open()
                    
                    MDTextField:
                        id: cantidad
                        hint_text: "Cantidad"
                        input_filter: 'int'
                        on_text_validate: root.on_cantidad_enter()
                    
                    MDTextField:
                        id: observaciones
                        hint_text: "Observaciones"
                        on_text_validate: root.on_observaciones_enter()
                        multiline: False
                    
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
        content.add_widget(MDLabel(text='¿Está seguro de que desea registrar este egreso de toner?'))
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

class EgresosTonerScreen(MDScreen):
    toners = ListProperty([])
    menu = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_enter(self):
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_toners()

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if not permisos or 'egresos_toner' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de egresos de toner')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_toners(self, filtro=''):
        toners = fetch_data("SELECT nombre FROM toners WHERE nombre LIKE ?", ('%' + filtro + '%',))
        menu_items = [
            {
                "text": toner[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=toner[0]: self.seleccionar_toner(x),
            } for toner in toners
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.toner,
            items=menu_items,
            width_mult=4,
        )

    def filtrar_toners(self, filtro):
        self.actualizar_lista_toners(filtro)

    def seleccionar_toner(self, toner):
        self.ids.toner.text = toner
        self.menu.dismiss()

    def on_cantidad_enter(self):
        self.ids.observaciones.focus = True

    def on_buscar_enter(self):
        self.ids.toner.focus = True

    def on_observaciones_enter(self):
        self.confirmar_egreso()

    def confirmar_egreso(self):
        popup = ConfirmacionPopup(confirmar_callback=self.registrar_egreso)
        popup.open()
        
    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def registrar_egreso(self):
        toner = self.ids.toner.text
        cantidad = self.ids.cantidad.text
        observaciones = self.ids.observaciones.text
        if not toner or not cantidad or not observaciones:
            self.ids.message.text = 'Por favor, complete todos los campos'
            return
        try:
            cantidad = int(cantidad)
        except ValueError:
            self.ids.message.text = 'La cantidad debe ser un número entero'
            return

        toner_id = fetch_data("SELECT id FROM toners WHERE nombre = ?", (toner,))
        if not toner_id:
            self.ids.message.text = 'Toner no encontrado'
            return
        toner_id = toner_id[0][0]

        stock_actual = fetch_data("SELECT cantidad FROM toners WHERE id = ?", (toner_id,))[0][0]
        if stock_actual >= cantidad:
            execute_query("UPDATE toners SET cantidad = cantidad - ? WHERE id = ?", (cantidad, toner_id))
            usuario_actual = self.app.usuario_actual
            execute_query("INSERT INTO movimientos_toner (toner_id, tipo, cantidad, fecha, observaciones, usuario) VALUES (?, ?, ?, ?, ?, ?)",
                          (toner_id, 'egreso', cantidad, datetime.now(), observaciones, usuario_actual))
            self.ids.message.text = 'Egreso de toner registrado correctamente'
            self.clear_fields()
        else:
            self.ids.message.text = 'Stock insuficiente'

    def clear_fields(self):
        self.ids.buscar_toner.text = ''
        self.ids.toner.text = ''
        self.ids.cantidad.text = ''
        self.ids.observaciones.text = ''

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

    def logout(self):
        App.get_running_app().stop()
        Window.close()

Builder.load_string(KV)