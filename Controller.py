import queue

import datagram
from Sender import Sender
from datagram import Datagram
from rdt import RDTSocket


class Controller:
    def __init__(self, socket: RDTSocket, data: bytes):
        self.socket = socket

        self.send_list = []
        self.data = data
        self.recv_buf = queue.PriorityQueue()
        self.window_size = 8

        self.to_ack = 0
        self.tmp = 0
        self.duplicate = 0

        self.received = -1

        self.finish_send = False
        self.finish_receive = False

        self.nxt_ack = queue.Queue()
        self.send_buf = queue.Queue()

        self.sender = Sender(self.socket, self.send_buf, self.nxt_ack)

    def ack_pack(self, ack):
        if self.to_ack - 1 == ack and self.to_ack < len(self.send_list):
            self.duplicate += 1
            if self.duplicate >= 3:
                self.duplicate = 0
                self.send_buf.put(self.send_list[self.to_ack])
        if self.to_ack <= ack + 1:
            self.duplicate = 0
            while self.to_ack <= ack + 1 and self.tmp < len(self.send_list) \
                    and self.tmp - self.to_ack < self.window_size:  # to debug
                self.send_buf.put(self.send_list[self.tmp])
                self.tmp += 1
                self.to_ack += 1
        if self.to_ack >= len(self.send_list):  # finish sending
            while self.send_buf.not_empty:
                self.send_buf.get()
            self.finish_send = True

    def recv_pack(self, packet: Datagram):
        print(packet.TYPE, packet.SYN, packet.ACK, packet.SACK)
        if packet.ACK != 0:
            self.ack_pack(packet.SACK)

        while not self.recv_buf.empty():
            seq, data = self.recv_buf.get()
            if seq == self.received + 1:
                self.received = seq
                self.data += data
            else:
                self.recv_buf.put((seq, data))
                break

        if packet.SEQ == self.received + 1:
            self.data += packet.PAYLOAD
            self.received = packet.SEQ
            while not self.recv_buf.empty():
                seq, data = self.recv_buf.get()
                if seq == self.received + 1:
                    self.received = seq
                    self.data += data
                else:
                    self.recv_buf.put((seq, data))
                    break
        else:
            if packet.SEQ > self.received + 1:
                self.recv_buf.put((packet.SEQ, packet.PAYLOAD))
        if not self.sender.is_alive():
            self.sender.start()

    def finish(self):
        return self.finish_send and self.finish_receive

    def send(self, to_send: bytes):
        self.send_list.extend(datagram.segment(to_send, 256))
        while self.send_buf.qsize() < self.window_size and self.tmp < len(self.send_list):
            self.send_buf.put(self.send_list[self.tmp])
            self.tmp += 1
        if not self.socket.receiver.is_alive():
            self.socket.receiver.start()
        if not self.sender.is_alive():
            self.sender.start()

    def send_syn(self):
        self.send_list = []
        self.tmp = 0
        self.send_list.append(Datagram(syn=1, type=1))
        self.send_buf.put(self.send_list[self.tmp])
        if not self.socket.receiver.is_alive():
            self.socket.receiver.start()
        if not self.sender.is_alive():
            self.sender.start()
