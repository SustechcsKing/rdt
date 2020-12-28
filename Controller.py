import queue

import datagram
from Receiver import Receiver
from Sender import Sender
from datagram import Datagram


class Controller:
    def __init__(self, socket, data: bytes):
        self.socket = socket

        self.send_list = []
        self.data = data

        self.window_size = 5

        self.tmp = 0
        self.duplicate = 0
        self.used_seq = 0

        self.wanting = 0

        self.finish_send = False
        self.finish_receive = False

        self.nxt_ack = queue.Queue()
        self.send_buf = queue.PriorityQueue()
        self.ack_list = queue.Queue()  # used to send ack to sender
        self.recv_buf = queue.Queue()
        self.ack_recv = queue.Queue()

        self.data_buf = queue.PriorityQueue()  # non-blocking mode to manage sequence
        self.recv_data = b''  # right sized data

        self.sender = Sender(self.socket, self.send_buf, self.nxt_ack, self.ack_recv)
        self.receiver = Receiver(self.socket, self.recv_buf)
        self.sender.start()
        self.receiver.start()

    def ack_pack(self, ack):
        self.ack_recv.put(ack)
        self.send_packs()

    def send_packs(self):
        print("w=", self.sender.window[0])
        while self.sender.window[0] < self.window_size and self.tmp < len(self.send_list):
            self.send_buf.put((self.send_list[self.tmp].SEQ, self.send_list[self.tmp]))
            print('put', self.send_list[self.tmp].PAYLOAD)
            self.tmp += 1
            self.sender.window[0] += 1

    def recv_pack(self):
        addr, datagram = self.recv_blocking()
        print("recv type,sin,ack,sack", datagram.TYPE, datagram.SYN, datagram.ACK, datagram.SACK)
        return datagram.PAYLOAD
        # if datagram.ACK != 0:
        #     self.ack_pack(datagram.SACK)
        #
        # while not self.recv_buf.empty():
        #     seq, data = self.recv_buf.get()
        #     if seq == self.wanting + 1:
        #         self.wanting = seq
        #         self.data += data
        #     else:
        #         self.recv_buf.put((seq, data))
        #         break
        #
        # if datagram.SEQ == self.wanting + 1:
        #     self.data += datagram.PAYLOAD
        #     self.wanting = datagram.SEQ
        #     while not self.recv_buf.empty():
        #         seq, data = self.recv_buf.get()
        #         if seq == self.wanting + 1:
        #             self.wanting = seq
        #             self.data += data
        #         else:
        #             self.recv_buf.put((seq, data))
        #             break
        # else:
        #     if datagram.SEQ > self.wanting + 1:
        #         self.recv_buf.put((datagram.SEQ, datagram.PAYLOAD))

    def send(self, to_send: bytes):  # 有问题
        self.send_list.extend(datagram.segment(to_send, 256, pre=self.used_seq))
        self.used_seq += (len(to_send) + 255) // 256
        print("used_seq", self.used_seq)
        self.send_packs()

    def send_syn(self):
        self.send_list.append(Datagram(syn=1, type=1, SEQ=self.used_seq))
        self.send_buf.put((self.send_list[self.tmp].SEQ, self.send_list[self.tmp]))
        self.tmp += 1
        self.used_seq += 1

    def send_syn_ack(self):
        self.send_list.append(Datagram(syn=1, type=1, ack=1, SACK=0, SEQ=self.used_seq))
        self.send_buf.put((self.send_list[self.tmp].SEQ, self.send_list[self.tmp]))
        self.tmp += 1
        self.used_seq += 1

    def recv_blocking(self):
        while True:
            if self.recv_buf.not_empty:
                addr, datagram = self.recv_buf.get()
                print("Recv Pack")
                if datagram.LEN != 0:
                    print("seq,data", datagram.SEQ, datagram.PAYLOAD)
                if datagram.ACK == 1:
                    print("sack", datagram.SACK)
                if datagram.ACK == 1:
                    self.ack_pack(datagram.SACK)

                if datagram.SEQ < self.wanting:
                    continue

                if datagram.LEN != 0 or datagram.TYPE == 1:
                    self.nxt_ack.put(self.wanting)
                    print("put_ack", self.wanting)

                self.wanting = datagram.SEQ + 1  # Here is a problem
                return addr, datagram

    def recv_nonblocking(self):

        if self.recv_buf.not_empty:
            addr, datagram = self.recv_buf.get()
            print("Recv Pack")
            if datagram.LEN != 0:
                print("seq,data", datagram.SEQ, datagram.PAYLOAD)
            if datagram.ACK == 1:
                print("sack", datagram.SACK)

            if datagram.SEQ < self.wanting:
                self.send_packs()
                return

            if datagram.SEQ == self.wanting:
                self.wanting += 1
                self.recv_data += datagram.PAYLOAD
                if not self.data_buf.empty():
                    seq, nxt_datagram = self.data_buf.get()
                    while seq == self.wanting:
                        self.wanting += 1
                        self.recv_data += nxt_datagram.PAYLOAD
                        if not self.data_buf.empty():
                            seq, nxt_datagram = self.data_buf.get()
                    if not self.data_buf.empty():
                        self.data_buf.put((seq, nxt_datagram))
                print(self.wanting - 1)
                self.ack_recv.put(self.wanting - 1)
                self.send_packs()
                return
            if datagram.SEQ > self.wanting:
                self.data_buf.put((datagram.SEQ, datagram))

    def recv_syn(self):
        self.wanting = 0
        while True:
            addr, datagram = self.recv_blocking()
            if datagram.TYPE == 1 and datagram.SYN == 1:
                return addr
