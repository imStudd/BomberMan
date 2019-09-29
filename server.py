#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import random
import select
import signal
import socket
import sys
import threading
import time
from math import ceil
from urllib.request import urlopen

MAX_CLIENTS = 32
EXPLOSION_TIMER = 0.6
START_TIMER = 0.5


class Server:
    def __init__(self, port=5555, main=False):
        self._sock = self._listener(port)

        self._settings = [1, 1, 0, 1500, 1]
        self._bonus_setting = [50, 1, 1, 1]
        self._bonus_list = [0, 1, 2]

        self._clients_data_keys = ["pseudonym", "x", "y",
                                   "bomb", "timer", "kill", "speed", "power", "life"]
        self._clients_data = {}
        self._clients_sock = {self._sock: -1}
        self._bomb_list = {}
        self._explosions = {}

        self._alive = 0
        self._ready = False

        self._get_maps = [m for m in os.listdir("ressources/maps/") if os.path.isfile(
            os.path.join("ressources/maps/", m)) and m[-4:] == ".txt"]
        self._get_spawns = [s for s in os.listdir("ressources/spawns/") if os.path.isfile(
            os.path.join("ressources/spawns/", s)) and s[-4:] == ".txt"]

        self._actual = 0
        self._map = open("ressources/maps/" +
                         self._get_maps[0], "rt").read().replace("\n", " ")
        self._spawns = open("ressources/spawns/" +
                            self._get_spawns[0], "rt").readlines()
        self._load_spawns()

        self._started = threading.Event()
        self._started.set()

        if not main:
            if sys.platform == "linux":
                signal.signal(signal.SIGUSR1, self._handler)
            self._server_thread = threading.Thread(target=self._start_server)
            self._server_thread.start()
        else:
            signal.signal(signal.SIGINT, self._handler)
            self._start_server()

    def _handler(self, signum, frame):
        self._started.clear()

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(('1.1.1.1', 80))
            local = s.getsockname()[0]
            s.close()
        except Exception as ex:
            print(ex)
            local = "N/A"

        try:
            ipv4 = urlopen("https://api.ipify.org/",
                             timeout=5).read().decode()
        except:
            ipv4 = "N/A"

        try:
            ipv6 = urlopen("https://api6.ipify.org/",
                             timeout=5).read().decode()
        except:
            ipv6 = "N/A"

        return [local, ipv4, ipv6]

    def _listener(self, port):
        for addrinfo in socket.getaddrinfo(None, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            ai_family, _, _, _, _ = addrinfo

            try:
                sock = socket.socket(ai_family, socket.SOCK_STREAM, 0)
            except socket.error as ex:
                print("[!] socket: %s\n" % ex)
                exit(1)

            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error as ex:
                print("[!] setsockopt: %s\n" % ex)
                exit(1)

            sock.setblocking(0)

            try:
                sock.bind(('', port))
            except socket.error as ex:
                print("[!] bind: %s\n" % ex)
                exit(1)

            try:
                sock.listen(8)
            except socket.error as ex:
                print("[!] listen: %s\n" % ex)
                exit(1)

        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

        ip = self._get_ip()
        if ip is not None:
            print("[*] Local IP: %s\n[*] Public IPV4: %s\n[*] Public IPV6: %s" % (ip[0], ip[1], ip[2]))
        print("[*] Listening on port %d...\n" % port)
        return sock

    def _start_server(self):
        while self._started.is_set():
            try:
                readable, _, _ = select.select(self._clients_sock, [], [], 1)
                for s in readable:
                    if s == self._sock:
                        if not self._ready:
                            try:
                                conn, addr = self._sock.accept()

                                if len(self._clients_sock) - 1 == MAX_CLIENTS:
                                    conn.sendall(b"ERR FUL\n")
                                    print("[!] Server full !\n")
                                    conn.close()
                                else:
                                    self._clients_sock[conn] = (
                                        -len(self._clients_sock) - 1)

                                    print("[+] New client connected @ %s:%d \n" %
                                          (str(addr[0]), addr[1]))
                                    print("[*] " + str(len(self._clients_sock) - 1) +
                                          " / " + str(MAX_CLIENTS) + " client(s) connected\n")
                            except socket.error as ex:
                                print("[!] accept error %s\n" % ex)

                        else:
                            conn, addr = self._sock.accept()
                            conn.sendall(b"ERR FUL\n")
                            conn.close()

                    else:
                        buf = s.recv(1024)

                        index = self._clients_sock[s]

                        if len(buf) == 0:
                            if index in self._clients_data:
                                if self._clients_data[index]["life"]:
                                    self._alive -= 1
                            self._remove_client(s)
                            self._sending_data_process("LFT", str(index))
                            if self._ready:
                                if self._alive <= 1 and self._alive < len(self._clients_data):
                                    self._ending()
                                if not len(self._clients_data):
                                    self._restarting()
                            break

                        self._received_data_procces(s, buf)
            except select.error as ex:
                print("[!] select: %s\n" % ex)
                self._started.clear()

        print("[*] Stopping Server...\n")
        self._sock.close()
        print("[-] Server stopped\n")

    def _sending_data_process(self, code, data):
        try:
            buf = code + " " + str(data) + "\n"

            for key, values in self._clients_sock.items():
                if values != -1:
                    key.sendall(buf.encode())

        except Exception as ex:
            print("[!] sending data process: %s\n" % ex)

    def _received_data_procces(self, client, data):
        try:
            index_client = self._clients_sock[client]

            # print("#DEBUG Server# - ", index_client, data)

            data = data.decode().splitlines()
            for buf in data:
                buf = buf.strip().split(" ")

                if buf[0] == "LOG":
                    for key, values in self._clients_data.items():
                        if values["pseudonym"] == buf[1]:
                            client.sendall(b"ERR UNAVAILABLE\n")
                            return

                    if len(self._clients_data) < 1:
                        n = 0
                    else:
                        n = max(self._clients_data) + 1
                    self._clients_sock[client] = n

                    new_client = [buf[1], self._game_spawns[n % len(self._game_spawns)][0], self._game_spawns[n % len(
                        self._game_spawns)][1], self._settings[0], time.time(), 0, 0.35 - 0.02 * self._settings[2], self._settings[1], self._settings[4]]
                    self._clients_data[n] = dict(
                        zip(self._clients_data_keys, new_client))
                    client.sendall(("CND %d\n" % n).encode())
                    self._alive += 1

                    b = str(n) + " " + buf[1]
                    self._sending_data_process("ARV", b)
                    b = str(len(self._clients_data) - 1)
                    if n > 0:
                        for key, values in self._clients_data.items():
                            if key != n:
                                b += " " + str(key) + " " + values["pseudonym"]
                        client.sendall(("LST " + b + "\n").encode())

                    [c for c in self._settings]
                    client.sendall(("ACT " + str(self._actual) + " " +
                                    self._get_maps[self._actual].replace(".txt", "") + "\n").encode())
                    client.sendall(("CFG " + " ".join(map(str, self._settings)) +
                                    " " + " ".join(map(str, self._bonus_setting)) + "\n").encode())

                    print("[*] " + str(len(self._clients_data)) + " / " +
                          str(len(self._clients_sock) - 1) + " client(s) logged\n")

                elif buf[0] == "MOV" and self._ready:
                    if self._clients_data[index_client]["life"]:
                        c_x, c_y = self._clients_data[index_client]["x"], self._clients_data[index_client]["y"]
                        if (time.time() - self._clients_data[index_client]["timer"]) >= self._clients_data[index_client]["speed"]:
                            self._clients_data[index_client]["timer"] = time.time(
                            )

                            if (buf[1] == "L"):
                                if (c_x > 0):
                                    p = self._game_map[(c_y + 1)][c_x - 1]
                                    if (p == 0 or p >= 4):
                                        if p >= 5:
                                            b = ceil((p - 5) * 100)
                                            if b == 0:
                                                self._clients_data[index_client]["bomb"] += 1
                                            if b == 1:
                                                if self._clients_data[index_client]["power"] + 1 <= max(self._game_map[0][0], self._game_map[0][1]):
                                                    self._clients_data[index_client]["power"] += 1
                                            if b == 2:
                                                if self._clients_data[index_client]["speed"] - 0.02 >= 0.05:
                                                    self._clients_data[index_client]["speed"] -= 0.02
                                                    self._clients_data[index_client]["speed"] = round(
                                                        self._clients_data[index_client]["speed"], 2)
                                            self._sending_data_process(
                                                "GOT", str(c_x - 1) + " " + str(c_y))

                                        if (c_x - 1, c_y) in self._explosions:
                                            killer = self._explosions[(
                                                c_x - 1, c_y)]
                                            self._clients_data[index_client]["life"] -= 1
                                            if not self._clients_data[index_client]["life"]:
                                                self._sending_data_process("DTH", str(
                                                    index_client) + " " + str(killer))
                                                self._alive -= 1
                                            else:
                                                self._clients_data[index_client]["x"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][0]
                                                self._clients_data[index_client]["y"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][1]
                                                self._game_map[self._game_spawns[index_client % len(
                                                    self._game_spawns)][1] + 1][self._game_spawns[index_client % len(self._game_spawns)][0]] = 4.0 + index_client / 100
                                                pos = str(index_client) + " " + str(self._clients_data[index_client]["x"]) + " " + str(
                                                    self._clients_data[index_client]["y"])
                                                self._sending_data_process(
                                                    "POS", pos)
                                                if index_client != killer:
                                                    self._clients_data[killer]["kill"] += 1
                                                o = self._game_map[(
                                                    c_y + 1)][c_x]
                                                if o != 3 and o == 4.0 + index_client / 100:
                                                    self._game_map[(
                                                        c_y + 1)][c_x] = 0

                                            if self._alive <= 1 and self._alive < len(self._clients_data):
                                                self._ending()

                                        else:
                                            self._clients_data[index_client]["x"] -= 1

                                            o = self._game_map[(c_y + 1)][c_x]
                                            if o != 3 and o == 4.0 + index_client / 100:
                                                self._game_map[(
                                                    c_y + 1)][c_x] = 0
                                            self._game_map[(
                                                c_y + 1)][c_x - 1] = 4.0 + index_client / 100
                                    else:
                                        return
                                else:
                                    return

                            elif (buf[1] == "R"):
                                if (c_x < self._game_map[0][0] - 1):
                                    p = self._game_map[(c_y + 1)][c_x + 1]
                                    if (p == 0 or p >= 4):
                                        if p >= 5:
                                            b = ceil((p - 5) * 100)
                                            if b == 0:
                                                self._clients_data[index_client]["bomb"] += 1
                                            if b == 1:
                                                if self._clients_data[index_client]["power"] + 1 <= max(self._game_map[0][0], self._game_map[0][1]):
                                                    self._clients_data[index_client]["power"] += 1
                                            if b == 2:
                                                if self._clients_data[index_client]["speed"] - 0.02 >= 0.05:
                                                    self._clients_data[index_client]["speed"] -= 0.02
                                                    self._clients_data[index_client]["speed"] = round(
                                                        self._clients_data[index_client]["speed"], 2)
                                            self._sending_data_process(
                                                "GOT", str(c_x + 1) + " " + str(c_y))

                                        if (c_x + 1, c_y) in self._explosions:
                                            killer = self._explosions[(
                                                c_x + 1, c_y)]
                                            self._clients_data[index_client]["life"] -= 1
                                            if not self._clients_data[index_client]["life"]:
                                                self._sending_data_process("DTH", str(
                                                    index_client) + " " + str(killer))
                                                self._alive -= 1
                                            else:
                                                self._clients_data[index_client]["x"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][0]
                                                self._clients_data[index_client]["y"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][1]
                                                self._game_map[self._game_spawns[index_client % len(
                                                    self._game_spawns)][1] + 1][self._game_spawns[index_client % len(self._game_spawns)][0]] = 4.0 + index_client / 100
                                                pos = str(index_client) + " " + str(self._clients_data[index_client]["x"]) + " " + str(
                                                    self._clients_data[index_client]["y"])
                                                self._sending_data_process(
                                                    "POS", pos)
                                                if index_client != killer:
                                                    self._clients_data[killer]["kill"] += 1
                                                o = self._game_map[(
                                                    c_y + 1)][c_x]
                                                if o != 3 and o == 4.0 + index_client / 100:
                                                    self._game_map[(
                                                        c_y + 1)][c_x] = 0

                                            if self._alive <= 1 and self._alive < len(self._clients_data):
                                                self._ending()

                                        else:
                                            self._clients_data[index_client]["x"] += 1

                                            o = self._game_map[(c_y + 1)][c_x]
                                            if o != 3 and o == 4.0 + index_client / 100:
                                                self._game_map[(
                                                    c_y + 1)][c_x] = 0
                                            self._game_map[(
                                                c_y + 1)][c_x + 1] = 4.0 + index_client / 100
                                    else:
                                        return
                                else:
                                    return

                            elif (buf[1] == "B"):
                                if (c_y < self._game_map[0][1] - 1):
                                    p = self._game_map[(c_y + 1) + 1][c_x]
                                    if (p == 0 or p >= 4):
                                        if p >= 5:
                                            b = ceil((p - 5) * 100)
                                            if b == 0:
                                                self._clients_data[index_client]["bomb"] += 1
                                            if b == 1:
                                                if self._clients_data[index_client]["power"] + 1 <= max(self._game_map[0][0], self._game_map[0][1]):
                                                    self._clients_data[index_client]["power"] += 1
                                            if b == 2:
                                                if self._clients_data[index_client]["speed"] - 0.02 >= 0.05:
                                                    self._clients_data[index_client]["speed"] -= 0.02
                                                    self._clients_data[index_client]["speed"] = round(
                                                        self._clients_data[index_client]["speed"], 2)
                                            self._sending_data_process(
                                                "GOT", str(c_x) + " " + str(c_y + 1))

                                        if (c_x, c_y + 1) in self._explosions:
                                            killer = self._explosions[(
                                                c_x, c_y + 1)]
                                            self._clients_data[index_client]["life"] -= 1
                                            if not self._clients_data[index_client]["life"]:
                                                self._sending_data_process("DTH", str(
                                                    index_client) + " " + str(killer))
                                                self._alive -= 1
                                            else:
                                                self._clients_data[index_client]["x"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][0]
                                                self._clients_data[index_client]["y"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][1]
                                                self._game_map[self._game_spawns[index_client % len(
                                                    self._game_spawns)][1] + 1][self._game_spawns[index_client % len(self._game_spawns)][0]] = 4.0 + index_client / 100
                                                pos = str(index_client) + " " + str(self._clients_data[index_client]["x"]) + " " + str(
                                                    self._clients_data[index_client]["y"])
                                                self._sending_data_process(
                                                    "POS", pos)
                                                if index_client != killer:
                                                    self._clients_data[killer]["kill"] += 1
                                                o = self._game_map[(
                                                    c_y + 1)][c_x]
                                                if o != 3 and o == 4.0 + index_client / 100:
                                                    self._game_map[(
                                                        c_y + 1)][c_x] = 0

                                            if self._alive <= 1 and self._alive < len(self._clients_data):
                                                self._ending()

                                        else:
                                            self._clients_data[index_client]["y"] += 1

                                            o = self._game_map[(c_y + 1)][c_x]
                                            if o != 3 and o == 4.0 + index_client / 100:
                                                self._game_map[(
                                                    c_y + 1)][c_x] = 0
                                            self._game_map[(
                                                c_y + 1) + 1][c_x] = 4.0 + index_client / 100
                                    else:
                                        return
                                else:
                                    return

                            elif (buf[1] == "T"):
                                if (c_y > 0):
                                    p = self._game_map[(c_y + 1) - 1][c_x]
                                    if (p == 0 or p >= 4):
                                        if p >= 5:
                                            b = ceil((p - 5) * 100)
                                            if b == 0:
                                                self._clients_data[index_client]["bomb"] += 1
                                            if b == 1:
                                                if self._clients_data[index_client]["power"] + 1 <= max(self._game_map[0][0], self._game_map[0][1]):
                                                    self._clients_data[index_client]["power"] += 1
                                            if b == 2:
                                                if self._clients_data[index_client]["speed"] - 0.02 >= 0.05:
                                                    self._clients_data[index_client]["speed"] -= 0.02
                                                    self._clients_data[index_client]["speed"] = round(
                                                        self._clients_data[index_client]["speed"], 2)
                                            self._sending_data_process(
                                                "GOT", str(c_x) + " " + str(c_y - 1))

                                        if (c_x, c_y - 1) in self._explosions:
                                            killer = self._explosions[(
                                                c_x, c_y - 1)]
                                            self._clients_data[index_client]["life"] -= 1
                                            if not self._clients_data[index_client]["life"]:
                                                self._sending_data_process("DTH", str(
                                                    index_client) + " " + str(killer))
                                                self._alive -= 1
                                            else:
                                                self._clients_data[index_client]["x"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][0]
                                                self._clients_data[index_client]["y"] = self._game_spawns[index_client % len(
                                                    self._game_spawns)][1]
                                                self._game_map[self._game_spawns[index_client % len(
                                                    self._game_spawns)][1] + 1][self._game_spawns[index_client % len(self._game_spawns)][0]] = 4.0 + index_client / 100
                                                pos = str(index_client) + " " + str(self._clients_data[index_client]["x"]) + " " + str(
                                                    self._clients_data[index_client]["y"])
                                                self._sending_data_process(
                                                    "POS", pos)
                                                if index_client != killer:
                                                    self._clients_data[killer]["kill"] += 1
                                                o = self._game_map[(
                                                    c_y + 1)][c_x]
                                                if o != 3 and o == 4.0 + index_client / 100:
                                                    self._game_map[(
                                                        c_y + 1)][c_x] = 0

                                            if self._alive <= 1 and self._alive < len(self._clients_data):
                                                self._ending()

                                        else:
                                            self._clients_data[index_client]["y"] -= 1

                                            o = self._game_map[(c_y + 1)][c_x]
                                            if o != 3 and o == 4.0 + index_client / 100:
                                                self._game_map[(
                                                    c_y + 1)][c_x] = 0
                                            self._game_map[(
                                                c_y + 1) - 1][c_x] = 4.0 + index_client / 100
                                    else:
                                        return
                                else:
                                    return

                            p = str(index_client) + " " + str(self._clients_data[index_client]["x"]) + " " + str(
                                self._clients_data[index_client]["y"])
                            self._sending_data_process("POS", p)

                elif buf[0] == "BMB" and self._ready:
                    if self._clients_data[index_client]["life"]:
                        c_x, c_y = self._clients_data[index_client]["x"], self._clients_data[index_client]["y"]
                        p = self._game_map[c_y + 1][c_x]
                        if self._clients_data[index_client]["bomb"] > 0 and (p == 0 or p >= 4.):
                            self._game_map[c_y + 1][c_x] = 3
                            b = str(c_x) + " " + str(c_y) + " " + \
                                str(self._clients_data[index_client]["power"])
                            self._sending_data_process("BMB", b)
                            self._clients_data[index_client]["bomb"] -= 1

                            self._bomb_list[(c_x, c_y)] = (
                                index_client, self._clients_data[index_client]["power"])
                            threading.Thread(
                                target=self._bomb_timer, args=((c_x, c_y),)).start()

                elif buf[0] == "RST" and self._ready and index_client == min(self._clients_data):
                    self._restarting()

                elif buf[0] == "RDY" and not self._ready and index_client == min(self._clients_data):
                    self._load_map()
                    self._sending_data_process("MAP", self._map)
                    self._ready = True

                    for key, values in self._clients_sock.items():
                        if values < -1:
                            self._remove_client(client)

                    a = str(len(self._clients_data))
                    for key, values in self._clients_data.items():
                        a += " " + str(key) + " " + \
                            str(values["x"]) + " " + str(values["y"])
                    self._sending_data_process("ALL", a)
                    self._sending_data_process("STR", START_TIMER)
                    # time.sleep(START_TIMER)
                    print("[*] Starting Game\n")

                elif buf[0] == "QUT":
                    if self._clients_data[index_client]["life"]:
                        self._alive -= 1
                    self._remove_client(client)
                    self._sending_data_process("LFT", str(index_client))
                    if self._ready:
                        if self._alive <= 1 and self._alive < len(self._clients_data):
                            self._ending()
                    if self._ready and len(self._clients_data) == 0:
                        self._restarting()

                elif buf[0] == "MSG" and not self._ready:
                    m = str(index_client) + " "
                    for b in buf[1:]:
                        m += b + " "
                    self._sending_data_process("MSG", m)

                elif buf[0] == "NXT" and not self._ready and index_client == min(self._clients_data):
                    self._actual = (self._actual + 1) % len(self._get_maps)
                    self._map = open(
                        "ressources/maps/" + self._get_maps[self._actual], "rt").read().replace("\n", " ")
                    self._spawns = open(
                        "ressources/spawns/" + self._get_spawns[self._actual], "rt").readlines()
                    self._sending_data_process("ACT", str(
                        self._actual) + " " + self._get_maps[self._actual].replace(".txt", ""))
                    self._load_spawns()
                    print("[*] Map changed\n")

                elif buf[0] == "PRV" and not self._ready and index_client == min(self._clients_data):
                    if self._actual - 1 < 0:
                        self._actual = len(self._get_maps) - 1
                    else:
                        self._actual -= 1
                    self._map = open(
                        "ressources/maps/" + self._get_maps[self._actual], "rt").read().replace("\n", " ")
                    self._spawns = open(
                        "ressources/spawns/" + self._get_spawns[self._actual], "rt").readlines()
                    self._sending_data_process("ACT", str(
                        self._actual) + " " + self._get_maps[self._actual].replace(".txt", ""))
                    self._load_spawns()
                    print("[*] Map changed\n")

                elif buf[0] == "SET" and not self._ready and index_client == min(self._clients_data):
                    for i in range(1, len(buf)):
                        self._settings[i - 1] = int(buf[i])
                    for key, values in self._clients_data.items():
                        self._clients_data[key].update({"x": self._game_spawns[key % len(self._game_spawns)][0],
                                                        "y": self._game_spawns[key % len(self._game_spawns)][1],
                                                        "bomb": self._settings[0],
                                                        "timer": time.time(),
                                                        "kill": 0,
                                                        "speed": 0.35 - 0.02 * self._settings[2],
                                                        "power": self._settings[1],
                                                        "life": self._settings[4]})
                    print("[*] Settings changed\n")
                    self._sending_data_process("CFG", " ".join(
                        map(str, self._settings)) + " " + " ".join(map(str, self._bonus_setting)))

                elif buf[0] == "CHA" and not self._ready and index_client == min(self._clients_data):
                    self._bonus_list.clear()
                    self._bonus_list.extend([0] * int(buf[2]))
                    self._bonus_list.extend([1] * int(buf[3]))
                    self._bonus_list.extend([2] * int(buf[4]))
                    if len(self._bonus_list) > 0:
                        self._bonus_setting[0] = int(buf[1])
                    else:
                        self._bonus_setting[0] = 0
                    random.shuffle(self._bonus_list)
                    self._sending_data_process("CFG", " ".join(
                        map(str, self._settings)) + " " + " ".join(map(str, self._bonus_setting)))

                # else:
                #     print("[!] UNTREATED MESSAGE: %s\n " % buf)

        except Exception as ex:
            print("[!] received data process: %s\n" % ex)

    def _remove_client(self, client):
        c = client.getpeername()

        i = self._clients_sock[client]
        if i in self._clients_data:
            self._clients_data.pop(i)

        print("[*] Closing connection with %s:%d...\n" % (c[0], c[1]))
        if not client._closed:
            client.close()
        self._clients_sock.pop(client)

        print("[-] Connection closed\n")

    def _load_map(self):
        gmap = self._map
        gmap = gmap.split()
        game_map = [[int(gmap[0]), int(gmap[1])]]
        line = []
        for x in range(2, len(gmap)):
            if (x - 2 > 0) and (x - 2) % int(gmap[0]) == 0:
                game_map.append(line)
                line = []
            line.append(float(gmap[x]))
        game_map.append(line)
        self._game_map = game_map

        for key in self._clients_data.keys():
            self._game_map[self._game_spawns[key % len(
                self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100

    def _load_spawns(self):
        self._game_spawns = []
        for i in range(len(self._spawns)):
            self._game_spawns.append(list(map(int, self._spawns[i].split())))

        for key in self._clients_data.keys():
            self._clients_data[key].update({"x": self._game_spawns[key % len(self._game_spawns)][0],
                                            "y": self._game_spawns[key % len(self._game_spawns)][1]})

    def _bomb_timer(self, bomb):
        time.sleep(self._settings[3] / 1000)
        if bomb in self._bomb_list:
            self._destroy_blocks(bomb)

    def _explosions_duration(self, bomb):
        time.sleep(0.6)
        if bomb in self._explosions:
            self._explosions.pop(bomb)

    def _destroy_blocks(self, bomb):
        buf = ""
        broke = []
        killer = self._bomb_list[bomb][0]

        def destruction(bomb):
            nonlocal buf, broke, killer

            self._sending_data_process(
                "EXP", str(bomb[0]) + " " + str(bomb[1]))
            self._game_map[bomb[1] + 1][bomb[0]] = 2
            broke.append((bomb[0], bomb[1] + 1, 0))
            self._clients_data[self._bomb_list[bomb][0]]["bomb"] += 1

            self._explosions[bomb] = killer
            threading.Thread(target=self._explosions_duration,
                             args=(bomb,)).start()

            for key, values in self._clients_data.items():
                if values["life"]:
                    if (values["x"], values["y"]) == (bomb[0], bomb[1]):
                        b = str(key) + " " + str(self._bomb_list[bomb][0])
                        self._clients_data[key]["life"] -= 1
                        if not self._clients_data[key]["life"]:
                            self._sending_data_process("DTH", b)
                            self._alive -= 1
                        else:
                            self._clients_data[key]["x"] = self._game_spawns[key % len(
                                self._game_spawns)][0]
                            self._clients_data[key]["y"] = self._game_spawns[key % len(
                                self._game_spawns)][1]
                            self._game_map[self._game_spawns[key % len(
                                self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100
                            broke.append((values["x"], values["y"], 0))
                            pos = str(
                                key) + " " + str(self._clients_data[key]["x"]) + " " + str(self._clients_data[key]["y"])
                            self._sending_data_process("POS", pos)
                        if key != killer:
                            self._clients_data[killer]["kill"] += 1
                        self._game_map[bomb[1] + 1][bomb[0]] = 0

            for i in range(1, self._bomb_list[bomb][1] + 1):
                if bomb[0] + i < self._game_map[0][0]:
                    block = self._game_map[bomb[1] + 1][bomb[0] + i]
                    self._explosions[(bomb[0] + i, bomb[1])] = killer
                    threading.Thread(target=self._explosions_duration, args=(
                        (bomb[0] + i, bomb[1]),)).start()

                    if block >= 4 and block < 5:
                        p = ceil((block - 4) * 100)
                        self._clients_data[p]["life"] -= 1
                        if not self._clients_data[p]["life"]:
                            self._sending_data_process("DTH", str(
                                p) + " " + str(self._bomb_list[bomb][0]))
                            self._alive -= 1
                        else:
                            self._clients_data[p]["x"] = self._game_spawns[p % len(
                                self._game_spawns)][0]
                            self._clients_data[p]["y"] = self._game_spawns[p % len(
                                self._game_spawns)][1]
                            self._game_map[self._game_spawns[p % len(
                                self._game_spawns)][1] + 1][self._game_spawns[p % len(self._game_spawns)][0]] = 4.0 + p / 100
                            broke.append((values["x"], values["y"], 0))
                            pos = str(
                                p) + " " + str(self._clients_data[p]["x"]) + " " + str(self._clients_data[p]["y"])
                            self._sending_data_process("POS", pos)
                        if p != killer:
                            self._clients_data[killer]["kill"] += 1
                        for key, values in self._clients_data.items():
                            if key != p and values["life"]:
                                if (values["x"], values["y"]) == (bomb[0] + i, bomb[1]):
                                    b = str(key) + " " + \
                                        str(self._bomb_list[bomb][0])
                                self._clients_data[key]["life"] -= 1
                                if not self._clients_data[key]["life"]:
                                    self._sending_data_process("DTH", b)
                                    self._alive -= 1
                                else:
                                    self._clients_data[key]["x"] = self._game_spawns[key % len(
                                        self._game_spawns)][0]
                                    self._clients_data[key]["y"] = self._game_spawns[key % len(
                                        self._game_spawns)][1]
                                    pos = str(
                                        key) + " " + str(self._clients_data[key]["x"]) + " " + str(self._clients_data[key]["y"])
                                    self._game_map[self._game_spawns[key % len(
                                        self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100
                                    broke.append((values["x"], values["y"], 0))
                                    self._sending_data_process("POS", pos)
                                if key != killer:
                                    self._clients_data[killer]["kill"] += 1
                        self._game_map[bomb[1] + 1][bomb[0] + i] = 0

                    if block >= 5:
                        self._sending_data_process("GOT", str(
                            bomb[0] + i) + " " + str(bomb[1]))
                        self._game_map[(bomb[1] + 1)][bomb[0] + i] = 0

                    if block == 1:
                        buf += str((bomb[0] + i)) + " " + str(bomb[1]) + " "

                        r = self._bonus_setting[0] / 10
                        r = random.uniform(-(9 - r), r)
                        if r:
                            r = random.choice(self._bonus_list)
                            self._sending_data_process("BNS", str(
                                bomb[0] + i) + " " + str(bomb[1]) + " " + str(r))
                            broke.append(
                                (bomb[0] + i, bomb[1] + 1, 5.0 + r / 100))
                        else:
                            broke.append((bomb[0] + i, bomb[1] + 1, 0))
                        break
                    elif block == 3:
                        destruction((bomb[0] + i, bomb[1]))
                        break
                    elif block != 0:
                        break

            for i in range(1, self._bomb_list[bomb][1] + 1):
                if bomb[0] - i >= 0:
                    block = self._game_map[bomb[1] + 1][bomb[0] - i]
                    self._explosions[(bomb[0] - i, bomb[1])] = killer
                    threading.Thread(target=self._explosions_duration, args=(
                        (bomb[0] - i, bomb[1]),)).start()

                    if block >= 4 and block < 5:
                        p = ceil((block - 4) * 100)
                        self._clients_data[p]["life"] -= 1
                        if not self._clients_data[p]["life"]:
                            self._sending_data_process("DTH", str(
                                p) + " " + str(self._bomb_list[bomb][0]))
                            self._alive -= 1
                        else:
                            self._clients_data[p]["x"] = self._game_spawns[p % len(
                                self._game_spawns)][0]
                            self._clients_data[p]["y"] = self._game_spawns[p % len(
                                self._game_spawns)][1]
                            self._game_map[self._game_spawns[p % len(
                                self._game_spawns)][1] + 1][self._game_spawns[p % len(self._game_spawns)][0]] = 4.0 + p / 100
                            broke.append((values["x"], values["y"], 0))
                            pos = str(
                                p) + " " + str(self._clients_data[p]["x"]) + " " + str(self._clients_data[p]["y"])
                            self._sending_data_process("POS", pos)
                        if p != killer:
                            self._clients_data[killer]["kill"] += 1
                        for key, values in self._clients_data.items():
                            if key != p and values["life"]:
                                if (values["x"], values["y"]) == (bomb[0] - i, bomb[1]):
                                    b = str(key) + " " + \
                                        str(self._bomb_list[bomb][0])
                                    self._clients_data[key]["life"] -= 1
                                    if not self._clients_data[key]["life"]:
                                        self._sending_data_process("DTH", b)
                                        self._alive -= 1
                                    else:
                                        self._clients_data[key]["x"] = self._game_spawns[key % len(
                                            self._game_spawns)][0]
                                        self._clients_data[key]["y"] = self._game_spawns[key % len(
                                            self._game_spawns)][1]
                                        self._game_map[self._game_spawns[key % len(
                                            self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100
                                        broke.append(
                                            (values["x"], values["y"], 0))
                                        pos = str(
                                            key) + " " + str(self._clients_data[key]["x"]) + " " + str(self._clients_data[key]["y"])
                                        self._sending_data_process("POS", pos)
                                    if key != killer:
                                        self._clients_data[killer]["kill"] += 1
                        self._game_map[bomb[1] + 1][bomb[0] - i] = 0
                    if block >= 5:
                        self._sending_data_process("GOT", str(
                            bomb[0] - i) + " " + str(bomb[1]))
                        self._game_map[(bomb[1] + 1)][bomb[0] - i] = 0

                    if block == 1:
                        buf += str((bomb[0] - i)) + " " + str(bomb[1]) + " "

                        r = self._bonus_setting[0] / 10
                        r = random.randint(-(9 - r), r)
                        if r:
                            r = random.choice(self._bonus_list)
                            self._sending_data_process("BNS", str(
                                bomb[0] - i) + " " + str(bomb[1]) + " " + str(r))
                            broke.append(
                                (bomb[0] - i, bomb[1] + 1, 5.0 + r / 100))
                        else:
                            broke.append((bomb[0] - i, bomb[1] + 1, 0))
                        break
                    elif block == 3:
                        destruction((bomb[0] - i, bomb[1]))
                        break
                    elif block != 0:
                        break

            for i in range(1, self._bomb_list[bomb][1] + 1):
                if bomb[1] + i < self._game_map[0][1]:
                    block = self._game_map[(bomb[1] + 1) + i][bomb[0]]
                    self._explosions[(bomb[0], bomb[1] + i)] = killer
                    threading.Thread(target=self._explosions_duration, args=(
                        (bomb[0], bomb[1] + i),)).start()

                    if block >= 4 and block < 5:
                        p = ceil((block - 4) * 100)
                        self._clients_data[p]["life"] -= 1
                        if not self._clients_data[p]["life"]:
                            self._sending_data_process("DTH", str(
                                p) + " " + str(self._bomb_list[bomb][0]))
                            self._alive -= 1
                        else:
                            self._clients_data[p]["x"] = self._game_spawns[p % len(
                                self._game_spawns)][0]
                            self._clients_data[p]["y"] = self._game_spawns[p % len(
                                self._game_spawns)][1]
                            self._game_map[self._game_spawns[p % len(
                                self._game_spawns)][1] + 1][self._game_spawns[p % len(self._game_spawns)][0]] = 4.0 + p / 100
                            broke.append((values["x"], values["y"], 0))
                            pos = str(
                                p) + " " + str(self._clients_data[p]["x"]) + " " + str(self._clients_data[p]["y"])
                            self._sending_data_process("POS", pos)
                        if p != killer:
                            self._clients_data[killer]["kill"] += 1
                        for key, values in self._clients_data.items():
                            if key != p and values["life"]:
                                if (values["x"], values["y"]) == (bomb[0], bomb[1] + i):
                                    b = str(key) + " " + \
                                        str(self._bomb_list[bomb][0])
                                    self._clients_data[key]["life"] -= 1
                                    if not self._clients_data[key]["life"]:
                                        self._sending_data_process("DTH", b)
                                        self._alive -= 1
                                    else:
                                        self._clients_data[key]["x"] = self._game_spawns[key % len(
                                            self._game_spawns)][0]
                                        self._clients_data[key]["y"] = self._game_spawns[key % len(
                                            self._game_spawns)][1]
                                        self._game_map[self._game_spawns[key % len(
                                            self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100
                                        broke.append(
                                            (values["x"], values["y"], 0))
                                        pos = str(
                                            key) + " " + str(self._clients_data[key]["x"]) + " " + str(self._clients_data[key]["y"])
                                        self._sending_data_process("POS", pos)
                                    if key != killer:
                                        self._clients_data[killer]["kill"] += 1
                        self._game_map[(bomb[1] + 1) + i][bomb[0]] = 0
                    if block >= 5:
                        self._sending_data_process("GOT", str(
                            bomb[0]) + " " + str(bomb[1] + i))
                        self._game_map[(bomb[1] + 1) + i][bomb[0]] = 0

                    if block == 1:
                        buf += str(bomb[0]) + " " + str(bomb[1] + i) + " "

                        r = self._bonus_setting[0] / 10
                        r = random.randint(-(9 - r), r)
                        if r:
                            r = random.choice(self._bonus_list)
                            self._sending_data_process("BNS", str(
                                bomb[0]) + " " + str(bomb[1] + i) + " " + str(r))
                            broke.append(
                                (bomb[0], (bomb[1] + 1) + i, 5.0 + r / 100))
                        else:
                            broke.append((bomb[0], (bomb[1] + 1) + i, 0))
                        break
                    elif block == 3:
                        destruction((bomb[0], bomb[1] + i))
                        break
                    elif block != 0:
                        break

            for i in range(1, self._bomb_list[bomb][1] + 1):
                if bomb[1] - i >= 0:
                    block = self._game_map[(bomb[1] + 1) - i][bomb[0]]
                    self._explosions[(bomb[0], bomb[1] - i)] = killer
                    threading.Thread(target=self._explosions_duration, args=(
                        (bomb[0], bomb[1] - i),)).start()

                    if block >= 4 and block < 5:
                        p = ceil((block - 4) * 100)
                        self._clients_data[p]["life"] -= 1
                        if not self._clients_data[p]["life"]:
                            self._sending_data_process("DTH", str(
                                p) + " " + str(self._bomb_list[bomb][0]))
                            self._alive -= 1
                        else:
                            self._clients_data[p]["x"] = self._game_spawns[p % len(
                                self._game_spawns)][0]
                            self._clients_data[p]["y"] = self._game_spawns[p % len(
                                self._game_spawns)][1]
                            self._game_map[self._game_spawns[p % len(
                                self._game_spawns)][1] + 1][self._game_spawns[p % len(self._game_spawns)][0]] = 4.0 + p / 100
                            broke.append((values["x"], values["y"], 0))
                            pos = str(
                                p) + " " + str(self._clients_data[p]["x"]) + " " + str(self._clients_data[p]["y"])
                            self._sending_data_process("POS", pos)
                        if p != killer:
                            self._clients_data[killer]["kill"] += 1
                        self._game_map[(bomb[1] + 1) - i][bomb[0]] = 0
                        for key, values in self._clients_data.items():
                            if key != p and values["life"]:
                                if (values["x"], values["y"]) == (bomb[0], bomb[1] - i):
                                    b = str(key) + " " + \
                                        str(self._bomb_list[bomb][0])
                                    self._clients_data[key]["life"] -= 1
                                    if not self._clients_data[key]["life"]:
                                        self._sending_data_process("DTH", b)
                                        self._alive -= 1
                                    else:
                                        self._clients_data[key]["x"] = self._game_spawns[key % len(
                                            self._game_spawns)][0]
                                        self._clients_data[key]["y"] = self._game_spawns[key % len(
                                            self._game_spawns)][1]
                                        self._game_map[self._game_spawns[key % len(
                                            self._game_spawns)][1] + 1][self._game_spawns[key % len(self._game_spawns)][0]] = 4.0 + key / 100
                                        broke.append(
                                            (values["x"], values["y"], 0))
                                        pos = str(
                                            key) + " " + str(self._clients_data[key]["x"]) + " " + str(self._clients_data[key]["y"])
                                        self._sending_data_process("POS", pos)
                                    if key != killer:
                                        self._clients_data[killer]["kill"] += 1
                        self._game_map[(bomb[1] + 1) - i][bomb[0]] = 0
                    if block >= 5:
                        self._sending_data_process("GOT", str(
                            bomb[0]) + " " + str(bomb[1] - i))
                        self._game_map[(bomb[1] + 1) - i][bomb[0]] = 0

                    if block == 1:
                        buf += str(bomb[0]) + " " + str(bomb[1] - i) + " "

                        r = self._bonus_setting[0] / 10
                        r = random.randint(-(9 - r), r)
                        if r:
                            r = random.choice(self._bonus_list)
                            self._sending_data_process("BNS", str(
                                bomb[0]) + " " + str(bomb[1] - i) + " " + str(r))
                            broke.append(
                                (bomb[0], (bomb[1] + 1) - i, 5.0 + r / 100))
                        else:
                            broke.append((bomb[0], (bomb[1] + 1) - i, 0))
                        break
                    elif block == 3:
                        destruction((bomb[0], bomb[1] - i))
                        break
                    elif block != 0:
                        break

            self._bomb_list.pop(bomb)

        destruction(bomb)

        if self._alive <= 1 and self._alive < len(self._clients_data):
            self._ending()

        for b in broke:
            self._game_map[b[1]][b[0]] = float(b[2])

        if len(buf) > 0:
            time.sleep(EXPLOSION_TIMER)
            self._sending_data_process("BRK", buf)

    def _restarting(self):
        print("[*] Restarting\n")
        for key, values in self._clients_data.items():
            self._clients_data[key].update({"x": self._game_spawns[key % len(self._game_spawns)][0],
                                            "y": self._game_spawns[key % len(self._game_spawns)][1],
                                            "bomb": self._settings[0],
                                            "timer": time.time(),
                                            "kill": 0,
                                            "speed": 0.35 - 0.02 * self._settings[2],
                                            "power": self._settings[1],
                                            "life": self._settings[4]})
            self._game_map[int(values["y"]) +
                           1][int(values["x"])] = 4.0 + key / 100
        self._alive = len(self._clients_data)
        self._sending_data_process("RST", "")
        time.sleep(1)
        self._ready = False

    def _ending(self):
        winner = -1
        kills = (-1, -1)
        for key, values in self._clients_data.items():
            if values["life"]:
                winner = key
            if values["kill"] > kills[1]:
                kills = (key, values["kill"])
        if winner == -1:
            winner = kills[0]
        self._sending_data_process("END", winner)
        print("[*] Game ended\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s port\n" % sys.argv[0])
        exit(1)

    s = Server(int(sys.argv[1]), True)
