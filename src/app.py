from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Input, Static

from client import Client


class MainMenu(Screen):
    TEXT = "Welcome to TeleGods Client, please select a service ;D"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Horizontal(
                Button(
                    label="TeleBank",
                    variant="primary",
                    id="bank",
                    classes="large-button",
                ),
                Button(
                    label="TeleLiquor Store",
                    variant="warning",
                    id="liquor-store",
                    classes="large-button",
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        # Button ID
        if button_id is None:
            print("error")
        self.app.push_screen(f"{button_id}-server-connection")


class BankServerConnection(Screen):
    server = "bank"
    ip = "127.0.0.1"
    port = "8888"
    server_name = "bank" if server == "bank" else "liquor store"
    TEXT = f"Please enter the IP address and port of the {server_name} that you're trying to connect..."
    ERROR128_TEXT = "The IP address you entered is invalid"
    ERROR129_TEXT = "The port you entered is invalid"
    TIMEOUT_SCREEN_ID = "bank-server-timeout"
    BANK_LOGIN_SCREEN_ID = "bank-login"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR128_TEXT, id="error128", classes="text error hidden"),
            Static(self.ERROR129_TEXT, id="error129", classes="text error hidden"),
            Horizontal(
                Input(
                    placeholder="IP Address (127.0.0.1)",
                    id=f"{self.server}-server-ip",
                    classes="ip-input",
                    restrict=r"[0-9.]*",
                    valid_empty=True,
                ),
                Input(
                    placeholder="Port (8888)",
                    id=f"{self.server}-server-port",
                    classes="port-input",
                    restrict=r"[0-9]*",
                    valid_empty=True,
                ),
                Button(
                    label="Connect",
                    variant="success",
                    id="connect",
                ),
                Button(label="Back", variant="error", id="back"),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def __update_error(self, error_code: int, id: str):
        dom = self.query_one(id)
        if error_code != 0 and dom.has_class("hidden"):
            dom.remove_class("hidden")
        elif error_code == 0 and not dom.has_class("hidden"):
            dom.add_class("hidden")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.has_class("ip-input"):
            self.ip = event.value
        elif event.input.has_class("port-input"):
            self.port = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            print("error")
        match button_id:
            case "back":
                self.app.pop_screen()
            case "connect":
                # Validate IP
                ip_error_code, _ = CLIENT.validate_ip(self.ip)
                self.__update_error(ip_error_code, "#error128")

                # Validate port
                port_error_code, _ = CLIENT.validate_port(self.port)
                self.__update_error(port_error_code, "#error129")

                if ip_error_code == 0 and port_error_code == 0:
                    connection_error_code, _ = CLIENT.bank_connect(self.ip, self.port)
                    if connection_error_code != 0:
                        self.app.push_screen(self.TIMEOUT_SCREEN_ID)
                        return
                    self.app.push_screen(self.BANK_LOGIN_SCREEN_ID)


class BankTimeout(Screen):
    server = "bank"
    server_name = "bank" if server == "bank" else "liquor store"
    ERROR130_TEXT = "Couldn't connect to the specified server, please check the address and try again..."

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.ERROR130_TEXT, classes="text error"),
            Horizontal(
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class BankLogin(Screen):
    TEXT = 'Welcome to TeleGods Bank, where your financial security is our top priority!\n\nPlease log in to access your account and enjoy a seamless banking experience.\n\nIf you\'re a new user, click on the "Sign up" button to create an account and explore the world of the TeleGods Bank.\n\nThank you for choosing TeleGods Bank!'
    ERROR1_TEXT = "Invalid login (User not found or incorrect password)"
    ERROR_INCOMPLETE_TEXT = "Please fill all the required fields"
    BANK_REGISTER_SCREEN_ID = "bank-register"
    BANK_MAIN_MENU_SCREEN_ID = "bank-main-menu"
    username = ""
    password = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR1_TEXT, id="error1", classes="text error hidden"),
            Static(
                self.ERROR_INCOMPLETE_TEXT,
                id="error-incomplete",
                classes="text error hidden",
            ),
            Input(
                placeholder="Username",
                id="username",
                restrict=r"^[a-zA-Z0-9_]+$",
                valid_empty=False,
            ),
            Input(
                placeholder="Password",
                id="password",
                valid_empty=False,
                password=True,
            ),
            Horizontal(
                Button(
                    label="Log in",
                    variant="success",
                    id="login",
                    classes="large-button",
                ),
                Button(
                    label="Sign up",
                    variant="primary",
                    id="register",
                    classes="large-button",
                ),
                Button(
                    label="Disconnect",
                    variant="error",
                    id="disconnect",
                    classes="large-button",
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def __update_error(self, error_code: int, id: str):
        dom = self.query_one(id)
        if error_code != 0 and dom.has_class("hidden"):
            dom.remove_class("hidden")
        elif error_code == 0 and not dom.has_class("hidden"):
            dom.add_class("hidden")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "username":
            self.username = event.value
        elif event.input.id == "password":
            self.password = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            print("error")
        match button_id:
            case "login":
                # Handle incomplete fields
                if self.username == "" or self.password == "":
                    self.__update_error(1, "#error-incomplete")
                    return
                else:
                    self.__update_error(0, "#error-incomplete")

                login_error_code, uuid = CLIENT.login(self.username, self.password)
                self.__update_error(login_error_code, "#error1")

                if login_error_code == 0:
                    self.uuid = uuid
                    self.app.push_screen(self.BANK_MAIN_MENU_SCREEN_ID)
            case "disconnect":
                CLIENT.bank_disconnect()
                self.app.pop_screen()


class TelegodsClientApp(App):
    BINDINGS = [
        ("ctrl+d", "toggle_dark_mode", "Toggle dark mode"),
        ("ctrl+q", "quit", "Quit"),
    ]
    CSS_PATH = "app.css"
    SCREENS = {
        "main-menu": MainMenu(),
        "bank-server-connection": BankServerConnection(),
        "bank-server-timeout": BankTimeout(),
        "bank-login": BankLogin(),
    }

    def on_mount(self) -> None:
        self.title = "TeleGods Client"
        self.sub_title = "version 0.1.0"
        self.push_screen("main-menu")

    def action_toggle_dark_mode(self):
        self.dark = not self.dark

    def action_quit(self):
        self.app.exit()


if __name__ == "__main__":
    global CLIENT, current_server
    CLIENT = Client()
    current_server = ""

    TelegodsClientApp().run()
