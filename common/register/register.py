from kivy.uix.screenmanager import Screen


class RegisterScreen(Screen):
    def on_enter(self):
        self.ids.username_input.text = ""
        self.ids.email_input.text = ""
        self.ids.phone_input.text = ""
        self.ids.password_input.text = ""
        self.ids.confirm_input.text = ""
        self.ids.error_label.text = ""
