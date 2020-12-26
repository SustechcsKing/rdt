import queue
import threading

from datagram import Datagram
from rdt import RDTSocket


class Receiver(threading.Thread):
    def __init__(self, socket: RDTSocket, recv_buf: queue.Queue):
        super().__init__()
        self.socket = socket
        self.recv_buf = recv_buf
        self.syn = 0
        self.fin = 0

    def run(self):
        while True:
            packet, addr = self.socket.recvfrom(2048)
            datagram = Datagram()
            datagram.depack(packet)
            if datagram.TYPE == 1 and datagram.SYN == 1:
                self.recv_buf.put((addr, datagram))
            if addr != self.socket.recv_from:
                continue
            if datagram.checksum() == datagram.CHECKSUM:
                self.recv_buf.put(datagram)
