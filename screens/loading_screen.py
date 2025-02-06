from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp

Builder.load_string('''
<LoadingScreen>:
    FloatLayout:
        AsyncImage:
            source: app.resource_path('images/logo.png')  # Asegúrate de tener esta imagen
            allow_stretch: False
            keep_ratio: True
        # Image:
        #     source: app.resource_path('images/logo.png')  # Asegúrate de tener esta imagen
        #     size_hint: None, None
        #     size: "100dp", "100dp"
        #     pos_hint: {'center_x': 0.5, 'center_y': 0.6}
        MDSpinner:
            size_hint: None, None
            size: dp(46), dp(46)
            pos_hint: {'center_x': 0.5, 'center_y': 0.4}
            active: True
        MDLabel:
            text: "Cargando..."
            halign: "center"
            pos_hint: {'center_x': 0.5, 'center_y': 0.3}
            color: (0,0,0,1)
            font_style: "H5"
''')

class LoadingScreen(Screen):
    def on_enter(self):
        # Simula un tiempo de carga (puedes ajustar esto según tus necesidades)
        Clock.schedule_once(self.load_main_app, 2)

    def load_main_app(self, dt):
        app = MDApp.get_running_app()
        app.load_main_app()