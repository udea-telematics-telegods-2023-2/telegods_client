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

    def bank_connect(self, ip: str, port: str) -> tuple[int, str]:
        self.bank_ip = ip
        self.bank_port = port
        self.bank_socket = socket(AF_INET, SOCK_STREAM)
        self.bank_socket.settimeout(3)
        try:
            self.bank_socket.connect((self.bank_ip, int(self.bank_port)))
            return 0, ""
        except ConnectionRefusedError:
            return 130, ""
        except TimeoutError:
            return 131, ""

    def bank_disconnect(self) -> tuple[int, str]:
        self.bank_socket.close()
        return 0, ""

    def login(self, username: str, password: str) -> tuple[int, str]:
        self.bank_socket.sendall(f"LOGIN {username} {password}\r\n".encode("utf-8"))
        response, data = self.bank_socket.recv(1024).decode("utf-8").split()
        if response.startswith("OK"):
            self.uuid = data
            return 0, self.uuid
        return int(data), ""
