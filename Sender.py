import queue
import threading

from datagram import Datagram


class Sender(threading.Thread):  # to add arguments with priority
    def __init__(self, socket, send_buf: queue.Queue, ack_list: queue.Queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.to_send = send_buf
        self.ack_list = ack_list
        self.to_ack = []
        self.acked = -1
        self.start_time = []

    def run(self):#有问题
        while True:
            if self.to_send.empty() and self.ack_list.empty():
                continue
            if self.to_send.empty():
                pack = Datagram()
            else:
                pack = self.to_send.get()
            if not self.ack_list.empty():
                seq = self.ack_list.get()
                pack.set_ack(1)
                pack.set_sack(seq)
                print("sAck", pack.SACK)
            print("Payload", pack.PAYLOAD)

            if self.socket.send_to is not None:
                self.socket.sendto(pack.packet, self.socket.send_to)
