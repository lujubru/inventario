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
from kivymd.uix.list import MDList, TwoLineListItem
from kivy.uix.scrollview import ScrollView
import os
import csv
from datetime import datetime

KV = '''
<MenuButton@MDRectangleFlatIconButton>:
    size_hint: 1, None
    height: "48dp"

<ReparacionesScreen>:
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
                        text: "Agregar Reparación"
                        icon: "plus-circle"
                        on_release: root.agregar_reparacion()
                    
                    MenuButton:
                        text: "Modificar Reparación"
                        icon: "pencil"
                        on_release: root.modificar_reparacion()
                    
                    MenuButton:
                        text: "Ver Reparaciones en Curso"
                        icon: "eye"
                        on_release: root.ver_reparaciones()
                    
                    MenuButton:
                        text: "Histórico de Reparaciones"
                        icon: "history"
                        on_release: root.ver_historico_reparaciones()
                    
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
                title: "Reparaciones"
                elevation: 4
            
            ScrollView:
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    adaptive_height: True
                    
                    MDTextField:
                        id: modelos_spinner
                        hint_text: "Seleccionar modelo"
                        on_focus: if self.focus: root.menu_modelos.open()
                    
                    MDTextField:
                        id: tipo
                        hint_text: "Tipo"
                        on_text_validate: root.on_tipo_enter()
                    
                    MDTextField:
                        id: modelo
                        hint_text: "Modelo"
                        on_text_validate: root.on_modelo_enter()
                    
                    MDTextField:
                        id: sn
                        hint_text: "SN"
                        on_text_validate: root.on_sn_enter()
                    
                    MDTextField:
                        id: motivo
                        hint_text: "Motivo"
                        on_text_validate: root.on_motivo_enter()
                    
                    MDTextField:
                        id: estado_reparacion
                        hint_text: "Estado de reparación"
                    
                    MDTextField:
                        id: estado_actual
                        hint_text: "Estado actual"
                        on_focus: if self.focus: root.menu_estado.open()
                    
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
        content.add_widget(MDLabel(text='¿Está seguro de que desea realizar esta acción?'))
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

class ReparacionesListPopup(Popup):
    def __init__(self, reparaciones, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Lista de Reparaciones en Curso'
        self.size_hint = (0.9, 0.9)
        self.reparaciones = reparaciones
        content = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        
        scroll = ScrollView()
        list_view = MDList()
        
        for reparacion in reparaciones:
            item = TwoLineListItem(
                text=f"{reparacion[2]} - {reparacion[3]} - SN: {reparacion[4]}",
                secondary_text=f"Motivo: {reparacion[5][:30]}... | Estado: {reparacion[6]} | Actual: {reparacion[8]}"
            )
            list_view.add_widget(item)
        
        scroll.add_widget(list_view)
        content.add_widget(scroll)
        
        button_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        close_button = Button(text='Cerrar')
        close_button.bind(on_press=self.dismiss)
        save_button = Button(text='Guardar')
        save_button.bind(on_press=self.save_to_file)
        button_layout.add_widget(close_button)
        button_layout.add_widget(save_button)
        content.add_widget(button_layout)
        
        self.content = content

    def save_to_file(self, instance):
        documents_path = os.path.expanduser('~/Documents')
        filename = f'reparaciones_en_curso_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(documents_path, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Tipo', 'Modelo', 'SN', 'Motivo', 'Estado de Reparación', 'Fecha', 'Estado Actual'])
            for reparacion in self.reparaciones:
                writer.writerow(reparacion[1:])  # Excluimos el primer campo (id de la base de datos)
        
        self.show_save_confirmation(filepath)

    def show_save_confirmation(self, filepath):
        popup = Popup(title='Guardado Exitoso',
                      content=Label(text=f'El archivo se ha guardado en:\n{filepath}'),
                      size_hint=(0.6, 0.4))
        popup.open()

class HistoricoReparacionesPopup(Popup):
    def __init__(self, sn, **kwargs):
        super().__init__(**kwargs)
        self.title = f'Histórico de Reparaciones - SN: {sn}'
        self.size_hint = (0.9, 0.9)
        content = MDBoxLayout(orientation='vertical', padding=10, spacing=10)
        
        scroll = ScrollView()
        list_view = MDList()
        
        reparaciones = fetch_data("SELECT * FROM reparaciones WHERE sn = %s ORDER BY fecha DESC", (sn,))
        for reparacion in reparaciones:
            item = TwoLineListItem(
                text=f"{reparacion[2]} - {reparacion[3]} - Fecha: {reparacion[7]}",
                secondary_text=f"Motivo: {reparacion[5][:30]}... | Estado: {reparacion[6]} | Actual: {reparacion[8]}"
            )
            list_view.add_widget(item)
        
        scroll.add_widget(list_view)
        content.add_widget(scroll)
        
        close_button = Button(text='Cerrar', size_hint=(1, 0.1))
        close_button.bind(on_press=self.dismiss)
        content.add_widget(close_button)
        
        self.content = content

class ReparacionesScreen(MDScreen):
    modelos = ListProperty([])
    menu_modelos = ObjectProperty(None)
    menu_estado = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.estados = ["Reparado", "En reparación"]

    def on_enter(self):
        Clock.schedule_once(self.check_permissions, 0)
        self.actualizar_lista_modelos()
        self.crear_menu_estado()

    def check_permissions(self, dt):
        usuario_actual = self.app.usuario_actual
        permisos = fetch_data("SELECT permisos FROM usuarios WHERE nombre_usuario = %s", (usuario_actual,))
        if permisos and permisos[0][0]:
            permisos_lista = permisos[0][0].split(',')
            if 'reparaciones' in permisos_lista:
                return  # El usuario tiene permisos, no hacemos nada
        
        # Si llegamos aquí, el usuario no tiene permisos
        error_popup = ErrorPopup(message='No tienes permiso para acceder a la pantalla de reparaciones')
        error_popup.bind(on_dismiss=self.return_to_menu)
        error_popup.open()

    def return_to_menu(self, instance):
        self.manager.current = 'menu_principal'

    def actualizar_lista_modelos(self):
        modelos = fetch_data("SELECT DISTINCT modelo FROM reparaciones WHERE estado_actual != 'Reparado'")
        menu_items = [
            {
                "text": modelo[0],
                "viewclass": "OneLineListItem",
                "on_release": lambda x=modelo[0]: self.seleccionar_modelo(x),
            } for modelo in modelos
        ]
        self.menu_modelos = MDDropdownMenu(
            caller=self.ids.modelos_spinner,
            items=menu_items,
            width_mult=4,
        )

    def crear_menu_estado(self):
        menu_items = [
            {
                "text": estado,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=estado: self.seleccionar_estado(x),
            } for estado in self.estados
        ]
        self.menu_estado = MDDropdownMenu(
            caller=self.ids.estado_actual,
            items=menu_items,
            width_mult=4,
        )

    def seleccionar_modelo(self, modelo):
        self.ids.modelos_spinner.text = modelo
        self.cargar_datos_modelo(modelo)
        self.menu_modelos.dismiss()

    def seleccionar_estado(self, estado):
        self.ids.estado_actual.text = estado
        self.menu_estado.dismiss()

    def cargar_datos_modelo(self, modelo):
        datos = fetch_data("SELECT tipo, modelo, sn, motivo, estado, estado_actual FROM reparaciones WHERE modelo = %s ORDER BY id DESC LIMIT 1", (modelo,))
        if datos:
            self.ids.tipo.text = datos[0][0] or ""
            self.ids.modelo.text = datos[0][1] or ""
            self.ids.sn.text = datos[0][2] or ""
            self.ids.motivo.text = datos[0][3] or ""
            self.ids.estado_reparacion.text = datos[0][4] or ""
            self.ids.estado_actual.text = datos[0][5] or ""
        else:
            self.limpiar_campos()

    def agregar_reparacion(self):
        tipo = self.ids.tipo.text
        modelo = self.ids.modelo.text
        sn = self.ids.sn.text
        motivo = self.ids.motivo.text
        estado_reparacion = self.ids.estado_reparacion.text
        estado_actual = self.ids.estado_actual.text

        if not tipo or not modelo or not sn or not motivo or not estado_reparacion or not estado_actual:
            self.ids.message.text = 'Por favor, complete todos los campos'
            return

        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_agregar_reparacion(tipo, modelo, sn, motivo, estado_reparacion, estado_actual))
        popup.open()

    def confirmar_agregar_reparacion(self, tipo, modelo, sn, motivo, estado_reparacion, estado_actual):
        execute_query(
            "INSERT INTO reparaciones (tipo, modelo, sn, motivo, estado, estado_actual, fecha) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
            (tipo, modelo, sn, motivo, estado_reparacion, estado_actual)
        )
        self.ids.message.text = 'Reparación agregada correctamente'
        self.limpiar_campos()
        self.actualizar_lista_modelos()

        
    def modificar_reparacion(self):
        modelo = self.ids.modelos_spinner.text
        tipo = self.ids.tipo.text
        sn = self.ids.sn.text
        motivo = self.ids.motivo.text
        estado_reparacion = self.ids.estado_reparacion.text
        estado_actual = self.ids.estado_actual.text

        if not modelo or not tipo or not sn or not motivo or not estado_reparacion or not estado_actual:
            self.ids.message.text = 'Por favor, seleccione un modelo y complete todos los campos'
            return

        popup = ConfirmacionPopup(confirmar_callback=lambda: self.confirmar_modificar_reparacion(modelo, tipo, sn, motivo, estado_reparacion, estado_actual))
        popup.open()

    def confirmar_modificar_reparacion(self, modelo, tipo, sn, motivo, estado_reparacion, estado_actual):
        execute_query(
            """
            UPDATE reparaciones 
            SET tipo = %s, sn = %s, motivo = %s, estado = %s, estado_actual = %s 
            WHERE modelo = %s
            """, 
            (tipo, sn, motivo, estado_reparacion, estado_actual, modelo)
        )
        self.ids.message.text = 'Reparación modificada correctamente'
        self.limpiar_campos()
        self.actualizar_lista_modelos()

    def ver_reparaciones(self):
        reparaciones = fetch_data(
            """
            SELECT * FROM reparaciones 
            WHERE estado_actual != 'Reparado' 
            ORDER BY id DESC
            """
        )
        popup = ReparacionesListPopup(reparaciones)
        popup.open()

    def ver_historico_reparaciones(self):
        sn = self.ids.sn.text
        if not sn:
            self.ids.message.text = 'Por favor, ingrese un número de serie (SN)'
            return
        popup = HistoricoReparacionesPopup(sn)
        popup.open()

    def on_tipo_enter(self):
        self.ids.modelo.focus = True

    def on_modelo_enter(self):
        self.ids.sn.focus = True

    def on_sn_enter(self):
        self.ids.motivo.focus = True

    def on_motivo_enter(self):
        self.ids.estado_reparacion.focus = True

    def limpiar_campos(self):
        self.ids.tipo.text = ''
        self.ids.modelo.text = ''
        self.ids.sn.text = ''
        self.ids.motivo.text = ''
        self.ids.estado_reparacion.text = ''
        self.ids.estado_actual.text = ''
        self.ids.modelos_spinner.text = ''

    def volver_menu_principal(self):
        self.manager.current = 'menu_principal'

    def change_screen(self, screen_name):
        self.manager.current = screen_name

    def logout(self):
        App.get_running_app().stop()
        Window.close()

Builder.load_string(KV)