import USocket
import datagram
from USocket import UnreliableSocket
import threading
import time
import queue as q
from datagram import Datagram

port_cnt = 0


class RDTSocket(UnreliableSocket):
    """
    The functions with which you are to build your RDT.
    -   recvfrom(bufsize)->bytes, addr
    -   sendto(bytes, address)
    -   bind(address)

    You can set the mode of the socket.
    -   settimeout(timeout)
    -   setblocking(flag)
    By default, a socket is created in the blocking mode. 
    https://docs.python.org/3/library/socket.html#socket-timeouts

    """

    def __init__(self, rate=None, debug=True):
        super().__init__(rate=rate)
        self._rate = rate
        self._send_to = None
        self._recv_from = None
        self.debug = debug
        self.data = bytes()
        self.controller = Controller(self, self.data)
        self.receiver = Receiver(self, self.controller)
        #############################################################################
        # TODO: ADD YOUR NECESSARY ATTRIBUTES HERE
        #############################################################################

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def accept(self) -> ('RDTSocket', (str, int)):
        """
        Accept a connection. The socket must be bound to an address and listening for 
        connections. The return value is a pair (conn, address) where conn is a new 
        socket object usable to send and receive data on the connection, and address 
        is the address bound to the socket on the other end of the connection.

        This function should be blocking. 
        """
        conn, addr = RDTSocket(self._rate), None
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.receiver.start()
        self.receiver.join()
        if self.receiver.syn == 1:
            print(addr)
            addr = self.receiver.address
            conn._send_to = addr
            conn._recv_from = addr
            self.controller.send_syn()
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return conn, addr

    def connect(self, address: (str, int)):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        #    self.sendto(b'syn', address)
        self._send_to = address
        self._recv_from = address
        self.controller.send_syn()
        if not self.receiver.is_alive():
            self.receiver.start()
        self.receiver.join()
        server_addr = self.receiver.get_address()
        self._send_to = server_addr
        self._recv_from = server_addr

        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def recv(self, bufsize: int) -> bytes:
        """
        Receive data from the socket. 
        The return value is a bytes object representing the data received. 
        The maximum amount of data to be received at once is specified by bufsize. 
        
        Note that ONLY data send by the peer should be accepted.
        In other words, if someone else sends data to you from another address,
        it MUST NOT affect the data returned by this function.
        """
        data = b''
        assert self._recv_from, "Connection not established yet. Use recvfrom instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        if not self.receiver.is_alive():
            self.receiver.start()
        data = self.data
        self.data = bytes()
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        return data

    def send(self, bytes: bytes):
        """
        Send data to the socket. 
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        assert self._send_to, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.sendto(bytes, self._send_to)
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither further sends nor receives are allowed.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        self.send(b'')
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################
        super().close()

    @property
    def send_to(self):
        return self._send_to

    @property
    def recv_from(self):
        return self._recv_from


class Controller:
    def __init__(self, socket: RDTSocket, data: bytes):
        self.socket = socket

        self.send_list = []
        self.data = data
        self.recv_buf = q.PriorityQueue()
        self.window_size = 8

        self.to_ack = 0
        self.tmp = 0
        self.duplicate = 0

        self.received = -1

        self.finish_send = False
        self.finish_receive = False

        self.nxt_ack = q.Queue()
        self.send_buf = q.Queue()

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


class Sender(threading.Thread):
    def __init__(self, socket: RDTSocket, send_buf: q.Queue, ack_list: q.Queue):
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


class Receiver(threading.Thread):
    def __init__(self, socket: RDTSocket, controller: Controller):
        super().__init__()
        self.socket = socket
        self.controller = controller
        self.address = None
        self.syn = 0
        self.fin = 0

    def run(self):
        while True:
            packet, addr = self.socket.recvfrom(2048)
            datagram = Datagram()
            datagram.depack(packet)
            if datagram.TYPE == 1:
                self.address = addr
                self.syn = datagram.SYN
                self.fin = datagram.FIN
                self.controller.recv_pack(datagram)
            if addr != self.socket.recv_from:
                continue

            if datagram.checksum() == datagram.CHECKSUM:
                self.controller.recv_pack(datagram)
            if self.controller.finish():
                break

    def get_address(self):
        return self.address
