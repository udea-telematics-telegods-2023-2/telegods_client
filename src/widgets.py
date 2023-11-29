from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.dom import DOMNode
from textual.events import Compose
from textual.screen import Screen
from textual.widgets import Button, Digits, Header, Footer, Input, Label, Static
from json import dumps, loads

from client import Client

CLIENT = Client()
ERROR1_TEXT = "Invalid login (User not found or incorrect password)"
ERROR2_TEXT = "Invalid registration (User already registered)"
ERROR3_TEXT = "Insufficient funds"
ERROR128_TEXT = "The IP address you entered is invalid"
ERROR129_TEXT = "The port you entered is invalid"
ERROR130_TEXT = "Couldn't connect to the specified server, please check the address and try again..."
ERROR131_TEXT = "Please fill all the required fields"
ERROR132_TEXT = "Passwords don't match"
ERROR133_TEXT = "Invalid amount, please enter a value greater than 0"
ERROR252_TEXT = "UUID not found, please check the value and try again..."


def update_hidden(hide: bool, dom: DOMNode):
    if not hide and dom.has_class("hidden"):
        dom.remove_class("hidden")
    elif hide and not dom.has_class("hidden"):
        dom.add_class("hidden")


def clear_fields(screen: Screen, ids: list[str]):
    for id in ids:
        dom = screen.query_one(id)
        if isinstance(dom, Input):
            dom.value = ""


def clear_errors(screen: Screen, ids: list[str]):
    for id in ids:
        dom = screen.query_one(id)
        update_hidden(True, dom)


def handle_incomplete_fields_error(values: list):
    return 131 if any([value == "" for value in values]) else 0


class MainMenu(Screen):
    TEXT = "Welcome to TeleGods Client,\n\nHotkeys can be seen at all time in the bottom of the screen."

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Container(
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
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        # Add next screen with parameter
        self.app.push_screen(ServerConnection(button_id))


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


class ServerConnection(Screen):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.default_ip = "127.0.0.1"
        self.default_port = "8888"
        self.ip = self.default_ip
        self.port = self.default_port
        self.server_name = self.server.replace("-", " ")
        self.TEXT = f"Please enter the IP address and port of the {self.server_name} that you're trying to connect,\nor leave empty to use the default values..."

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(ERROR128_TEXT, id="error128", classes="text error hidden"),
            Static(ERROR129_TEXT, id="error129", classes="text error hidden"),
            Container(
                Input(
                    placeholder="IP Address (127.0.0.1)",
                    id="server-ip",
                    classes="ip-input",
                    restrict=r"[0-9.]*",
                    valid_empty=True,
                ),
                Input(
                    placeholder="Port (8888)",
                    id="server-port",
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

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "server-ip":
            self.ip = event.value if event.value != "" else self.default_ip
        elif event.input.id == "server-port":
            self.port = event.value if event.value != "" else self.default_port

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()
            case "connect":
                # Clear remaining errors
                clear_errors(self.screen, ["#error128", "#error129"])

                # Validate IP
                ip_error_code, _ = CLIENT.validate_ip(self.ip)
                update_hidden(ip_error_code == 0, self.query_one("#error128"))

                # Validate port
                port_error_code, _ = CLIENT.validate_port(self.port)
                update_hidden(port_error_code == 0, self.query_one("#error129"))

                if ip_error_code == 0 and port_error_code == 0:
                    connection_error_code, data = CLIENT.connect(self.ip, self.port)
                    # If got any error here, it means we couldn't connect to the server
                    print(connection_error_code)
                    print(self.server)
                    print(data)
                    if connection_error_code != 0 or self.server != data:
                        self.app.push_screen(Timeout())
                        return

                    # Else we logged in succesfully
                    if self.server == "bank":
                        self.app.push_screen(BankLogin())
                    elif self.server == "liquor_store":
                        error_code, json = CLIENT.list_liquors()
                        self.app.push_screen(LiquorStoreMainMenu(json))


class Timeout(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(ERROR130_TEXT, classes="text error"),
            Container(
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class LiquorStoreMainMenu(Screen):
    def __init__(self, json: str):
        super().__init__()
        parsed_json = loads(json)
        connected_users, OWNER_UUID = parsed_json[-2:]
        self.liquors_list = parsed_json[:-2]
        self.connected_users = connected_users
        self.OWNER_UUID = OWNER_UUID
        self.liquor_widgets = [
            self.LiquorWidget(uuid, commercial_name, cc, stock, price)
            for uuid, commercial_name, cc, stock, price in self.liquors_list
        ]

    TEXT = "Welcome to TeleGods Liquor Store, choose your poison!"

    class LiquorWidget(Static):
        def __init__(
            self, uuid: str, commercial_name: str, cc: str, stock: int, price: float
        ):
            self.uuid = uuid
            self.commercial_name = commercial_name
            self.cc = cc
            self.stock = stock
            self.price = price

        def compose(self) -> ComposeResult:
            yield Static(self.commercial_name)
            yield Static(f"Brought with delicacy from {self.cc}")
            yield Static(f"{self.cc} units left in stock")
            yield Static(f"{self.price} ＴＣ")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield ScrollableContainer(Static(self.TEXT, classes="text"), id="liquors")
        self.query_one("#liquors").mount_all(self.liquor_widgets)


class BankLogin(Screen):
    TEXT = 'Welcome to TeleGods Bank, where your financial security is our top priority!\n\nIf you\'re a new user, click on the "Register" button to create an account and explore the world of the TeleGods Bank.\n\nThank you for choosing TeleGods Bank!'
    username = ""
    password = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(ERROR1_TEXT, id="error1", classes="text error hidden"),
            Static(
                ERROR131_TEXT,
                id="error131",
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
            Container(
                Button(
                    label="Log in",
                    variant="success",
                    id="login",
                    classes="large-button",
                ),
                Button(
                    label="Register",
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

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#username", "#password"])

        # Clear errors
        clear_errors(self.screen, ["#error1", "#error131"])

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "username":
            self.username = event.value
        elif event.input.id == "password":
            self.password = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "disconnect":
                CLIENT.disconnect()
                self.app.pop_screen()

            case "login":
                # Clear remaining errors
                clear_errors(self.screen, ["#error1", "#error131"])

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error(
                    [self.username, self.password]
                )
                update_hidden(error_code == 0, self.query_one("#error131"))
                if error_code == 131:
                    return

                # Send login and handle error
                error_code, uuid = CLIENT.login(self.username, self.password)
                update_hidden(error_code == 0, self.query_one("#error1"))
                if error_code == 0:
                    self.app.push_screen(BankMainMenu(uuid, self.username))

            case "register":
                self.app.push_screen(BankRegister())


class BankRegister(Screen):
    TEXT = "Please provide a unique username containing only letters (a-z, A-Z), numbers (0-9), or underscores (_).\n\nIf you already have an account, click on the 'Back' button and log in your TeleGods Bank account."
    ERROR0 = "User succesfully registered, you can now go back and log in"
    username = ""
    password = ""
    confirm_password = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR0, id="error0", classes="text success hidden"),
            Static(ERROR2_TEXT, id="error2", classes="text error hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Static(ERROR132_TEXT, id="error132", classes="text error hidden"),
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
            Input(
                placeholder="Confirm your password",
                id="confirm-password",
                valid_empty=False,
                password=True,
            ),
            Container(
                Button(
                    label="Register",
                    variant="success",
                    id="register",
                    classes="large-button",
                ),
                Button(
                    label="Back",
                    variant="error",
                    id="back",
                    classes="large-button",
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#username", "#password", "#confirm-password"])

        # Clear errors and success message
        clear_errors(self.screen, ["#error0", "#error2", "#error131", "#error132"])

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "username":
            self.username = event.value
        elif event.input.id == "password":
            self.password = event.value
        elif event.input.id == "confirm-password":
            self.confirm_password = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()

            case "register":
                # Clear errors and success message
                clear_errors(
                    self.screen, ["#error0", "#error2", "#error131", "#error132"]
                )

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error(
                    [self.username, self.password, self.confirm_password]
                )
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Handle password mismatch
                if self.password != self.confirm_password:
                    error_code = 132
                    update_hidden(error_code != 132, self.query_one("#error132"))
                    return

                # Send login and handle error
                error_code, _ = CLIENT.register(self.username, self.password)
                update_hidden(error_code != 2, self.query_one("#error2"))

                # Show success message
                update_hidden(error_code != 0, self.query_one("#error0"))


class BankBalance(Screen):
    def __init__(self, balance: str):
        super().__init__()
        self.balance = balance
        self.TEXT = "Your current balance is:"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Digits(f"{self.balance}  ＴＣ (TeleCredits)", classes="text"),
            Button(label="Back", variant="error", id="back", classes="large-button"),
            classes="centered-container",
        )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.app.pop_screen()


class BankDeposit(Screen):
    def __init__(self, uuid):
        super().__init__()
        self.TEXT = (
            "Please enter the amount of money you want to deposit into your account"
        )
        self.ERROR0 = "Succesfully deposited the amount into your account balance"
        self.amount = ""
        self.uuid = uuid

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR0, id="error0", classes="text success hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Static(ERROR133_TEXT, id="error133", classes="text error hidden"),
            Input(
                placeholder="Amount",
                id="amount",
                valid_empty=False,
                restrict=r"[0-9]*",
            ),
            Container(
                Button(
                    label="Deposit",
                    variant="success",
                    id="deposit",
                    classes="large-button",
                ),
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#amount"])

        # Clear errors and success message
        clear_errors(self.screen, ["#error0", "#error131", "#error133"])

    def on_input_changed(self, event: Input.Changed) -> None:
        self.amount = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()

            case "deposit":
                # Clear errors and success message
                clear_errors(self.screen, ["#error0", "#error131", "#error133"])

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error([self.amount])
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Send deposit
                CLIENT.deposit(self.uuid, self.amount)

                # Clear amount to deny accidental deposit
                clear_fields(self.screen, ["#amount"])

                # Show success message
                update_hidden(error_code != 0, self.query_one("#error0"))


class BankWithdraw(Screen):
    def __init__(self, uuid):
        super().__init__()
        self.TEXT = (
            "Please enter the amount of money you want to withdraw from your account"
        )
        self.ERROR0 = "Succesfully withdrawed the amount from your account balance"
        self.amount = ""
        self.uuid = uuid

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(ERROR3_TEXT, id="error3", classes="text error hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Static(self.ERROR0, id="error0", classes="text success hidden"),
            Input(
                placeholder="Amount",
                id="amount",
                valid_empty=False,
                restrict=r"[0-9]*",
            ),
            Container(
                Button(
                    label="Withdraw",
                    variant="warning",
                    id="withdraw",
                    classes="large-button",
                ),
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#amount"])

        # Clear errors and success message
        clear_errors(self.screen, ["#error0", "#error3", "#error131", "#error133"])

    def on_input_changed(self, event: Input.Changed) -> None:
        self.amount = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()

            case "withdraw":
                # Clear errors and success message
                clear_errors(self.screen, ["#error0", "#error3", "#error131"])

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error([self.amount])
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Send withdraw and handle error
                error_code, _ = CLIENT.withdraw(self.uuid, self.amount)
                update_hidden(error_code != 3, self.query_one("#error3"))

                # Clear amount to prevent accidental withdraw
                clear_fields(self.screen, ["#amount"])

                # Show success message
                update_hidden(error_code != 0, self.query_one("#error0"))


class BankTransfer(Screen):
    def __init__(self, uuid):
        super().__init__()
        self.TEXT = (
            "Please enter the recipient's UUID and the amount you want to transfer"
        )
        self.ERROR0 = "Transaction succesful"
        self.uuid = uuid
        self.recv_uuid = ""
        self.amount = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR0, id="error0", classes="text success hidden"),
            Static(ERROR3_TEXT, id="error3", classes="text error hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Static(ERROR252_TEXT, id="error252", classes="text error hidden"),
            Input(
                placeholder="Receiver UUID",
                id="recv-uuid",
                valid_empty=False,
                restrict=r"[a-z0-9-]*",
            ),
            Input(
                placeholder="Amount",
                id="amount",
                valid_empty=False,
                restrict=r"[0-9]*",
            ),
            Container(
                Button(
                    label="Transfer",
                    variant="warning",
                    id="transfer",
                    classes="large-button",
                ),
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#recv-uuid", "#amount"])

        # Clear errors and success message
        clear_errors(self.screen, ["#error0", "#error3", "#error131", "#error252"])

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "recv-uuid":
            self.recv_uuid = event.value
        elif event.input.id == "amount":
            self.amount = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()

            case "transfer":
                # Clear errors and success message
                clear_errors(
                    self.screen, ["#error0", "#error3", "#error131", "#error252"]
                )

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error(
                    [self.recv_uuid, self.amount]
                )
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Send transfer and handles errors
                error_code, _ = CLIENT.transfer(
                    sender_uuid=self.uuid, recv_uuid=self.recv_uuid, amount=self.amount
                )

                # Clear amount to deny accidental double transfer
                clear_fields(self.screen, ["#amount"])

                # UUID not found
                if error_code == 252:
                    update_hidden(error_code != 252, self.query_one("#error252"))
                    return

                # Insufficient funds
                if error_code == 3:
                    update_hidden(error_code != 3, self.query_one("#error3"))
                    return

                # Show success message
                update_hidden(error_code != 0, self.query_one("#error0"))


class BankVerifyPassword(Screen):
    def __init__(self, username: str):
        super().__init__()
        self.TEXT = "Please enter your current password"
        self.ERROR1_TEXT = "Password doesn't match actual password"
        self.username = username
        self.password = ""
        self.changed = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR1_TEXT, id="error1", classes="text error hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Input(
                placeholder="Current password",
                id="password",
                valid_empty=False,
                password=True,
            ),
            Container(
                Button(
                    label="Check password",
                    variant="warning",
                    id="checkpasswd",
                    classes="large-button",
                ),
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        if self.changed:
            self.app.pop_screen()

        # Clear fields on resume
        clear_fields(self.screen, ["#password"])

        # Clear errors and success message
        clear_errors(self.screen, ["#error1", "#error131"])

    def on_input_changed(self, event: Input.Changed) -> None:
        self.password = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.app.pop_screen()

            case "checkpasswd":
                # Clear errors
                clear_errors(self.screen, ["#error1", "#error131"])

                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error([self.password])
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Tries to login with supplied information
                error_code, uuid = CLIENT.login(self.username, self.password)
                if error_code == 1:
                    update_hidden(error_code != 1, self.query_one("#error1"))
                    return

                # Show success message
                self.changed = self.app.push_screen(
                    BankChangePassword(uuid, self.password)
                )


class BankChangePassword(Screen):
    def __init__(self, uuid: str, old_password: str):
        super().__init__()
        self.TEXT = "Please enter your new password"
        self.ERROR0_TEXT = "Password changed succesfully"
        self.uuid = uuid
        self.old_password = old_password
        self.password = ""
        self.confirm_password = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Static(self.ERROR0_TEXT, id="error0", classes="text success hidden"),
            Static(ERROR131_TEXT, id="error131", classes="text error hidden"),
            Static(ERROR132_TEXT, id="error132", classes="text error hidden"),
            Input(
                placeholder="New password",
                id="password",
                valid_empty=False,
                password=True,
            ),
            Input(
                placeholder="Confirm new password",
                id="confirm-password",
                valid_empty=False,
                password=True,
            ),
            Container(
                Button(
                    label="Change password",
                    variant="warning",
                    id="chpasswd",
                    classes="large-button",
                ),
                Button(
                    label="Back", variant="error", id="back", classes="large-button"
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def on_screen_resume(self) -> None:
        # Clear fields on resume
        clear_fields(self.screen, ["#password", "#confirm-password"])

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "password":
            self.password = event.value
        elif event.input.id == "confirm-password":
            self.confirm_password = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Get button ID and validate it
        button_id = event.button.id
        if button_id is None:
            return

        match button_id:
            case "back":
                self.dismiss(True)

            case "chpasswd":
                # Clear errors and success message
                clear_errors(self.screen, ["#error0", "#error131", "#error132"])
                error_code = 0
                # Handle incomplete fields error
                error_code = handle_incomplete_fields_error(
                    [self.password, self.confirm_password]
                )
                if error_code == 131:
                    update_hidden(error_code != 131, self.query_one("#error131"))
                    return

                # Handle password mismatch
                if self.password != self.confirm_password:
                    error_code = 132
                    update_hidden(error_code != 132, self.query_one("#error132"))
                    return

                # Sends CHPASSWD with supplied information
                print(self.uuid, self.old_password, self.password)
                error_code, _ = CLIENT.chpasswd(
                    self.uuid, self.old_password, self.password
                )

                # Show success message
                update_hidden(error_code != 0, self.query_one("#error0"))


class BankMainMenu(Screen):
    def __init__(self, uuid: str, username: str):
        super().__init__()
        self.uuid = uuid
        self.username = username
        self.TEXT = f"Welcome back {username}, your UUID is {self.uuid}\n\nPlease select a transaction:"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield Container(
            Static(self.TEXT, classes="text"),
            Button(
                label="Check balance",
                variant="success",
                id="balance",
                classes="large-button",
            ),
            Button(
                label="Deposit funds",
                variant="success",
                id="deposit",
                classes="large-button",
            ),
            Button(
                label="Withdraw money",
                variant="warning",
                id="withdraw",
                classes="large-button",
            ),
            Button(
                label="Transfer funds",
                variant="warning",
                id="transfer",
                classes="large-button",
            ),
            Container(
                Button(
                    label="Change Password",
                    variant="error",
                    id="chpasswd",
                    classes="large-button",
                ),
                Button(
                    label="Logout",
                    variant="error",
                    id="logout",
                    classes="large-button",
                ),
                classes="horizontal-selection",
            ),
            classes="centered-container",
        )

    def logout(self):
        _, _ = CLIENT.logout()
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            return
        match button_id:
            case "balance":
                error_code, cmd_return = CLIENT.balance()
                if error_code != 0:
                    return
                self.app.push_screen(BankBalance(cmd_return))
            case "deposit":
                self.app.push_screen(BankDeposit(self.uuid))
            case "withdraw":
                self.app.push_screen(BankWithdraw(self.uuid))
            case "transfer":
                self.app.push_screen(BankTransfer(self.uuid))
            case "chpasswd":
                self.app.push_screen(BankVerifyPassword(self.username))
            case "logout":
                self.logout()
