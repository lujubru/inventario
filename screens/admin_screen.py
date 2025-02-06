from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
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

<AdminScreen>:
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
                        text: "Agregar Usuario"
                        icon: "account-plus"
                        on_release: root.agregar_usuario()
                    
                    MenuButton:
                        text: "Modificar Usuario"
                        icon: "account-edit"
                        on_release: root.modificar_usuario()
                    
                    MenuButton:
                        text: "Eliminar Usuario"
                        icon: "account-remove"
                        on_release: root.eliminar_usuario()
                    
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
                title: "Administración de Usuarios"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: usuarios_spinner
                        hint_text: "Seleccionar usuario"
                        on_focus: if self.focus: root.menu.open()
                    
                    MDTextField:
                        id: nombre
                        hint_text: "Nombre completo"
                        on_text_validate: root.on_nombre_enter()
                        multiline: False
                    
                    MDTextField:
                        id: username
                        hint_text: "Nombre de usuario"
                        helper_text: "Solo para nuevos usuarios"
                        helper_text_mode: "on_focus"
                        on_text_validate: root.on_usuarios_enter()
                        multiline: False
                    
                    MDTextField:
                        id: mail
                        hint_text: "Correo electrónico"
                        on_text_validate: root.on_mail_enter()
                        multiline: False
                    
                    MDTextField:
                        id: password
                        hint_text: "Contraseña"
                        password: True
                        on_text_validate: root.on_contra_enter()
                        multiline: False
                    
                    MDLabel:
                        text: "Permisos:"
                        font_style: "H6"
                    
                    MDGridLayout:
                        cols: 2
                        adaptive_height: True
                        
                        MDCheckbox:
                            id: permiso_ingresos
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Ingresos"
                        
                        MDCheckbox:
                            id: permiso_egresos
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Egresos"
                        
                        MDCheckbox:
                            id: permiso_consulta_stock
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Consulta Stock"
                        
                        MDCheckbox:
                            id: permiso_historico_movimientos
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Histórico Movimientos"
                        
                        MDCheckbox:
                            id: permiso_admin_screen
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Acceso a administración"
                        
                        MDCheckbox:
                            id: permiso_agregar_articulos
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Agregar Artículos"
                        
                        MDCheckbox:
                            id: permiso_agregar_toner
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Agregar Toner"
                        
                        MDCheckbox:
                            id: permiso_ingresos_toner
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Ingresos Toner"
                        
                        MDCheckbox:
                            id: permiso_egresos_toner
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Egresos Toner"
                        
                        MDCheckbox:
                            id: permiso_consulta_toner
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Consulta Toner"
                        
                        MDCheckbox:
                            id: permiso_historico_movimientos_toner
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Histórico Movimientos Toner"
                        
                        MDCheckbox:
                            id: permiso_reparaciones
                            size_hint: None, None
                            size: "24dp", "24dp"
                        MDLabel:
                            text: "Reparaciones"
                    
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

class AdminScreen(MDScreen):
    permisos_opciones = ListProperty(['admin', 'usuario', 'invitado'])
    permisos_detallados = ListProperty(['ingresos', 'egresos', 'consulta_stock', 'historico_movimientos', 'agregar_articulos', 'admin_screen',
                                        'agregar_toner', 'ingresos_toner', 'egresos_toner', 'consulta_toner', 'historico_movimientos_toner', 'reparaciones'])
    usuarios_spinner = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.menu = None

    def on_enter(self):
        super().on_enter()
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_usuarios()

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if permisos and permisos[0][0]:
            permisos_lista = permisos[0][0].split(',')
            if 'admin_screen' in permisos_lista:
                return  # El usuario tiene permisos, no hacemos nada
        
        # Si llegamos aquí, el usuario no tiene permisos
        error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de administración')
        error_popup.bind(on_dismiss=self.return_to_menu)
        error_popup.open()

    def actualizar_lista_usuarios(self):
        usuarios = fetch_data("SELECT nombre_usuario FROM usuarios")
        menu_items = []
        for user in usuarios:
            username = user[0] if user[0] else "Usuario sin nombre"
            if isinstance(username, str) and username.strip():  # Verificar que sea una cadena no vacía
                menu_items.append({
                    "text": username,
                    "viewclass": "OneLineListItem",
                    "on_release": lambda x=username: self.seleccionar_usuario(x),
                })
        
        if not menu_items:
            menu_items.append({
                "text": "No hay usuarios",
                "viewclass": "OneLineListItem",
                "on_release": lambda x: None,
            })

        self.menu = MDDropdownMenu(
            caller=self.ids.usuarios_spinner,
            items=menu_items,
            width_mult=4,
        )

    def seleccionar_usuario(self, usuario):
        if usuario and usuario != "No hay usuarios":
            self.ids.usuarios_spinner.text = usuario
            self.cargar_datos_usuario(usuario)
        else:
            self.ids.usuarios_spinner.text = ""
            self.limpiar_campos()
        self.menu.dismiss()

    def agregar_usuario(self):
        username = self.ids.username.text.strip()
        nombre = self.ids.nombre.text.strip()
        mail = self.ids.mail.text.strip()
        password = self.ids.password.text
        
        if not username or not nombre or not mail or not password:
            self.ids.message.text = 'Todos los campos son obligatorios'
            return

        permisos = ','.join([p for p in self.permisos_detallados if self.ids[f'permiso_{p}'].active])
        try:
            execute_query("INSERT INTO usuarios (nombre_usuario, password, permisos, nombre, mail) VALUES (?, ?, ?, ?, ?)", 
                          (username, password, permisos, nombre, mail))
            self.ids.message.text = 'Usuario agregado correctamente'
            self.limpiar_campos()
            self.actualizar_lista_usuarios()
        except Exception as e:
            self.ids.message.text = f'Error al agregar usuario: {str(e)}'

    def modificar_usuario(self):
        username = self.ids.usuarios_spinner.text.strip()
        nombre = self.ids.nombre.text.strip()
        mail = self.ids.mail.text.strip()
        password = self.ids.password.text
        
        if not username or not nombre or not mail:
            self.ids.message.text = 'Nombre de usuario, nombre y correo son obligatorios'
            return

        permisos = ','.join([p for p in self.permisos_detallados if self.ids[f'permiso_{p}'].active])
        try:
            if password:
                execute_query("UPDATE usuarios SET password = ?, permisos = ?, nombre = ?, mail = ? WHERE nombre_usuario = ?", 
                              (password, permisos, nombre, mail, username))
            else:
                execute_query("UPDATE usuarios SET permisos = ?, nombre = ?, mail = ? WHERE nombre_usuario = ?", 
                              (permisos, nombre, mail, username))
            self.ids.message.text = 'Usuario modificado correctamente'
            self.limpiar_campos()
            self.actualizar_lista_usuarios()
        except Exception as e:
            self.ids.message.text = f'Error al modificar usuario: {str(e)}'

    def eliminar_usuario(self):
        username = self.ids.usuarios_spinner.text.strip()
        if not username:
            self.ids.message.text = 'Selecciona un usuario para eliminar'
            return

        try:
            execute_query("DELETE FROM usuarios WHERE nombre_usuario = ?", (username,))
            self.ids.message.text = 'Usuario eliminado correctamente'
            self.limpiar_campos()
            self.actualizar_lista_usuarios()
        except Exception as e:
            self.ids.message.text = f'Error al eliminar usuario: {str(e)}'

    def cargar_datos_usuario(self, usuario):
        datos = fetch_data("SELECT password, permisos, nombre, mail FROM usuarios WHERE nombre_usuario = ?", (usuario,))
        if datos:
            self.ids.password.text = datos[0][0]
            self.ids.nombre.text = datos[0][2] if datos[0][2] else ""
            self.ids.mail.text = datos[0][3] if datos[0][3] else ""
            permisos = datos[0][1].split(',') if datos[0][1] else []
            for p in self.permisos_detallados:
                self.ids[f'permiso_{p}'].active = p in permisos

    def limpiar_campos(self):
        self.ids.username.text = ''
        self.ids.nombre.text = ''
        self.ids.mail.text = ''
        self.ids.password.text = ''
        self.ids.usuarios_spinner.text = ''
        for p in self.permisos_detallados:
            self.ids[f'permiso_{p}'].active = False
        self.ids.message.text = ''

    def on_nombre_enter(self):
        self.ids.username.focus = True

    def on_usuarios_enter(self):
        self.ids.mail.focus = True

    def on_mail_enter(self):
        self.ids.password.focus = True

    def on_contra_enter(self):
        self.agregar_usuario()
            
    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def logout(self):
        App.get_running_app().stop()
        Window.close()

    def volver_menu_principal(self):
        self.manager.current = 'menu_principal'

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

Builder.load_string(KV)