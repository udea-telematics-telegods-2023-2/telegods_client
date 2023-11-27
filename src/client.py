import ipaddress
from socket import socket, AF_INET, SOCK_STREAM


class Client:
    def validate_ip(self, ip: str) -> tuple[int, str]:
        try:
            ipaddress.ip_address(ip)
            return 0, ""
        except ValueError:
            return 128, ""

    def validate_port(self, port: str) -> tuple[int, str]:
        try:
            _port = int(port)
            return (0, "") if 1 <= _port <= 65535 else (129, "")
        except ValueError:
            return 129, ""

    def connect(self, ip: str, port: str) -> tuple[int, str]:
        self.ip = ip
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.ip, int(self.port)))
            self.socket.sendall("HI\r\n".encode("utf-8"))
            response, *data = self.socket.recv(1024).decode("utf-8").split()
            if response == "OK":
                return 0, data[0]
            return 130, ""
        except ConnectionRefusedError:
            return 130, ""
        except TimeoutError:
            return 131, ""

    def disconnect(self) -> tuple[int, str]:
        self.socket.close()
        return 0, ""

    def reconnect(self) -> tuple[int, str]:
        self.disconnect()
        return self.connect(self.ip, self.port)

    def login(self, username: str, password: str) -> tuple[int, str]:
        self.socket.sendall(f"LOGIN {username} {password}\r\n".encode("utf-8"))
        response, data = self.socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            self.uuid = data
            return 0, self.uuid
        return int(data), ""

    def register(self, username: str, password: str) -> tuple[int, str]:
        self.socket.sendall(f"REGISTER {username} {password}\r\n".encode("utf-8"))
        response, *data = self.socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            return 0, ""
        return int(data[0]), ""

    def logout(self) -> tuple[int, str]:
        self.socket.sendall("LOGOUT\r\n".encode("utf-8"))
        # Handles weird bug that raises an exception each two logins
        self.reconnect()
        # Always succeeds
        return 0, ""

    def balance(self) -> tuple[int, str]:
        self.socket.sendall("BALANCE\r\n".encode("utf-8"))
        _, data = self.socket.recv(1024).decode("utf-8").split()
        # Always succeeds
        return 0, data

    def deposit(self, uuid: str, amount: str) -> tuple[int, str]:
        self.socket.sendall(f"DEPOSIT {uuid} {amount}\r\n".encode("utf-8"))
        self.socket.recv(1024).decode("utf-8").split()
        # Always succeeds
        return 0, ""

    def withdraw(self, uuid: str, amount: str) -> tuple[int, str]:
        self.socket.sendall(f"WITH {uuid} {amount}\r\n".encode("utf-8"))
        response, *data = self.socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            return 0, ""
        return int(data[0]), ""

    def transfer(
        self, sender_uuid: str, recv_uuid: str, amount: str
    ) -> tuple[int, str]:
        self.socket.sendall(
            f"TRANSFER {sender_uuid} {recv_uuid} {amount}\r\n".encode("utf-8")
        )
        response, *data = self.socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            return 0, ""
        return int(data[0]), ""

    def chpasswd(
        self, uuid: str, old_password: str, new_password: str
    ) -> tuple[int, str]:
        self.socket.sendall(
            f"CHPASSWD {uuid} {old_password} {new_password}\r\n".encode("utf-8")
        )
        response, *data = self.socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            return 0, ""
        return int(data[0]), ""
