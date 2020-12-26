def segment(data: str, max_length: int):
    data_list = []
    packet_list = []
    length1 = len(data)
    start = 0
    end = max_length
    while (end < length1):
        data_list.append(data[start:end])
        start = end
        end = end + max_length
    end = length1
    data_list.append(data[start:end])
    packet_list.append(Datagram(SYN=1, MAX_LENGTH=max_length, PAYLOAD=data_list[0].encode()))
    for i in range(1, len(data_list) - 1):
        packet_list.append(Datagram(MAX_LENGTH=max_length, PAYLOAD=data_list[i].encode()))
    packet_list.append(Datagram(FIN=1, MAX_LENGTH=max_length, PAYLOAD=data_list[-1].encode()))
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

    def set_seq(self, SEQ):
        self.SEQ = SEQ
        self.packet[1:5] = int.to_bytes(SEQ, length=4, byteorder='big')

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
