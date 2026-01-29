from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget

from storage import Storage


KV = """
ScreenManager:
    LoginScreen:
    RegisterScreen:
    TasksScreen:

<LoginScreen>:
    name: "login"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(12)

        MDLabel:
            text: "Login"
            halign: "center"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1] + dp(12)

        MDTextField:
            id: user
            hint_text: "Usuário"
            mode: "rectangle"

        MDTextField:
            id: pwd
            hint_text: "Senha"
            password: True
            mode: "rectangle"

        MDRaisedButton:
            text: "Entrar"
            pos_hint: {"center_x": 0.5}
            on_release: app.do_login()

        MDFlatButton:
            text: "Criar cadastro"
            pos_hint: {"center_x": 0.5}
            on_release: app.go("register")

<RegisterScreen>:
    name: "register"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(12)

        MDLabel:
            text: "Cadastro"
            halign: "center"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1] + dp(12)

        MDTextField:
            id: user
            hint_text: "Novo usuário"
            mode: "rectangle"

        MDTextField:
            id: pwd
            hint_text: "Senha"
            password: True
            mode: "rectangle"

        MDTextField:
            id: pwd2
            hint_text: "Confirmar senha"
            password: True
            mode: "rectangle"

        MDRaisedButton:
            text: "Criar conta"
            pos_hint: {"center_x": 0.5}
            on_release: app.do_register()

        MDFlatButton:
            text: "Voltar"
            pos_hint: {"center_x": 0.5}
            on_release: app.go("login")

<TasksScreen>:
    name: "tasks"
    MDBoxLayout:
        orientation: "vertical"

        MDToolbar:
            title: "Tarefas"
            left_action_items: [["logout", lambda x: app.logout()]]
            right_action_items: [["broom", lambda x: app.clear_all()]]

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(10)

            MDTextField:
                id: text
                hint_text: "Descrição da tarefa"
                mode: "rectangle"

            MDBoxLayout:
                spacing: dp(10)
                size_hint_y: None
                height: dp(56)

                MDTextField:
                    id: date
                    hint_text: "DD/MM/AAAA"
                    mode: "rectangle"

                MDTextField:
                    id: time
                    hint_text: "HH:MM"
                    mode: "rectangle"

            MDRaisedButton:
                text: "Adicionar"
                pos_hint: {"center_x": 0.5}
                on_release: app.add_task()

        ScrollView:
            MDList:
                id: list
"""


class LoginScreen: pass
class RegisterScreen: pass
class TasksScreen: pass


class TodoAndroidApp(MDApp):
    def build(self):
        self.title = "TodoApp"
        try:
            Window.size = (420, 760)
        except Exception:
            pass

        self.sm = Builder.load_string(KV)
        self.user = None
        self.store = Storage(self.user_data_dir)
        return self.sm

    def snack(self, msg: str):
        Snackbar(text=msg).open()

    def go(self, screen: str):
        self.sm.current = screen

    # ---------- AUTH ----------
    def do_login(self):
        s = self.sm.get_screen("login")
        u = (s.ids.user.text or "").strip()
        p = s.ids.pwd.text or ""
        ok, msg = self.store.login(u, p)
        if not ok:
            self.snack(msg)
            return
        self.user = u
        self.go("tasks")
        self.refresh_tasks()

    def do_register(self):
        s = self.sm.get_screen("register")
        u = (s.ids.user.text or "").strip()
        p1 = s.ids.pwd.text or ""
        p2 = s.ids.pwd2.text or ""
        if p1 != p2:
            self.snack("As senhas não conferem.")
            return
        ok, msg = self.store.register(u, p1)
        self.snack(msg)
        if ok:
            self.go("login")

    def logout(self):
        self.user = None
        self.go("login")

    # ---------- TASKS ----------
    def refresh_tasks(self):
        if not self.user:
            return
        s = self.sm.get_screen("tasks")
        s.ids.list.clear_widgets()

        tasks = self.store.list_tasks(self.user)

        for t in tasks:
            done = bool(t.get("done"))
            item = TwoLineAvatarIconListItem(
                text=t.get("texto", ""),
                secondary_text=f'{t.get("data","")} {t.get("hora","")}'.strip()
            )

            item.add_widget(
                IconLeftWidget(icon="checkbox-marked" if done else "checkbox-blank-outline")
            )

            del_btn = IconRightWidget(icon="delete")
            del_btn.on_release = (lambda task_id=t["id"]: self.delete_task(task_id))
            item.add_widget(del_btn)

            item.on_release = (lambda task=t: self.toggle_done(task))
            s.ids.list.add_widget(item)

    def add_task(self):
        if not self.user:
            return
        s = self.sm.get_screen("tasks")
        texto = s.ids.text.text or ""
        data = s.ids.date.text or ""
        hora = s.ids.time.text or ""

        ok, msg = self.store.add_task(self.user, texto, data, hora)
        self.snack(msg)
        if ok:
            s.ids.text.text = ""
            # mantém data, limpa hora (opcional)
            s.ids.time.text = ""
            self.refresh_tasks()

    def toggle_done(self, task: dict):
        self.store.toggle_done(self.user, int(task["id"]), not bool(task.get("done")))
        self.refresh_tasks()

    def delete_task(self, task_id: int):
        self.store.delete_task(self.user, int(task_id))
        self.refresh_tasks()

    def clear_all(self):
        if not self.user:
            return
        self.store.clear_all(self.user)
        self.refresh_tasks()
        self.snack("Tarefas limpas.")


if __name__ == "__main__":
    TodoAndroidApp().run()
