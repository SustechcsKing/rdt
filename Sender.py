import queue
import threading

from datagram import Datagram
from rdt import RDTSocket


class Sender(threading.Thread):  # to add arguments with priority
    def __init__(self, socket: RDTSocket, send_buf: queue.Queue, ack_list: queue.Queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.to_send = send_buf
        self.toAck = ack_list

    def run(self):
        while not self.to_send.empty() or not self.toAck.empty():
            if self.to_send.empty():
                pack = Datagram()
            else:
                pack = self.to_send.get()
            if not self.toAck.empty():
                seq = self.toAck.get()
                pack.set_ack(1)
                pack.set_sack(seq)
            self.socket.sendto(pack.packet, self.socket.send_to)
