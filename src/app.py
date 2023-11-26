from textual.app import App
from widgets import MainMenu


class TelegodsClientApp(App):
    BINDINGS = [
        ("ctrl+d", "toggle_dark_mode", "Toggle dark mode"),
        ("ctrl+c", "exit", "Exit"),
    ]
    CSS_PATH = "app.css"
    SCREENS = {
        "main-menu": MainMenu(),
    }

    def on_mount(self) -> None:
        self.title = "TeleGods Client"
        self.sub_title = "version 0.1.0"
        self.push_screen("main-menu")

    def action_toggle_dark_mode(self):
        self.dark = not self.dark

    def action_exit(self):
        self.app.exit()


if __name__ == "__main__":
    TelegodsClientApp().run()
