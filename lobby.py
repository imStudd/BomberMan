# -*- coding: utf-8 -*-

import queue
import threading
import tkinter

import _thread

from pygame import mixer

import game

config = [1, 1, 0, 1500, 1, 50, 1, 1, 1]
map_name = "N/A"


class Lobby:
    def __init__(self, sq, rq, players={}, num=None):
        global config, map_name

        self._send_q = sq
        self._recv_q = rq

        mixer.init(44100, -16, 2, 2048)
        self._m = mixer.music.load("ressources/audio/music/lobby.ogg")
        mixer.music.play(loops=-1)

        self._launch = False
        self._settings = config
        self._map_name = map_name
        self._players_data_keys = ["pseudonym", "x", "y"]
        self._players_data = players
        self._my_num = num

        self._lobby_menu()

        if self._my_num is not None and min(self._players_data) != self._my_num:
            self._menubar.entryconfig(1, state=tkinter.DISABLED)
            self._menubar.entryconfig(2, state=tkinter.DISABLED)

        self._waiting = threading.Event()
        self._waiting.set()
        self._lobby_thread = threading.Thread(
            target=self._receive_data, daemon=True)
        self._lobby_thread.start()

        self._lobby_win.mainloop()

        if self._launch:
            config = self._settings
            map_name = self._map_name
            game.Game(self._send_q, self._recv_q, self._my_num, self._game_map,
                      self._players_data, self._game_music.get(), self._game_effects.get())

    def _lobby_menu(self):
        self._lobby_win = tkinter.Tk()
        self._lobby_win.config(bg="white smoke")
        self._lobby_win.title("BOMBER MAN - Lobby")
        self._lobby_win.geometry("1000x600+400+200")
        self._lobby_win.resizable(0, 0)

        self._menubar = tkinter.Menu(self._lobby_win)
        self._menubar.config(bg="white smoke", fg="black")

        game_settings = tkinter.Menu(self._menubar, tearoff=0)
        game_settings.config(bg="white smoke", fg="black")

        self._game_music = tkinter.BooleanVar()
        self._game_music.set(True)
        self._game_effects = tkinter.BooleanVar()
        self._game_effects.set(True)
        game_settings.add_checkbutton(
            label="Music", variable=self._game_music, onvalue=True, offvalue=False)
        game_settings.add_checkbutton(
            label="Effects", variable=self._game_effects, onvalue=True, offvalue=False)
        game_settings.add_command(
            label="How to play ?", command=self._print_keys)

        self._music = tkinter.BooleanVar()
        self._menubar.add_command(label="Start Game", command=self._start_game)
        self._menubar.add_command(
            label="Server Settings", command=self._setting_menu)
        self._menubar.add_cascade(label="Game Settings", menu=game_settings)
        self._menubar.add_checkbutton(
            label="Music", command=self._toggle_music, variable=self._music, onvalue=True, offvalue=False)

        self._lobby_win.config(menu=self._menubar)
        self._music.set(True)

        self._players_list = tkinter.Listbox(
            self._lobby_win, selectmode=tkinter.SINGLE)
        self._players_list.pack(side=tkinter.LEFT, fill=tkinter.Y)

        lscrollbar = tkinter.Scrollbar(
            self._lobby_win, command=self._players_list.yview)
        lscrollbar.pack(side=tkinter.LEFT, fill=tkinter.Y)
        self._players_list.config(yscrollcommand=lscrollbar.set)

        self._chat_box = tkinter.Text(
            self._lobby_win, state=tkinter.DISABLED, wrap=tkinter.WORD)
        self._chat_box.pack(side=tkinter.TOP, expand=1, fill=tkinter.BOTH)

        tscrollbar = tkinter.Scrollbar(
            self._chat_box, command=self._chat_box.yview)
        tscrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self._chat_box.config(yscrollcommand=tscrollbar.set)

        self._message_textbox = tkinter.Entry(self._lobby_win)
        self._message_textbox.pack(
            side=tkinter.LEFT, pady=15, expand=1, fill=tkinter.X)
        self._message_textbox.bind("<Return>", lambda x: self._send_message())
        self._message_textbox.focus()

        send_button = tkinter.Button(
            self._lobby_win, width=8, text="Send", command=self._send_message)
        send_button.pack(side=tkinter.LEFT, padx=5)

        self._lobby_win.protocol("WM_DELETE_WINDOW", self._closing_event)

    def _setting_menu(self):
        self._setting_win = tkinter.Toplevel(self._lobby_win)
        self._setting_win.config(bg="white smoke")
        self._setting_win.title("BOMBER MAN - Server Settings")
        self._setting_win.geometry("510x235+400+200")
        self._setting_win.resizable(0, 0)

        bomb_label = tkinter.Label(
            self._setting_win, text="Number of bomb(s)", bg="white smoke")
        bomb_label.grid(row=0, column=0, pady=5, padx=10)

        self._set_nb_bomb = tkinter.IntVar(self._lobby_win)
        set_bomb = tkinter.Spinbox(self._setting_win, from_=1, to=999,
                                   width=10, textvariable=self._set_nb_bomb, justify=tkinter.CENTER)
        self._set_nb_bomb.set(self._settings[0])
        set_bomb.grid(row=0, column=1, pady=5, padx=10)

        timer_label = tkinter.Label(
            self._setting_win, text="Bombs timer (ms)", bg="white smoke")
        timer_label.grid(row=0, column=2, pady=5, padx=10)

        self._set_timer = tkinter.IntVar(self._lobby_win)
        self._set_timer_bomb = tkinter.Spinbox(
            self._setting_win, from_=0, to=9999, textvariable=self._set_timer, width=10, justify=tkinter.CENTER)
        self._set_timer.set(self._settings[3])
        self._set_timer_bomb.grid(row=0, column=3, pady=5, padx=10)

        power_label = tkinter.Label(
            self._setting_win, text="Starting power", bg="white smoke")
        power_label.grid(row=1, column=0, pady=5, padx=10)

        self._set_nb_power = tkinter.IntVar(self._lobby_win)
        set_power = tkinter.Spinbox(self._setting_win, from_=1, to=999,
                                    width=10, textvariable=self._set_nb_power, justify=tkinter.CENTER)
        self._set_nb_power.set(self._settings[1])
        set_power.grid(row=1, column=1, pady=5, padx=10)

        speed_label = tkinter.Label(
            self._setting_win, text="Starting speed", bg="white smoke")
        speed_label.grid(row=1, column=2, pady=5, padx=10)

        self._set_nb_speed = tkinter.IntVar(self._lobby_win)
        set_speed = tkinter.Spinbox(self._setting_win, from_=0, to=9,
                                    width=10, textvariable=self._set_nb_speed, justify=tkinter.CENTER)
        self._set_nb_speed.set(self._settings[2])
        set_speed.grid(row=1, column=3, pady=5, padx=10)

        life_label = tkinter.Label(
            self._setting_win, text="Number of life(s)", bg="white smoke")
        life_label.grid(row=2, column=0, pady=5, padx=10)

        self._set_nb_life = tkinter.IntVar(self._lobby_win)
        set_life = tkinter.Spinbox(self._setting_win, from_=1, to=999,
                                   width=10, textvariable=self._set_nb_life, justify=tkinter.CENTER)
        self._set_nb_life.set(self._settings[4])
        set_life.grid(row=2, column=1, pady=5, padx=10)

        ratio_label = tkinter.Label(
            self._setting_win, text="Bonus ratio", bg="white smoke")
        ratio_label.grid(row=3, column=0, pady=5, padx=10)

        self._set_bonus_ratio = tkinter.IntVar(self._lobby_win)
        set_ratio = tkinter.Spinbox(self._setting_win, from_=0, to=100, width=10,
                                    textvariable=self._set_bonus_ratio, justify=tkinter.CENTER)
        self._set_bonus_ratio.set(self._settings[5])
        set_ratio.grid(row=3, column=1, pady=5, padx=10)

        coef_bomb_label = tkinter.Label(
            self._setting_win, text="Coef bomb bonus", bg="white smoke")
        coef_bomb_label.grid(row=3, column=2, pady=5, padx=10)

        self._set_bomb_coef = tkinter.IntVar(self._lobby_win)
        set_bomb_coef = tkinter.Spinbox(self._setting_win, from_=0, to=100,
                                        width=10, textvariable=self._set_bomb_coef, justify=tkinter.CENTER)
        self._set_bomb_coef.set(self._settings[6])
        set_bomb_coef.grid(row=3, column=3, pady=5, padx=10)

        coef_power_label = tkinter.Label(
            self._setting_win, text="Coef power bonus", bg="white smoke")
        coef_power_label.grid(row=4, column=0, pady=5, padx=10)

        self._set_power_coef = tkinter.IntVar(self._lobby_win)
        set_power_coef = tkinter.Spinbox(self._setting_win, from_=0, to=100,
                                         width=10, textvariable=self._set_power_coef, justify=tkinter.CENTER)
        self._set_power_coef.set(self._settings[7])
        set_power_coef.grid(row=4, column=1, pady=5, padx=10)

        coef_speed_label = tkinter.Label(
            self._setting_win, text="Coef speed bonus", bg="white smoke")
        coef_speed_label.grid(row=4, column=2, pady=5, padx=10)

        self._set_speed_coef = tkinter.IntVar(self._lobby_win)
        set_speed_coef = tkinter.Spinbox(self._setting_win, from_=0, to=100,
                                         width=10, textvariable=self._set_speed_coef, justify=tkinter.CENTER)
        self._set_speed_coef.set(self._settings[8])
        set_speed_coef.grid(row=4, column=3, pady=5, padx=10)

        map_label = tkinter.Label(
            self._setting_win, text="Map", bg="white smoke")
        map_label.grid(row=5, column=0, pady=5, padx=10)

        prev_map = tkinter.Button(
            self._setting_win, text="<", relief=tkinter.GROOVE, command=self._previous)
        prev_map.grid(row=5, column=1, pady=5, padx=10, ipadx=10)

        self._map_name_label = tkinter.Label(
            self._setting_win, text=self._map_name, bg="white smoke")
        self._map_name_label.grid(row=5, column=2, pady=5, padx=10)

        next_map = tkinter.Button(
            self._setting_win, text=">", relief=tkinter.GROOVE, command=self._next)
        next_map.grid(row=5, column=3, pady=5, padx=10, ipadx=10)

        set_apply = tkinter.Button(
            self._setting_win, text="Apply", relief=tkinter.GROOVE, command=self._apply_settings)
        set_apply.grid(row=6, column=1, pady=5, padx=10, ipadx=10)

        cancel = tkinter.Button(self._setting_win, text="Cancel",
                                relief=tkinter.GROOVE, command=self._setting_win.destroy)
        cancel.grid(row=6, column=2, pady=5, padx=10, ipadx=10)

    def _apply_settings(self):
        sets = str(self._set_nb_bomb.get()) + " " + str(self._set_nb_power.get()) + " " + str(
            self._set_nb_speed.get()) + " " + str(self._set_timer.get()) + " " + str(self._set_nb_life.get())
        cha = str(self._set_bonus_ratio.get()) + " " + str(self._set_bomb_coef.get()) + \
            " " + str(self._set_power_coef.get()) + " " + \
            str(self._set_speed_coef.get())
        self._send_q.put(("SET", sets))
        self._send_q.put(("CHA", cha))
        self._setting_win.destroy()

    def _next(self):
        self._send_q.put(("NXT", ""))

    def _previous(self):
        self._send_q.put(("PRV", ""))

    def _closing_event(self):
        self._waiting.clear()
        self._send_q.put(("QUT", ""))

    def _toggle_music(self):
        if not self._music.get():
            mixer.music.pause()
        else:
            mixer.music.unpause()

    def _print_keys(self):
        self._chat_box.configure(state=tkinter.NORMAL)
        self._chat_box.insert(
            tkinter.END, "\n---------------- How to play ? ----------------\n")
        self._chat_box.insert(
            tkinter.END, "Movements: ←↑↓→ / QZSD / WASD\nBomb: SPACE\nRestart: ENTER\nQuit: ESCAPE\n")
        self._chat_box.insert(
            tkinter.END, "-----------------------------------------------\n\n")
        self._chat_box.configure(state=tkinter.DISABLED)
        self._chat_box.see(tkinter.END)

    def _start_game(self):
        self._send_q.put(("RDY", ""))

    def _send_message(self):
        if len(self._message_textbox.get()) > 0:
            self._send_q.put(("MSG", self._message_textbox.get()))
            self._message_textbox.delete(0, tkinter.END)

    def _receive_data(self):
        for values in self._players_data.values():
            self._players_list.insert(tkinter.END, values["pseudonym"])

        while self._waiting.is_set():
            buf = self._recv_q.get()
            self._received_data_proccess(buf)

        mixer.quit()
        self._lobby_win.destroy()

    def _received_data_proccess(self, data):
        # print("#DEBUG Lobby# - ", data)

        if data[0] == "CND":
            self._my_num = int(data[1])

        elif data[0] == "MSG":
            msg = self._players_data[int(data[1])]["pseudonym"] + ": "
            for m in data[2:]:
                msg += m + " "
            msg += "\n"

            self._chat_box.configure(state=tkinter.NORMAL)
            self._chat_box.insert(tkinter.END, msg)
            self._chat_box.configure(state=tkinter.DISABLED)
            self._chat_box.see(tkinter.END)

        elif data[0] == "ARV":
            self._players_data[int(data[1])] = {"pseudonym": data[2]}
            self._players_list.insert(int(data[1]), data[2])

            self._chat_box.configure(state=tkinter.NORMAL)
            self._chat_box.insert(tkinter.END, data[2] + " joined the game\n")
            self._chat_box.configure(state=tkinter.DISABLED)
            self._chat_box.see(tkinter.END)

        elif data[0] == "LST":
            for _ in range(int(data[1])):
                self._players_data[int(data[2])] = {"pseudonym": data[3]}
                self._players_list.insert(int(data[2]), data[3])
                del data[2:4]

            self._menubar.entryconfig(1, state=tkinter.DISABLED)
            self._menubar.entryconfig(2, state=tkinter.DISABLED)

        elif data[0] == "MAP":
            self._waiting.clear()
            self._chat_box.configure(state=tkinter.NORMAL)
            self._chat_box.insert(tkinter.END, "The game get started\n")
            self._chat_box.configure(state=tkinter.DISABLED)
            self._chat_box.see(tkinter.END)

            game_map = [[data[1], data[2]]]
            line = []
            for x in range(3, len(data)):
                if (x - 3 > 0) and (x - 3) % int(data[1]) == 0:
                    game_map.append(line)
                    line = []
                line.append(data[x])
            game_map.append(line)

            self._game_map = game_map
            self._launch = True

        elif data[0] == "LFT":
            if int(data[1]) in self._players_data:
                self._chat_box.configure(state=tkinter.NORMAL)
                self._chat_box.insert(tkinter.END, self._players_data[int(
                    data[1])]["pseudonym"] + " lefted the game\n")
                self._chat_box.configure(state=tkinter.DISABLED)
                self._chat_box.see(tkinter.END)

                self._players_data.pop(int(data[1]))
                self._players_list.delete(int(data[1]))

            if min(self._players_data) == self._my_num:
                self._menubar.entryconfig(1, state=tkinter.NORMAL)
                self._menubar.entryconfig(2, state=tkinter.NORMAL)

        elif data[0] == "ACT":
            self._map_name = data[2]
            try:
                self._map_name_label.config(text=self._map_name)
            except:
                pass

        elif data[0] == "CFG":
            self._settings = list(map(int, data[1:]))
            if min(self._players_data) != self._my_num:
                self._chat_box.configure(state=tkinter.NORMAL)
                self._chat_box.insert(
                    tkinter.END, "\n--------------- Server Settings ---------------\n")
                self._chat_box.insert(tkinter.END, "Bomb(s): %d\nPower: %d\nSpeed: %d\nBomb timer: %d\nLife(s): %d\nRatio bonus: %d\nCoef bomb: %d\nCoef power: %d\nCoef speed: %d\nMap: %s\n" % (
                    self._settings[0], self._settings[1], self._settings[2], self._settings[3], self._settings[4], self._settings[5], self._settings[6], self._settings[7], self._settings[8], self._map_name))
                self._chat_box.insert(
                    tkinter.END, "-----------------------------------------------\n\n")
                self._chat_box.configure(state=tkinter.DISABLED)
                self._chat_box.see(tkinter.END)

        elif data == "EXT":
            self._waiting.clear()

        # else:
        #     print("UNTREATED MESSAGE: ", data)
