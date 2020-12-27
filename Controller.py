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

        self.window_size = 8

        self.to_ack = 0
        self.tmp = 0
        self.last_ack = 0
        self.duplicate = 1

        self.wanting = 0

        self.finish_send = False
        self.finish_receive = False

        self.nxt_ack = queue.Queue()
        self.send_buf = queue.Queue()
        self.priority_buf = queue.Queue()   # send buffer with higher priority for retransmission
        # caused by time_out or duplicate ACK(loss)
        self.recv_buf = queue.Queue()
        # 当receive buffer容量不够
        # 1. 立即发三次重复ACK消息提示缺失的包
        # 2. 拥塞机制，减少发包

        self.sender = Sender(self.socket, self.send_buf, self.nxt_ack).start()
        self.receiver = Receiver(self.socket, self.recv_buf).start()

    def ack_pack(self, ack):    # 在ACK=1（receiver确实有收到包）时被调用； ACK=0只发送数据没有收到包去确认
        if self.to_ack < ack + 1:   # ack: receiver确认收到的最新一个包
            self.duplicate = 1
            while self.to_ack < ack + 1:
                self.to_ack += 1
                if self.tmp < len(self.send_list) \
                    and self.tmp - self.to_ack < self.window_size - self.priority_buf.qsize():
                    self.send_buf.put(self.send_list[self.tmp])
                    self.tmp += 1

        elif self.to_ack == ack + 1:
            self.duplicate += 1

            if self.duplicate == 3:
                # call retransmission
                self.priority_buf.put(self.send_list[ack])

    def recv_pack(self):
        addr, datagram = self.recv_blocking()
        print(datagram.TYPE, datagram.SYN, datagram.ACK, datagram.SACK)
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

    def send(self, to_send: bytes):#有问题
        self.send_list.extend(datagram.segment(to_send, 256))
        while self.send_buf.qsize() < self.window_size and self.tmp < len(self.send_list):
            self.send_buf.put(self.send_list[self.tmp])
            self.tmp += 1

    def send_syn(self):
        self.send_list.append(Datagram(syn=1, type=1))
        self.send_buf.put(self.send_list[self.tmp])

    def send_syn_ack(self):
        self.send_list.append(Datagram(syn=1, type=1, ack=1, SACK=0))
        self.send_buf.put(self.send_list[self.tmp])
        self.tmp += 1

    def recv_blocking(self):
        while True:
            # if self.recv_buf.not_empty:
            #     addr, datagram = self.recv_buf.get()
            #     if datagram.ACK == 1:
            #         self.ack_pack(datagram.SACK)
            #
            #     if datagram.LEN != 0 or datagram.TYPE == 1:
            #         self.nxt_ack.put(self.wanting)
            #     if datagram.SEQ < self.wanting:
            #         continue
            #     self.wanting = datagram.SEQ + 1
            #     return addr, datagram
            if self.recv_buf.not_empty:
                addr, datagram = self.recv_buf.get()
                if datagram.ACK == 1:
                    self.ack_pack(datagram.SACK)

                if datagram.LEN != 0 or datagram.TYPE == 1:
                    self.nxt_ack.put(self.wanting)
                if datagram.SEQ < self.wanting:
                    continue
                self.wanting = datagram.SEQ + 1
                return addr, datagram

    def recv_syn(self):
        while True:
            addr, datagram = self.recv_blocking()
            if datagram.TYPE == 1 and datagram.SYN == 1:
                return addr
