import queue
import threading

from datagram import Datagram


class Sender(threading.Thread):  # to add arguments with priority
    def __init__(self, socket, priority_buf: queue.Queue, send_buf: queue.Queue, ack_list: queue.Queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.to_send1 = priority_buf
        self.to_send2 = send_buf
        self.ack_list = ack_list
        self.to_ack = []
        self.acked = -1
        self.start_time = []

    def run(self):#有问题
        while True:
            if self.to_send1.empty() and self.to_send2.empty() and self.ack_list.empty():   # nothing to be send(ack or data or both)
                continue
            if not self.to_send1.empty():
                pack = self.to_send1.get()
            elif not self.to_send2.empty():     # has ack or data or both to be sent
                pack = self.to_send2.get()
            else:
                pack = Datagram()
            if not self.ack_list.empty():
                seq = self.ack_list.get()
                pack.set_ack(1)
                pack.set_sack(seq)
                print("sAck", pack.SACK)
            print("Payload", pack.PAYLOAD)

            if self.socket.send_to is not None:
                self.socket.sendto(pack.packet, self.socket.send_to)
