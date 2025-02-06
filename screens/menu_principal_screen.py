from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from database import execute_query, fetch_data
from kivy.app import App
from kivy.core.window import Window
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import win32print
import win32ui
import tempfile
from kivymd.uix.list import MDList, OneLineIconListItem, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivymd.uix.card import MDCard
from kivy.animation import Animation

KV = '''
<NotificationItem>:
    IconLeftWidget:
        icon: 'alert-circle-outline'

<NotificationPanel>:
    orientation: 'vertical'
    size_hint: (0.4, 1)  # Ocupa el 40% del ancho de la pantalla
    pos_hint: {"right": 1, "top": 1}
    md_bg_color: app.theme_cls.bg_light
    elevation: 10
    
    MDLabel:
        text: "Notificaciones"
        font_style: "H6"
        size_hint_y: None
        height: "48dp"
        padding: "15dp", "10dp"
    
    ScrollView:
        MDList:
            id: notification_list

<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<MenuPrincipalScreen>:
    notification_panel: notification_panel

    MDFloatLayout:
        Image:
            source: app.resource_path('images/inicio.jpg')
            allow_stretch: True
            keep_ratio: False
            size_hint: 1, 1
            pos_hint: {"center_x": .5, "center_y": .5}
        
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint: 1, 1
            
            MDBoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.5
                md_bg_color: app.theme_cls.bg_dark
                padding: "8dp"
                spacing: "8dp"
                
                MDLabel:
                    text: f"Bienvenido {root.nombre_usuario}"
                    font_style: "H6"
                    size_hint_y: None
                    height: self.texture_size[1]
                
                ScrollView:
                    MDList:
                        MenuButton:
                            text: "Administración"
                            icon: "cog"
                            on_release: root.change_screen('admin')
                        
                        MenuButton:
                            text: "Agregar Artículo"
                            icon: "plus-circle"
                            on_release: root.change_screen('agregar_articulo')
                        
                        MenuButton:
                            text: "Ingresos Hardware"
                            icon: "database-import"
                            on_release: root.change_screen('ingresos')
                        
                        MenuButton:
                            text: "Egresos Hardware"
                            icon: "database-export"
                            on_release: root.change_screen('egresos')
                        
                        MenuButton:
                            text: "Consulta Stock Hardware"
                            icon: "clipboard-list"
                            on_release: root.change_screen('consulta_stock')
                        
                        MenuButton:
                            text: "Histórico Movimientos"
                            icon: "history"
                            on_release: root.change_screen('historico_movimientos')
                        
                        MenuButton:
                            text: "Agregar Toner"
                            icon: "printer"
                            on_release: root.change_screen('agregar_toner')
                        
                        MenuButton:
                            text: "Ingresos Toner"
                            icon: "inbox-arrow-down"
                            on_release: root.change_screen('ingresos_toner')
                        
                        MenuButton:
                            text: "Egresos Toner"
                            icon: "inbox-arrow-up"
                            on_release: root.change_screen('egresos_toner')
                        
                        MenuButton:
                            text: "Consulta Toner"
                            icon: "magnify"
                            on_release: root.change_screen('consulta_toner')
                        
                        MenuButton:
                            text: "Histórico Movimientos Toner"
                            icon: "history"
                            on_release: root.change_screen('historico_movimientos_toner') 
                        
                        MenuButton:
                            text: "Reparaciones"
                            icon: "tools"
                            on_release: root.change_screen('reparaciones')
                        
                        MenuButton:
                            text: "Faltantes de stock"
                            icon: "alert-circle-outline"
                            on_release: root.show_faltantes()
                        
                        MenuButton:
                            text: "Cambiar Contraseña"
                            icon: "key-change"
                            on_release: root.cambiar_contrasena()
                        
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
                padding: "16dp"

        MDIconButton:
            icon: "bell-outline"
            pos_hint: {"right": 0.98, "top": 0.98}
            on_release: root.toggle_notification_panel()
            size_hint: None, None
            size: "48dp", "48dp"

        MDLabel:
            id: notification_count
            text: str(root.notification_count)
            pos_hint: {"right": 0.96, "top": 0.98}
            size_hint: None, None
            size: "20dp", "20dp"
            font_size: "12sp"
            theme_text_color: "Custom"
            text_color: 1, 0, 0, 1  # Red color for visibility

        NotificationPanel:
            id: notification_panel
            pos_hint: {"right": 1, "top": 0.9}
            opacity: 0
'''


class NotificationItem(OneLineIconListItem):
    pass

class NotificationPanel(MDCard):
    pass

class MenuPrincipalScreen(MDScreen):
    nombre_usuario = StringProperty("")
    notification_count = NumericProperty(0)
    notification_panel = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actualizar_nombre_usuario()
        Clock.schedule_once(self.check_low_stock, 0)

    def on_enter(self):
        self.actualizar_nombre_usuario()
        self.check_low_stock()

    def actualizar_nombre_usuario(self):
        usuario_actual = App.get_running_app().usuario_actual
        resultado = fetch_data("SELECT nombre FROM usuarios WHERE nombre_usuario = ?", (usuario_actual,))
        if resultado:
            self.nombre_usuario = resultado[0][0]
        else:
            self.nombre_usuario = usuario_actual

    def check_low_stock(self, *args):
        low_stock_threshold = 0  # cantidad minima
        low_stock_articles = fetch_data("SELECT codigo, nombre, cantidad FROM articulos WHERE cantidad <= ?", (low_stock_threshold,))
        low_stock_toners = fetch_data("SELECT codigo, nombre, cantidad FROM toners WHERE cantidad <= ?", (low_stock_threshold,))
        
        self.low_stock_items = low_stock_articles + low_stock_toners
        self.notification_count = len(self.low_stock_items)
        self.update_notification_panel()

    def update_notification_panel(self):
        notification_list = self.notification_panel.ids.notification_list
        notification_list.clear_widgets()
        
        if not self.low_stock_items:
            notification_list.add_widget(NotificationItem(text="No hay notificaciones de stock bajo."))
        else:
            for item in self.low_stock_items:
                notification_list.add_widget(NotificationItem(text=f"{item[1]} (Código: {item[0]}) - Stock: {item[2]}"))

    def toggle_notification_panel(self):
        if self.notification_panel.opacity == 0:
            self.notification_panel.opacity = 1
        else:
            self.notification_panel.opacity = 0
    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def show_error_message(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(300, 200))
        popup.open()

    def cambiar_contrasena(self):
        content = MDBoxLayout(orientation='vertical', spacing=5, padding=1)
        content.add_widget(MDLabel(text='Nueva contraseña:'))
        nueva_contrasena = TextInput(password=True, multiline=False)
        content.add_widget(nueva_contrasena)
        content.add_widget(MDLabel(text='Confirmar contraseña:'))
        confirmar_contrasena = TextInput(password=True, multiline=False)
        content.add_widget(confirmar_contrasena)

        def on_text_validate(instance):
            if instance == nueva_contrasena:
                confirmar_contrasena.focus = True
            elif instance == confirmar_contrasena:
                do_cambiar(None)

        nueva_contrasena.bind(on_text_validate=on_text_validate)
        confirmar_contrasena.bind(on_text_validate=on_text_validate)

        def do_cambiar(instance):
            if nueva_contrasena.text == confirmar_contrasena.text:
                usuario_actual = App.get_running_app().usuario_actual
                execute_query("UPDATE usuarios SET password = ? WHERE nombre_usuario = ?", (nueva_contrasena.text, usuario_actual))
                self.show_message('Contraseña cambiada correctamente')
                popup.dismiss()
            else:
                self.show_error_message('Las contraseñas no coinciden')

        buttons = MDBoxLayout(size_hint_y=None, height=48, spacing=10)
        btn_cancel = MDRectangleFlatIconButton(
            text='Cancelar',
            icon='close',
            on_release=lambda x: popup.dismiss(),
            size_hint_x=0.5
        )
        btn_change = MDRectangleFlatIconButton(
            text='Cambiar',
            icon='check',
            on_release=do_cambiar,
            size_hint_x=0.5
        )
        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_change)
        content.add_widget(buttons)

        popup = Popup(title="Cambiar contraseña", content=content, size_hint=(None, None), size=(400, 300))
        popup.open()

    def show_message(self, message):
        popup = Popup(title='Guardada correctamente', content=Label(text=message), size_hint=(None, None), size=(350, 300))
        popup.open()

    def logout(self):
        App.get_running_app().stop()
        Window.close()

    def show_faltantes(self):
        faltantes_articulos = fetch_data("SELECT codigo, nombre FROM articulos WHERE cantidad = 0")
        faltantes_toner = fetch_data("SELECT codigo, nombre FROM toners WHERE cantidad = 0")

        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        
        scroll_view = ScrollView(size_hint=(1, 1))
        md_list = MDList()

        md_list.add_widget(OneLineListItem(text="Hardware faltante:", theme_text_color="Custom", text_color=(1, 0.5, 0, 1)))  # Orange color for header
        for articulo in faltantes_articulos:
            md_list.add_widget(OneLineListItem(text=f"{articulo[0]} - {articulo[1]}"))
        
        md_list.add_widget(OneLineListItem(text="Toners faltantes:", theme_text_color="Custom", text_color=(1, 0.5, 0, 1)))  # Orange color for header
        for toner in faltantes_toner:
            md_list.add_widget(OneLineListItem(text=f"{toner[0]} - {toner[1]}"))

        scroll_view.add_widget(md_list)
        content.add_widget(scroll_view)

        button_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height="48dp", spacing=10, padding=[10, 10, 10, 10])
        guardar_pdf_button = MDRectangleFlatIconButton(
            text="Guardar como PDF",
            icon="file-pdf-box",
            on_release=lambda x: self.guardar_pdf_faltantes(faltantes_articulos, faltantes_toner),
            size_hint=(1, None),
            height="48dp"
        )
        button_layout.add_widget(guardar_pdf_button)

        content.add_widget(button_layout)

        popup = Popup(title="Hardware y Toners Faltantes", content=content, size_hint=(0.8, 0.8))
        popup.open()

    def guardar_pdf_faltantes(self, faltantes_articulos, faltantes_toner):
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        filename = os.path.join(desktop, "faltantes.pdf")

        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []

        data = [['Código', 'Nombre']]
        
        if faltantes_articulos:
            data.append(['Hardware faltante:'])
            data.extend([[articulo[0], articulo[1]] for articulo in faltantes_articulos])
        else:
            data.append(['No hay hardware faltante'])

        if faltantes_toner:
            data.append(['Toners faltantes:'])
            data.extend([[toner[0], toner[1]] for toner in faltantes_toner])
        else:
            data.append(['No hay toners faltantes'])

        table = Table(data)
        
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]

        for i, row in enumerate(data):
            if row[0] in ['Hardware faltante:', 'Toners faltantes:', 'No hay hardware faltante', 'No hay toners faltantes']:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.beige))
                style.append(('TEXTCOLOR', (0, i), (-1, i), colors.black))

        table.setStyle(TableStyle(style))

        elements.append(table)
        doc.build(elements)

        self.show_message(f"PDF guardado en el escritorio")

Builder.load_string(KV)