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
from kivy.core.window import Window

KV = '''
<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<AgregarTonerScreen>:
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
                        text: "Agregar Toner"
                        icon: "plus-circle"
                        on_release: root.agregar_toner()
                    
                    MenuButton:
                        text: "Borrar Toner"
                        icon: "minus-circle"
                        on_release: root.borrar_toner()
                    
                    MenuButton:
                        text: "Modificar Toner"
                        icon: "minus-circle"
                        on_release: root.modificar_toner()
                    
                    MenuButton:
                        text: "Ir a Ingresos Toner"
                        icon: "inbox-arrow-down"
                        on_release: root.change_screen('ingresos_toner')
                    
                    MenuButton:
                        text: "Ir a Egresos Toner"
                        icon: "inbox-arrow-up"
                        on_release: root.change_screen('egresos_toner')
                    
                    MenuButton:
                        text: "Ir a Consulta Toner"
                        icon: "magnify"
                        on_release: root.change_screen('consulta_toner')
                    
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
                title: "Agregar Toner"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: toners_spinner
                        hint_text: "Seleccionar toner"
                        on_focus: if self.focus: root.menu.open()
                    
                    MDTextField:
                        id: codigo
                        hint_text: "Código del toner"
                        on_text_validate: root.on_codigo_enter()
                    
                    MDTextField:
                        id: nombre
                        hint_text: "Nombre del toner"
                        on_text_validate: root.on_nombre_enter()
                    
                    MDTextField:
                        id: cantidad
                        hint_text: "Cantidad"
                        input_filter: 'int'
                        on_text_validate: root.on_cantidad_enter()
                    
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
        content.add_widget(MDLabel(text='¿Está seguro de que desea agregar este toner?'))
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

class AgregarTonerScreen(MDScreen):
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
        if not permisos or 'agregar_toner' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de agregar toners')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_toners(self):
        toners = fetch_data("SELECT nombre FROM toners")
        menu_items = [
            {
                "text": toner[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=toner[0]: self.seleccionar_toner(x),
            } for toner in toners
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.toners_spinner,
            items=menu_items,
            width_mult=4,
        )

    def seleccionar_toner(self, toner):
        self.ids.toners_spinner.text = toner
        self.cargar_datos_toner(toner)
        self.menu.dismiss()

    def cargar_datos_toner(self, toner):
        datos = fetch_data("SELECT codigo, cantidad FROM toners WHERE nombre = ?", (toner,))
        if datos:
            self.ids.codigo.text = datos[0][0]
            self.ids.nombre.text = toner
            self.ids.cantidad.text = str(datos[0][1])

    def agregar_toner(self):
        codigo = self.ids.codigo.text
        nombre = self.ids.nombre.text
        cantidad = self.ids.cantidad.text
        if not codigo or not nombre or not cantidad:
            self.ids.message.text = 'Por favor, complete todos los campos'
            return
        try:
            cantidad = int(cantidad)
        except ValueError:
            self.ids.message.text = 'La cantidad debe ser un número entero'
            return
        
        existente = fetch_data("SELECT * FROM toners WHERE codigo = ? OR nombre = ?", (codigo, nombre))
        if existente:
            error_popup = ErrorPopup(message='Toner o código repetido')
            error_popup.open()
            return
        
        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_agregar_toner(codigo, nombre, cantidad))
        popup.open()

    def confirmar_agregar_toner(self, codigo, nombre, cantidad):
        execute_query("INSERT INTO toners (codigo, nombre, cantidad) VALUES (?, ?, ?)", (codigo, nombre, cantidad))
        self.ids.message.text = 'Toner agregado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_toners()

    def borrar_toner(self):
        toner = self.ids.toners_spinner.text
        if not toner:
            self.ids.message.text = 'Por favor, seleccione un toner para borrar'
            return
        
        execute_query("DELETE FROM toners WHERE nombre = ?", (toner,))
        self.ids.message.text = 'Toner borrado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_toners()

    def on_codigo_enter(self):
        self.ids.nombre.focus = True

    def on_nombre_enter(self):
        self.ids.cantidad.focus = True

    def on_cantidad_enter(self):
        self.agregar_toner()
        
    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def limpiar_campos(self):
        self.ids.codigo.text = ''
        self.ids.nombre.text = ''
        self.ids.cantidad.text = ''
        self.ids.toners_spinner.text = ''

    def modificar_toner(self):
        toner = self.ids.toners_spinner.text
        codigo = self.ids.codigo.text
        nombre = self.ids.nombre.text
        cantidad = self.ids.cantidad.text

        if not toner or not codigo or not nombre or not cantidad:
            self.ids.message.text = 'Por favor, seleccione un toner y complete todos los campos'
            return

        try:
            cantidad = int(cantidad)
        except ValueError:
            self.ids.message.text = 'La cantidad debe ser un número entero'
            return

        # Verificar si el nuevo código o nombre ya existe para otro toner
        existente = fetch_data("SELECT * FROM toners WHERE (codigo = ? OR nombre = ?) AND nombre != ?", (codigo, nombre, toner))
        if existente:
            error_popup = ErrorPopup(message='Código o nombre ya existe para otro toner')
            error_popup.open()
            return

        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_modificar_toner(toner, codigo, nombre, cantidad))
        popup.open()

    def confirmar_modificar_toner(self, toner_original, codigo, nombre, cantidad):
        execute_query("UPDATE toners SET codigo = ?, nombre = ?, cantidad = ? WHERE nombre = ?", 
                      (codigo, nombre, cantidad, toner_original))
        self.ids.message.text = 'Toner modificado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_toners()

    def volver_menu_principal(self):
        self.manager.current = 'menu_principal'

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

    def logout(self):
        App.get_running_app().stop()
        Window.close()

Builder.load_string(KV)