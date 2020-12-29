import queue
import threading

from datagram import Datagram


class Receiver(threading.Thread):
    def __init__(self, socket, recv_buf: queue.Queue):
        super().__init__()
        self.socket = socket
        self.recv_buf = recv_buf
        self.syn = 0
        self.fin = 0

    def run(self):
        while True:
            try:
                packet, addr = self.socket.recvfrom(2048)
                datagram = Datagram()
                datagram.depack(packet)
                if datagram.TYPE == 1 and datagram.SYN == 1:
                    self.recv_buf.put((addr, datagram))
                if addr != self.socket.recv_from or self.socket.recv_from is None:
                    continue
                if datagram.checksum() == datagram.CHECKSUM:
                    self.recv_buf.put((addr, datagram))
            except:
                pass
