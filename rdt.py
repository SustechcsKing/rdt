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

