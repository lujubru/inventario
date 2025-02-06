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

<AgregarArticuloScreen>:
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
                        text: "Agregar Artículo"
                        icon: "plus-circle"
                        on_release: root.agregar_articulo()
                    
                    MenuButton:
                        text: "Borrar Artículo"
                        icon: "minus-circle"
                        on_release: root.borrar_articulo()
                    
                    MenuButton:
                        text: "Modificar Artículo"
                        icon: "minus-circle"
                        on_release: root.modificar_articulo()
                    
                    MenuButton:
                        text: "Ir a Ingresos Hardware"
                        icon: "database-import"
                        on_release: root.change_screen('ingresos')
                    
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
                title: "Agregar Artículo"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: articulos_spinner
                        hint_text: "Seleccionar artículo"
                        on_focus: if self.focus: root.menu.open()
                    
                    MDTextField:
                        id: codigo
                        hint_text: "Código del artículo"
                        on_text_validate: root.on_codigo_enter()
                    
                    MDTextField:
                        id: nombre
                        hint_text: "Nombre del artículo"
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
        content.add_widget(MDLabel(text='¿Está seguro de que desea agregar este artículo?'))
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

class AgregarArticuloScreen(MDScreen):
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
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = %s", (usuario_actual,))
        if not permisos or 'agregar_articulos' not in permisos[0][0].split(','):
            error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de agregar artículos')
            error_popup.bind(on_dismiss=self.return_to_menu)
            error_popup.open()

    def actualizar_lista_articulos(self):
        articulos = fetch_data("SELECT nombre FROM articulos")
        menu_items = [
            {
                "text": articulo[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=articulo[0]: self.seleccionar_articulo(x),
            } for articulo in articulos
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.articulos_spinner,
            items=menu_items,
            width_mult=4,
        )

    def seleccionar_articulo(self, articulo):
        self.ids.articulos_spinner.text = articulo
        self.cargar_datos_articulo(articulo)
        self.menu.dismiss()

    def cargar_datos_articulo(self, articulo):
        datos = fetch_data("SELECT codigo, cantidad FROM articulos WHERE nombre = %s", (articulo,))
        if datos:
            self.ids.codigo.text = datos[0][0]
            self.ids.nombre.text = articulo
            self.ids.cantidad.text = str(datos[0][1])

    def agregar_articulo(self):
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
        
        existente = fetch_data("SELECT * FROM articulos WHERE codigo = %s OR nombre = %s", (codigo, nombre))
        if existente:
            error_popup = ErrorPopup(message='Artículo o código repetido')
            error_popup.open()
            return
        
        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_agregar_articulo(codigo, nombre, cantidad))
        popup.open()

    def confirmar_agregar_articulo(self, codigo, nombre, cantidad):
        execute_query("INSERT INTO articulos (codigo, nombre, cantidad) VALUES (%s, %s, %s)", (codigo, nombre, cantidad))
        self.ids.message.text = 'Artículo agregado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_articulos()

    def borrar_articulo(self):
        articulo = self.ids.articulos_spinner.text
        if not articulo:
            self.ids.message.text = 'Por favor, seleccione un artículo para borrar'
            return
        
        execute_query("DELETE FROM articulos WHERE nombre = %s", (articulo,))
        self.ids.message.text = 'Artículo borrado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_articulos()

    def on_codigo_enter(self):
        self.ids.nombre.focus = True

    def on_nombre_enter(self):
        self.ids.cantidad.focus = True

    def on_cantidad_enter(self):
        self.agregar_articulo()

    def limpiar_campos(self):
        self.ids.codigo.text = ''
        self.ids.nombre.text = ''
        self.ids.cantidad.text = ''
        self.ids.articulos_spinner.text = ''

    def modificar_articulo(self):
        articulo = self.ids.articulos_spinner.text
        codigo = self.ids.codigo.text
        nombre = self.ids.nombre.text
        cantidad = self.ids.cantidad.text

        if not articulo or not codigo or not nombre or not cantidad:
            self.ids.message.text = 'Por favor, seleccione un artículo y complete todos los campos'
            return

        try:
            cantidad = int(cantidad)
        except ValueError:
            self.ids.message.text = 'La cantidad debe ser un número entero'
            return

        # Verificar si el nuevo código o nombre ya existe para otro artículo
        existente = fetch_data("SELECT * FROM articulos WHERE (codigo = %s OR nombre = %s) AND nombre != %s", (codigo, nombre, articulo))
        if existente:
            error_popup = ErrorPopup(message='Código o nombre ya existe para otro artículo')
            error_popup.open()
            return

        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_modificar_articulo(articulo, codigo, nombre, cantidad))
        popup.open()

    def confirmar_modificar_articulo(self, articulo_original, codigo, nombre, cantidad):
        execute_query("UPDATE articulos SET codigo = %s, nombre = %s, cantidad = %s WHERE nombre = %s", 
                      (codigo, nombre, cantidad, articulo_original))
        self.ids.message.text = 'Artículo modificado correctamente'
        self.limpiar_campos()
        self.actualizar_lista_articulos()

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
        existente = fetch_data("SELECT * FROM toners WHERE (codigo = %s OR nombre = %s) AND nombre != %s", (codigo, nombre, toner))
        if existente:
            error_popup = ErrorPopup(message='Código o nombre ya existe para otro toner')
            error_popup.open()
            return

        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_modificar_toner(toner, codigo, nombre, cantidad))
        popup.open()

    def confirmar_modificar_toner(self, toner_original, codigo, nombre, cantidad):
        execute_query("UPDATE toners SET codigo = %s, nombre = %s, cantidad = %s WHERE nombre = %s", 
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