from kivy.uix.screenmanager import Screen
from database import fetch_data
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder

# Definición del diseño de la interfaz de usuario en KV
kv_string = '''
<LoginScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)

        Image:
            source: app.resource_path('images/logo.png')
            size_hint: None, None
            size: dp(900), dp(260)
            pos_hint: {'center_x': 0.5}

        MDTextField:
            id: username_input
            hint_text: "Usuario"
            icon_right: "account"
            multiline: False
            on_text_validate: password_input.focus = True
            size_hint_x: None
            width: "300dp"
            font_size: "18sp"
            pos_hint: {"center_x": .5}

        MDTextField:
            id: password_input
            hint_text: "Contraseña"
            multiline: False
            on_text_validate: root.login()
            icon_right: "eye-off"
            size_hint_x: None
            width: "300dp"
            font_size: "18sp"
            pos_hint: {"center_x": .5}
            password: True

        MDBoxLayout:
            size_hint_x: None
            width: "300dp"
            pos_hint: {"center_x": .5}

            MDCheckbox:
                id: remember_username
                size_hint: None, None
                size: "48dp", "5dp"
                on_active: root.toggle_remember_username(*args)

            MDLabel:
                text: "Recordar usuario"
                font_size: "14sp"

        MDRaisedButton:
            text: "Iniciar Sesión"
            font_size: "18sp"
            pos_hint: {"center_x": .5}
            on_release: root.login()

        MDLabel:
            id: error_label
            text: ""
            theme_text_color: "Error"
            halign: "center"
            font_style: "Caption"

        MDRaisedButton:
            text: "Salir"
            font_size: "18sp"
            pos_hint: {"center_x": .5}
            on_release: root.salir_aplicacion()
'''

# Cargar el diseño KV
Builder.load_string(kv_string)

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(on_enter=self.set_focus)

    def set_focus(self, instance):
        Clock.schedule_once(self._set_focus, 0.1)

    def _set_focus(self, dt):
        if 'username_input' in self.ids:
            self.ids.username_input.focus = True
        else:
            print("Error: No se encontró el campo de usuario")

    def on_enter(self):
        self.load_saved_username()

    def load_saved_username(self):
        saved_username = App.get_running_app().config.get('User', 'username')
        if saved_username:
            self.ids.username_input.text = saved_username
            self.ids.remember_username.active = True

    def toggle_remember_username(self, checkbox, value):
        if not value:
            App.get_running_app().config.set('User', 'username', '')
            App.get_running_app().config.write()

    def login(self):
        username = self.ids.username_input.text
        password = self.ids.password_input.text
        user = fetch_data("SELECT * FROM usuarios WHERE (nombre_usuario = ? OR mail = ?) AND password = ?", (username, username, password))
        if user:
            if self.ids.remember_username.active:
                App.get_running_app().config.set('User', 'username', username)
            else:
                App.get_running_app().config.set('User', 'username', '')
            App.get_running_app().config.write()
            
            App.get_running_app().establecer_usuario_actual(user[0][1])  # Usar nombre_usuario
            self.clear_fields()
            self.manager.current = 'menu_principal'
        else:
            self.ids.error_label.text = 'Usuario o contraseña incorrectos'

    def clear_fields(self):
        self.ids.password_input.text = ''
        self.ids.error_label.text = ''
        if not self.ids.remember_username.active:
            self.ids.username_input.text = ''

    def salir_aplicacion(self):
        App.get_running_app().stop()
        Window.close()

    def on_leave(self):
        self.clear_fields()