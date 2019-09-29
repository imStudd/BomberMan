#!/usr/bin/python3
# -*- coding: utf-8 -*-

import queue
import signal
import sys
import threading

import client
import lobby
import menu
import server
import game


def handler(signum, frame):
    for t in threading.enumerate():
        signal.pthread_kill(t.ident, signal.SIGUSR1)
        signal.pthread_kill(t.ident, signal.SIGUSR2)


if __name__ == "__main__":
    if sys.platform == "linux":
        signal.signal(signal.SIGINT, handler)

    send_q = queue.Queue()
    recv_q = queue.Queue()

    menu.Menu(send_q)

    data = send_q.get()

    if len(data) == 2:
        server.Server(data[0])
        send_q.put(("LOG", data[1]))
        client.Client("127.0.0.1", data[0], send_q, recv_q)
    elif len(data) == 3:
        send_q.put(("LOG", data[2]))
        client.Client(data[0], data[1], send_q, recv_q)
    else:
        sys.exit()

    lobby.Lobby(send_q, recv_q)
