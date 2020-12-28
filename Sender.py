import queue
import threading
import time

from datagram import Datagram


class Sender(threading.Thread):  # to add arguments with priority
    def __init__(self, socket, send_buf: queue.PriorityQueue, ack_list: queue.Queue, ack_recv: queue.Queue):
        threading.Thread.__init__(self)
        self.socket = socket
        self.to_send = send_buf
        self.ack_list = ack_list  # ack 对方
        self.ack_recv = ack_recv  # ack received
        self.to_ack = []  # 自己等待ack的包
        self.window = [0]
        self.ack_index = 0
        self.timeout = 0.5

    def run(self):  # 有问题
        while True:
            if self.to_send.empty() and self.ack_list.empty():
                continue
            if self.to_send.empty():
                pack = Datagram()
            else:
                seq, pack = self.to_send.get()
                self.to_ack.append((pack, time.time()))
            if not self.ack_list.empty():
                seq = self.ack_list.get()
                pack.set_ack(1)
                pack.set_sack(seq)

            if self.ack_index < len(self.to_ack):  # timeout重传处理
                while not self.ack_recv.empty():
                    ack = self.ack_recv.get()
                    if ack >= self.ack_index:
                        self.ack_index = ack + 1
                        self.window[0] = len(self.to_ack) - self.ack_index + self.to_send.qsize()
                if self.ack_index >= len(self.to_ack):
                    continue
                # pack, start_time = self.to_ack[self.ack_index]
                # while time.time() - start_time > self.timeout:
                #     self.to_send.put((pack.SEQ, pack))
                #     self.ack_index += 1
                #     if self.ack_index < len(self.to_ack):
                #         pack, start_time = self.to_ack[self.ack_index]
                #     else:
                #         break

            try:
                self.socket.sendto(pack.packet, self.socket.send_to)
            except:
                pass
