def segment(data: bytes, slice_size: int, pre=0):
    packet_list = []
    slices = [data[i * slice_size:i * slice_size + slice_size] for i in range(len(data) // slice_size + 1)]
    i = 0
    for slice in slices:
        syn = 0
        fin = 0
        if i == 0:
            syn = 1
        if i == len(slices):
            fin = 1
        packet_list.append(Datagram(syn=syn, fin=fin, SEQ=pre + i, PAYLOAD=slice))
        i = i + 1

    return packet_list


class Datagram(object):

    def __init__(self, syn=0, fin=0, ack=0, type=0, SEQ=0, SACK=0, MAX_LENGTH=1024, PAYLOAD=b''):
        self.SYN = syn
        self.FIN = fin
        self.ACK = ack
        self.TYPE = type  # Type is add to present whether the datagram is a  syn or fin datagram
        self.SEQ = SEQ
        self.SACK = SACK
        self.LEN = len(PAYLOAD)
        self.MAX_LENGTH = MAX_LENGTH
        self.PAYLOAD = PAYLOAD
        self.packet = b''
        self.CHECKSUM = self.checksum()
        self.pack()

    def set_ack(self, ACK):
        self.ACK = ACK
        self.pack()

    def set_type(self, TYPE):
        self.TYPE = TYPE
        self.pack()

    def set_sack(self, sack):
        self.SACK = sack
        self.pack()

    def checksum(self):
        # Input: data
        # Output: checksum
        checksum = 0
        for byte in self.PAYLOAD:
            checksum += byte
            checksum %= 65536
        return ~checksum & 0xffff

    def pack(self):
        # Input: a str with LEN length
        # Output: the package with header and data
        sum = self.TYPE * 8 + self.ACK * 4 + self.FIN * 2 + self.SYN * 1
        send_data = int.to_bytes(sum, 1, 'big', signed=True)
        send_data = send_data + self.SEQ.to_bytes(4, "big")
        send_data = send_data + self.SACK.to_bytes(4, "big")
        send_data = send_data + self.LEN.to_bytes(4, "big")
        send_data = send_data + self.CHECKSUM.to_bytes(2, "big")
        send_data = send_data + self.PAYLOAD
        self.packet = send_data

    def depack(self, data: bytes):
        # Input: data
        # Output: If the data satisfy the checksum,
        # The inf and header
        # header_list = []
        pre = int.from_bytes(data[0:1], "big")
        self.SYN = pre % 2
        pre //= 2
        self.FIN = pre % 2
        pre //= 2
        self.ACK = pre % 2
        pre //= 2
        self.TYPE = pre
        self.SEQ = int.from_bytes(data[1:5], "big")
        self.SACK = int.from_bytes(data[5:9], "big")
        self.LEN = int.from_bytes(data[9:13], "big")
        self.CHECKSUM = int.from_bytes(data[13:15], "big")
        self.PAYLOAD = data[15:]
