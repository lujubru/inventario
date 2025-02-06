from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import StringProperty
from screens.login_screen import LoginScreen
from screens.menu_principal_screen import MenuPrincipalScreen
from screens.admin_screen import AdminScreen
from screens.agregar_articulo_screen import AgregarArticuloScreen
from screens.ingresos_screen import IngresosScreen
from screens.egresos_screen import EgresosScreen
from screens.consulta_stock_screen import ConsultaStockScreen
from screens.historico_movimientos_screen import HistoricoMovimientosScreen
from screens.historico_movimientos_toner_screen import HistoricoMovimientosTonerScreen
from screens.agregar_toner_screen import AgregarTonerScreen
from screens.ingresos_toner_screen import IngresosTonerScreen
from screens.egresos_toner_screen import EgresosTonerScreen
from screens.consulta_toner_screen import ConsultaTonerScreen
from screens.reparaciones_screen import ReparacionesScreen
from screens.loading_screen import LoadingScreen
from kivymd.app import MDApp
from kivy.config import Config
import os
import sys

def ruta_recurso(ruta_relativa):

    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, ruta_relativa)

# Obtener la ruta del directorio actual
directorio_actual = os.path.dirname(os.path.abspath(__file__))

# Cargar todos los archivos .kv
kv_directory = ruta_recurso('kv')
if os.path.exists(kv_directory):
    for archivo_kv in os.listdir(kv_directory):
        if archivo_kv.endswith('.kv'):
            Builder.load_file(os.path.join(kv_directory, archivo_kv))
else:
    print(f"El directorio 'kv' no existe en la ruta: {kv_directory}")

class InventarioApp(MDApp):
    usuario_actual = StringProperty('')

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        icon_path = ruta_recurso('images/icon.png')
        if os.path.exists(icon_path):
            self.icon = icon_path
        else:
            print(f"El archivo de icono no existe en la ruta: {icon_path}")

        # Configuración para guardar el nombre de usuario
        self.config = Config
        self.config.setdefaults('User', {'username': ''})

        self.sm = ScreenManager()
        self.sm.add_widget(LoadingScreen(name='loading'))
        self.sm.current = 'loading'
        
        return self.sm

    def load_main_app(self):
        # Agregar todas las pantallas
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(MenuPrincipalScreen(name='menu_principal'))
        self.sm.add_widget(AdminScreen(name='admin'))
        self.sm.add_widget(AgregarArticuloScreen(name='agregar_articulo'))
        self.sm.add_widget(IngresosScreen(name='ingresos'))
        self.sm.add_widget(EgresosScreen(name='egresos'))
        self.sm.add_widget(ConsultaStockScreen(name='consulta_stock'))
        self.sm.add_widget(HistoricoMovimientosScreen(name='historico_movimientos'))
        self.sm.add_widget(HistoricoMovimientosTonerScreen(name='historico_movimientos_toner'))
        self.sm.add_widget(AgregarTonerScreen(name='agregar_toner'))
        self.sm.add_widget(IngresosTonerScreen(name='ingresos_toner'))
        self.sm.add_widget(EgresosTonerScreen(name='egresos_toner'))
        self.sm.add_widget(ConsultaTonerScreen(name='consulta_toner'))
        self.sm.add_widget(ReparacionesScreen(name='reparaciones'))

        # Verificar si se pasó un nombre de pantalla como argumento
        if len(sys.argv) > 1:
            pantalla_inicial = sys.argv[1]
            if pantalla_inicial in self.sm.screen_names:
                self.sm.current = pantalla_inicial
            else:
                print(f"Pantalla '{pantalla_inicial}' no encontrada. Iniciando en la pantalla de login.")
                self.sm.current = 'login'
        else:
            self.sm.current = 'login'

    def establecer_usuario_actual(self, usuario):
        self.usuario_actual = usuario

    def resource_path(self, ruta_relativa):
        return ruta_recurso(ruta_relativa)

    def get_application_config(self):
        return super(InventarioApp, self).get_application_config('~/.inventarioapp/config.ini')

if __name__ == '__main__':
    InventarioApp().run()