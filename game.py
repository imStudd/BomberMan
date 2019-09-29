# -*- coding: utf-8 -*-

import queue
from math import ceil

import pygame

import client
import lobby
import map
import menu
import player
import server


class Game:
    def __init__(self, sq, rq, num, game_map, players, music=True, effect=True):
        self._send_q = sq
        self._recv_q = rq

        self._clock = pygame.time.Clock()

        self._num = num
        self._music = music
        self._effect = effect
        self._ended = False
        self._playing = True
        self._map = game_map

        self._players_data = players
        self._players_list = pygame.sprite.OrderedUpdates()

        self._create_window()
        self._start_game()

    def _create_window(self):
        try:
            if self._music:
                pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.init()

            res_y = pygame.display.Info().current_h
            # res_x = pygame.display.Info().current_w

            x = 96 + 32 * int(self._map[0][0])
            y = 48 + 32 * (int(self._map[0][1]) + 1)
            self._scale = 32

            if (y > res_y):
                self._scale = int(res_y / (int(self._map[0][1]) + 4))
                x = int((self._scale * 1.5) * 2 +
                        self._scale * int(self._map[0][0]))
                y = int((self._scale * 1.5) + self._scale *
                        (int(self._map[0][1])) + 1)
                self._window = pygame.display.set_mode(
                    (x, y), pygame.DOUBLEBUF)
            else:
                self._window = pygame.display.set_mode(
                    (x, y), pygame.DOUBLEBUF)

            pygame.display.set_caption("Bomber Man", "ressources/icon.png")
            icon = pygame.image.load("ressources/icon.png").convert_alpha()
            pygame.display.set_icon(icon)
        except Exception as ex:
            print("create window: %s\n" % ex)
            self._send_q.put(("QUT", ""))
            pygame.quit()
            quit()

    def _start_game(self):
        self._map = map.Map(self._window, self._map, self._scale, self._effect)

        if self._music:
            pygame.mixer.music.load("ressources/audio/music/game.ogg")
            pygame.mixer.music.play(loops=-1)

        pygame.key.set_repeat(1, 50)
        while self._playing:
            # try:
            self._clock.tick(60)

            if not self._recv_q.empty():
                data = self._recv_q.get()
                self._received_data_proccess(data)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._send_q.put(("QUT", ""))
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._send_q.put(("QUT", ""))
                        pygame.quit()
                        quit()
                    if event.key == pygame.K_RETURN:
                        self._send_q.put(("RST", ""))
                    if not self._ended:
                        if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self._send_q.put(("MOV", "B"))
                        if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_z:
                            self._send_q.put(("MOV", "T"))
                        if event.key == pygame.K_LEFT or event.key == pygame.K_a or event.key == pygame.K_q:
                            self._send_q.put(("MOV", "L"))
                        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            self._send_q.put(("MOV", "R"))
                        if event.key == pygame.K_SPACE:
                            self._send_q.put(("BMB", ""))

            self._map.update()
            self._players_list.update()

            if self._ended:
                self._window.blit(self._winner[0], self._winner[1])

            pygame.display.flip()

        pygame.quit()
        lobby.Lobby(self._send_q, self._recv_q, self._players_data, self._num)
        # except (pygame.error, Exception) as ex:
        #     print("game: %s\n" % ex)

    def _received_data_proccess(self, data):
        # print("#DEBUG Game# - ", data)

        if data[0] == "POS":
            for i, s in enumerate(self._players_list.sprites()):
                if s.num == int(data[1]):
                    self._players_list.sprites()[i].move(
                        int(data[2]), int(data[3]))
                    break

        elif data[0] == "BMB":
            self._map.add_bomb(int(data[1]), int(data[2]), int(data[3]))

        elif data[0] == "EXP":
            self._map.explode_bomb(int(data[1]), int(data[2]))

        elif data[0] == "DTH":
            for i, s in enumerate(self._players_list.sprites()):
                if s.num == int(data[1]):
                    self._players_list.remove(s)
                    break

        elif data[0] == "BNS":
            self._map.add_bonus(int(data[1]), int(data[2]), int(data[3]))

        elif data[0] == "GOT":
            self._map.remove_bonus(int(data[1]), int(data[2]))

        elif data[0] == "BRK":
            for x, y in zip(data[1::2], data[2::2]):
                self._map._destroy_blocks(int(x), int(y))

        elif data[0] == "LFT":
            for i, s in enumerate(self._players_list.sprites()):
                if s.num == int(data[1]):
                    self._players_list.remove(self._players_list.sprites()[i])
                    break
            self._players_data.pop(int(data[1]))

        elif data[0] == "ALL":
            for _ in range(int(data[1])):
                self._players_data[int(data[2])].update(
                    {"x": int(data[3]), "y": int(data[4]), "alive": True})
                del data[2:5]

        elif data[0] == "STR":
            for key, values in self._players_data.items():
                self._players_list.add(player.Player(
                    self._window, self._scale, values["x"],  values["y"],  key))

        elif data[0] == "END":
            font = pygame.font.SysFont(
                None, int((self._map._win_width + self._map._win_height) / 12))
            if int(data[1]) in self._players_data:
                winner = font.render(self._players_data[int(
                    data[1])]["pseudonym"] + " HAS WON", True, (255, 215, 0))
            else:
                winner = font.render("EGALITY", True, (255, 215, 0))
            winner_rect = winner.get_rect()
            winner_rect.move_ip((self._map._win_width / 2 - winner_rect.width / 2),
                                (self._map._win_height / 2 - winner_rect.height / 2))
            self._winner = (winner, winner_rect)
            self._ended = True

        elif data[0] == "RST":
            self._playing = False

        elif data == "EXT":
            pygame.quit()
            quit()

        # else:
        #     print("UNTREATED MESSAGE: ", data)
