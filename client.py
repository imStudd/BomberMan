# -*- coding: utf-8 -*-

import queue
import select
import signal
import socket
import sys
import threading


class Client:
    def __init__(self, host, port, sq, rq):
        self._host = host
        self._port = port

        self._connect()
        self._send_q = sq
        self._recv_q = rq

        if sys.platform == "linux":
            signal.signal(signal.SIGUSR2, self._handler)

        self._connected = threading.Event()
        self._client_thread = threading.Thread(target=self._receive_data)
        self._connected.set()
        self._client_thread.start()

    def _handler(self, signum, frame):
        self._connected.clear()

    def _connect(self):
        for addrinfo in socket.getaddrinfo(self._host, self._port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            ai_family, sock_type, _, _, sock_addr = addrinfo

            try:
                sock = socket.socket(ai_family, sock_type)
            except socket.error as ex:
                print("(!) sock: %s\n" % ex)
            except Exception as ex:
                print("(!) sock: %s\n" % ex)

            try:
                sock.connect(sock_addr)
            except socket.error as ex:
                print("(!) connect: %s\n" % ex)
                exit(1)

            sock.setblocking(0)

            if self._host != sock_addr[0]:
                print("(+) Connected to %s(%s):%d\n" %
                      (self._host, sock_addr[0], self._port))
            else:
                print("(+) Connected to %s:%d\n" % (self._host, self._port))

        self._sock = sock

    def _sending_data_proccess(self, code, data):
        try:
            buf = code + " " + data + "\n"

            self._sock.sendall(buf.encode())
        except Exception as ex:
            print("(!) sending data proccess: %s\n" % ex)

    def _receive_data(self):
        while self._connected.is_set():
            try:
                readable, _, _ = select.select([self._sock], [], [], 0.05)
                for s in readable:
                    buf = s.recv(10240)

                    if len(buf) == 0:
                        self._connected.clear()
                        break

                    self._received_data_proccess(buf)

                if not self._send_q.empty():
                    d = self._send_q.get()
                    if d[0] == "QUT":
                        self._connected.clear()
                    self._sending_data_proccess(d[0], d[1])

            except select.error as ex:
                print("(!) select: %s\n" % ex)
                self._sending_data_proccess("QUT", "")
                self._connected.clear()

        self._recv_q.put("EXT")
        print("(*) Disconnecting to server...\n")
        self._sock.close()
        print("(-) Disconnected\n")

    def _received_data_proccess(self, data):
        try:
            # print("#DEBUG Client# - ", data)

            data = data.decode().splitlines()

            for buf in data:
                buf = buf.strip().split(" ")

                if buf[0] == "ERR":
                    if "FULL" in buf[1]:
                        print("Server full, closing connection with server !\n")
                    if "UNAVAILABLE" in buf[1]:
                        print("Nickname unavailable\n")
                    self._connected.clear()

                else:
                    self._recv_q.put(buf)

        except Exception as ex:
            print("(!) received data process: %s\n" % ex)
