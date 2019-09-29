# -*- coding: utf-8 -*-

import queue
import tkinter
import tkinter.ttk

import client
import game
import server


class Menu:
    def __init__(self, q):
        self._q = q
        self._main_menu()

    def _main_menu(self):
        self._main_win = tkinter.Tk()
        self._main_win.config(bg="white smoke")
        self._main_win.title("BOMBER MAN - Menu")
        self._main_win.geometry("500x600")
        self._main_win.resizable(0, 0)

        self._bomber_label = tkinter.Label(
            self._main_win, text="BOMBER\nMAN", bg="white smoke", fg="#343852", font="Arial 55 bold")
        self._bomber_label.pack(side=tkinter.TOP, pady=15)

        self._nickname_label = tkinter.Label(
            self._main_win, text="Nickname", bg="white smoke")
        self._nickname_label.pack(side=tkinter.TOP, pady=10)

        self._nickname = tkinter.StringVar()
        self._nickname_entry = tkinter.Entry(
            self._main_win, textvariable=self._nickname, justify=tkinter.CENTER)
        self._nickname_entry.pack(side=tkinter.TOP)
        self._nickname_entry.focus()

        self._host_button = tkinter.Button(self._main_win, text="Host Game", width=20,
                                           height=2, relief=tkinter.GROOVE, command=self._host_menu, state=tkinter.DISABLED)
        self._host_button.pack(side=tkinter.TOP, pady=75)

        self._join_button = tkinter.Button(self._main_win, text="Join Game", width=20,
                                           height=2, relief=tkinter.GROOVE, command=self._join_menu, state=tkinter.DISABLED)
        self._join_button.pack(side=tkinter.TOP, pady=0)

        self._main_win.protocol("WM_DELETE_WINDOW", self._closing_event)
        self._nickname.trace("w", self._nickname_event)

        self._main_win.mainloop()

    def _host_menu(self):
        self._nickname_entry.config(state=tkinter.DISABLED)
        self._host_button.config(state=tkinter.DISABLED)
        self._join_button.config(state=tkinter.DISABLED)

        self._host_win = tkinter.Toplevel()
        self._host_win.config(bg="white smoke")
        self._host_win.title("BOMBER MAN - Host")
        self._host_win.geometry("450x150")
        self._host_win.resizable(0, 0)

        self._port_label = tkinter.Label(
            self._host_win, text="Port", bg="white smoke")
        self._port_label.pack(side=tkinter.TOP, pady=10)

        self._host_port = tkinter.IntVar()
        self._host_port.set(5555)
        self._port_spinbox = tkinter.Spinbox(
            self._host_win, from_=1024, to=65535, width=20, textvariable=self._host_port, justify=tkinter.CENTER)
        self._port_spinbox.pack(side=tkinter.TOP)

        self._start_button = tkinter.Button(
            self._host_win, text="Start", relief=tkinter.GROOVE, command=self._host_start)
        self._start_button.pack(
            side=tkinter.LEFT, padx=5, expand=1, fill=tkinter.X)

        self._cancel_button = tkinter.Button(
            self._host_win, text="Cancel", relief=tkinter.GROOVE, command=lambda: self._cancel_event(self._host_win))
        self._cancel_button.pack(
            side=tkinter.RIGHT, padx=5, expand=1, fill=tkinter.X)

        self._host_win.protocol(
            "WM_DELETE_WINDOW", lambda: self._cancel_event(self._host_win))

    def _join_menu(self):
        self._nickname_entry.config(state=tkinter.DISABLED)
        self._host_button.config(state=tkinter.DISABLED)
        self._join_button.config(state=tkinter.DISABLED)

        self._join_win = tkinter.Toplevel()
        self._join_win.config(bg="white smoke")
        self._join_win.title("BOMBER MAN - Join")
        self._join_win.geometry("350x200")
        self._join_win.resizable(0, 0)

        self._addr_label = tkinter.Label(
            self._join_win, text="Address", bg="white smoke")
        self._addr_label.pack(side=tkinter.TOP, pady=10)

        self._addr = tkinter.StringVar()
        self._addr.set("192.168.0.0")
        self._addr_entry = tkinter.Entry(
            self._join_win, textvariable=self._addr, justify=tkinter.CENTER)
        self._addr_entry.pack(side=tkinter.TOP)
        self._addr_entry.focus()

        self._port_label = tkinter.Label(
            self._join_win, text="Port", bg="white smoke")
        self._port_label.pack(side=tkinter.TOP, pady=15)

        self._join_port = tkinter.IntVar()
        self._join_port.set(5555)
        self._port_spinbox = tkinter.Spinbox(
            self._join_win, from_=1024, to=65535, textvariable=self._join_port, justify=tkinter.CENTER)
        self._port_spinbox.pack(side=tkinter.TOP)

        self._cancel_button = tkinter.Button(
            self._join_win, text="Cancel", relief=tkinter.GROOVE, command=lambda: self._cancel_event(self._join_win))
        self._cancel_button.pack(
            side=tkinter.RIGHT, padx=5, expand=1, fill=tkinter.X)

        self._connect_button = tkinter.Button(
            self._join_win, text="Connect", relief=tkinter.GROOVE, command=self._client_connect)
        self._connect_button.pack(
            side=tkinter.LEFT, padx=5, expand=1, fill=tkinter.X)

        self._join_win.protocol(
            "WM_DELETE_WINDOW", lambda: self._cancel_event(self._join_win))

    def _host_start(self):
        self._q.put((self._host_port.get(), self._nickname.get()))
        self._main_win.destroy()

    def _client_connect(self):
        self._q.put(
            (self._addr.get(), self._join_port.get(), self._nickname.get()))
        self._main_win.destroy()

    def _nickname_event(self, i, d, c):
        self._nickname.set(self._nickname.get().replace(" ", ""))
        if len(self._nickname.get()) > 0:
            self._host_button.config(state=tkinter.NORMAL)
            self._join_button.config(state=tkinter.NORMAL)
        else:
            self._host_button.config(state=tkinter.DISABLED)
            self._join_button.config(state=tkinter.DISABLED)

    def _cancel_event(self, win):
        win.destroy()
        self._host_button.config(state=tkinter.NORMAL)
        self._join_button.config(state=tkinter.NORMAL)
        self._nickname_entry.config(state=tkinter.NORMAL)

    def _closing_event(self):
        self._q.put("exit")
        self._main_win.destroy()
