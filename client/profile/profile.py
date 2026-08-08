from kivy.app import App
from kivy.uix.screenmanager import Screen


class ProfileScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        profile = app.db.users.get_profile(app.user_id)

        self.ids.username_label.text = f"Signed in as {profile['username']}"
        self.ids.name_input.text = profile["name"] or ""
        self.ids.msg_label.text = ""
