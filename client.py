import sys
import selectors
import types

sel = selectors.DefaultSelector()

def event_loop():
    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                service_connection(key, mask)
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print(f"Sending {data.outb!r} to connection {data.connid}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {recv_data!r} from connection {data.connid}")
            data.recv_total += len(recv_data)
        if data.recv_total >= data.msg_total:
            print(f"Closing connection {data.connid}")
            sel.unregister(sock)
            sock.close()

import socket

def start_connections(host, port, num_conns):
    for i in range(num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {host}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((host, port))
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=1024,
            recv_total=0,
            messages=[b"Message from client."],
            outb=b"",
        )
        sel.register(sock, events, data=data)

if len(sys.argv) != 4:
    print("Usage: python client.py <host> <port> <num_connections>")
    sys.exit(1)

host, port, num_conns = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
start_connections(host, port, num_conns)
event_loop()
