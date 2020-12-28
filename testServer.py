import threading
import time

from rdt import RDTSocket

server_addr = ('127.0.0.1', 2130)


class Echo(threading.Thread):
    def __init__(self, conn: RDTSocket, address):
        threading.Thread.__init__(self)
        self.conn = conn
        self.address = address

    def run(self):
        start = time.perf_counter()
        while True:
            data = self.conn.recv(2048)
            if data != b'':
                print("receive and send:", data)
                self.conn.send(data)


#        print(f'connection finished in {time.perf_counter() - start}s')


def main():
    server_socket = RDTSocket()
    server_socket.bind(server_addr)
    while True:
        conn, addr = server_socket.accept()
        print(addr)
        Echo(conn, addr).start()


if __name__ == '__main__':
    main()
