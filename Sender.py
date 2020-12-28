import queue
import threading
import time

from datagram import Datagram


class Sender(threading.Thread):  # to add arguments with priority
    def __init__(self, socket, send_buf: queue.PriorityQueue, ack_list: queue.Queue, ack_recv: queue.Queue, window_size: []):
        threading.Thread.__init__(self)
        self.socket = socket
        self.to_send = send_buf
        self.ack_list = ack_list  # ack 对方
        self.ack_recv = ack_recv  # ack received
        self.last_ack = -1
        self.to_ack = []  # 自己等待ack的包
        self.window = [0]    # num of to ack
        self.ack_index = 0
        self.timeout = 10
        self.size = window_size

    def run(self):  # 有问题
        while True:
            if ((len(self.to_ack) - self.ack_index) >= self.size[0] or self.to_send.empty()) and self.ack_list.empty():
                continue

            if (len(self.to_ack) - self.ack_index) < self.size[0]:
                if not self.to_send.empty():
                    print("len(self.to_ack)", len(self.to_ack), )
                    print("already_acked:", self.ack_index)
                    seq, pack = self.to_send.get()
                    self.to_ack.append((pack, time.time()))
                    print("send_seq", pack.SEQ)
            else:
                pack = Datagram()

            if not self.ack_list.empty():
                while not self.ack_list.empty():
                    sack = self.ack_list.get()
                    # print("send_ack", sack)
                    if sack > self.last_ack:
                        self.last_ack = sack
                pack.set_ack(1)
                # print("has sack 1", self.last_ack)
                pack.set_sack(self.last_ack)
            # if self.last_ack != -1:
            #     pack.set_ack(1)
            #     pack.set_sack(self.last_ack)
            #     print("send_last_ack", self.last_ack)

            # if (len(self.to_ack) - 1 - self.ack_index) < self.size[0]:
            #     print("send_last_ack", self.last_ack)

            if self.ack_index < len(self.to_ack):
                while not self.ack_recv.empty():
                    ack = self.ack_recv.get()
                    if ack >= self.ack_index:
                        self.ack_index = ack + 1
                        # self.window[0] = len(self.to_ack) - self.ack_index
                # print("len(self.to_ack)", len(self.to_ack), )
                # print("already_acked:", self.ack_index)
                # timeout
                if self.ack_index < len(self.to_ack):
                    pack1, start_time = self.to_ack[self.ack_index]
                    while time.time() - start_time > self.timeout:
                        print("retrans", time.time() - start_time, self.ack_index, pack1.SEQ)
                        self.to_send.put((pack1.SEQ, pack1))
                        self.ack_index += 1
                        if self.ack_index < len(self.to_ack):
                            pack1, start_time = self.to_ack[self.ack_index]
                        else:
                            break

            try:
                self.socket.sendto(pack.packet, self.socket.send_to)
            except:
                pass
