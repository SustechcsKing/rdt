def segment(data: str, slice_size: int):
    encoded = data.encode()
    packet_list = []
    slices = [encoded[i * slice_size:i * slice_size + slice_size] for i in range(len(encoded) // slice_size + 1)]
    i = 0
    for slice in slices:
        syn = 0
        fin = 0
        if i == 0:
            syn = 1
        if i == len(slices):
            fin = 1
        packet_list.append(Datagram(SYN=syn, FIN=fin, SEQ=i, PAYLOAD=slice))
        i = i + 1

    return packet_list


class Datagram(object):

    def __init__(self, SYN=0, FIN=0, ACK=0, TYPE=0, SEQ=0, SEQACK=0, MAX_LENGTH=1024, PAYLOAD=b''):
        self.SYN = SYN
        self.FIN = FIN
        self.ACK = ACK
        self.TYPE = TYPE  # Type is add to present whether the packet is a  syn or fin packet
        self.SEQ = SEQ
        self.SEQACK = SEQACK
        self.LEN = len(PAYLOAD)
        self.MAX_LENGTH = MAX_LENGTH
        self.PAYLOAD = PAYLOAD
        self.packet = b''
        self.CHECKSUM = self.checksum()
        self.pack()

    def set_ack(self, ACK):
        self.ACK = ACK
        self.packet[0:1] = int.to_bytes(self.TYPE * 8 + self.SYN * 4 + self.FIN * 2 + self.ACK * 1,
                                        byteorder='big', length=1)

    def set_type(self, TYPE):
        self.TYPE = TYPE
        self.packet[0:1] = int.to_bytes(self.TYPE * 8 + self.SYN * 4 + self.FIN * 2 + self.ACK * 1,
                                        byteorder='big', length=1)

    def set_seqack(self, SEQACK):
        self.SEQACK = SEQACK
        self.packet[5:9] = int.to_bytes(SEQACK, length=4, byteorder='big')

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
        send_data = int.to_bytes(self.TYPE * 8 + self.ACK * 4 + self.FIN * 2 + self.SYN * 1,
                                 byteorder='big', length=1)
        send_data = send_data + self.SEQ.to_bytes(4, "big")
        send_data = send_data + self.SEQACK.to_bytes(4, "big")
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
        self.SEQ = int.from_bytes(data[1:5], "big")
        self.SEQACK = int.from_bytes(data[5:9], "big")
        self.LEN = int.from_bytes(data[9:13], "big")
        self.CHECKSUM = int.from_bytes(data[13:15], "big")
        self.PAYLOAD = data[15:]


if __name__ == "__main__":
    a = "1234512345123451234512"
    b = 'iagsdgajsgadsda'
    dg = Datagram(PAYLOAD=a.encode())
    print(dg.packet)
    a2 = segment(a, 8)
    for item in a2:
        print(item.packet)
        dg.depack(item.packet)
        print(dg.SEQ)
        print(dg.PAYLOAD.decode())
        print(dg.LEN)
