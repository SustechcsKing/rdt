import time
from difflib import Differ
from rdt import RDTSocket

server_addr = ('127.0.0.1', 2130)


def main():
    socket = RDTSocket()
    socket.connect(server_addr)
    echo = b''
    count = 5
    slice_size = 1024
    blocking_send = False

    with open('alice.txt', 'r') as f:
        data = f.read()
        encoded = data.encode()
        assert len(data) == len(encoded)

    '''
    check if your rdt pass either of the two
    mode A may be significantly slower when slice size is small
    '''
    if blocking_send:
        print('transmit in mode A, send & recv in slices')
        slices = [encoded[i * slice_size:i * slice_size + slice_size] for i in range(len(encoded) // slice_size + 1)]
        assert sum([len(slice) for slice in slices]) == len(encoded)

        start = time.perf_counter()
        for i in range(count):  # send 'alice.txt' for count times
            for slice in slices:
                socket.sendto(slice)
                reply = socket.recv(slice_size)
                echo += reply
    else:
        print('transmit in mode B')
        start = time.perf_counter()
        for i in range(count):
            socket.send(encoded)
            while len(echo) < len(encoded) * (i + 1):
                reply = socket.recv(slice_size)
                echo += reply

    socket.close()

    '''
    make sure the following is reachable
    '''

    print(f'transmitted {len(encoded) * count}bytes in {time.perf_counter() - start}s')
    diff = Differ().compare((data * count).splitlines(keepends=True), echo.decode().splitlines(keepends=True))
    for line in diff:
        if not line.startswith('  '):  # check if data is correctly echoed
            print(line)


if __name__ == '__main__':
    main()
