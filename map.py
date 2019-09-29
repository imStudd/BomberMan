# -*- coding: utf-8 -*-

import threading
import time
from math import ceil

import pygame

import player


class Map():
    def __init__(self, window, game_map, scale, effect=True):
        self._window = window
        self._win_width, self._win_height = pygame.display.get_surface().get_size()

        self._map = game_map
        self._map_width = int(self._map[0][0])
        self._map_height = int(self._map[0][1])

        self._explosion = pygame.image.load(
            "ressources/textures/explosion.png").convert_alpha()
        self._bomb = pygame.image.load(
            "ressources/textures/bomb.png").convert_alpha()
        self._box = pygame.image.load(
            "ressources/textures/box.png").convert_alpha()
        self._bush = pygame.image.load(
            "ressources/textures/bush.png").convert_alpha()

        self._bonus_0 = pygame.image.load(
            "ressources/textures/bonus_0.png").convert_alpha()
        self._bonus_1 = pygame.image.load(
            "ressources/textures/bonus_1.png").convert_alpha()
        self._bonus_2 = pygame.image.load(
            "ressources/textures/bonus_2.png").convert_alpha()

        self._scale = scale
        self._scale_t = int(self._scale * 1.5)

        self._explosion = pygame.transform.smoothscale(
            self._explosion, (self._scale, self._scale))
        self._bomb = pygame.transform.smoothscale(
            self._bomb, (self._scale, self._scale))
        self._box = pygame.transform.smoothscale(
            self._box, (self._scale, self._scale))
        self._bush = pygame.transform.smoothscale(
            self._bush, (self._scale, self._scale))

        self._bonus_0 = pygame.transform.scale(
            self._bonus_0, (self._scale, self._scale))
        self._bonus_1 = pygame.transform.scale(
            self._bonus_1, (self._scale, self._scale))
        self._bonus_2 = pygame.transform.scale(
            self._bonus_2, (self._scale, self._scale))

        self._effect = effect
        if self._effect:
            self._explosion_effect = pygame.mixer.Sound(
                "ressources/audio/effects/explosion.wav")

        self._bomb_list = {}
        self._explosion_list = {}
        self._bonus_list = {}

        self._background = self._load_background()

    def _load_background(self):
        bg = pygame.Surface((self._win_width, self._win_height))
        grass = pygame.image.load("ressources/textures/grass.png").convert()
        tree = pygame.image.load(
            "ressources/textures/tree.png").convert_alpha()
        tree = pygame.transform.scale(tree, (self._scale_t, self._scale_t))

        for i in range(0, int(ceil(self._win_width / self._scale))):
            for j in range(0, int(ceil(self._win_height / self._scale))):
                bg.blit(grass, (i * self._scale, j * self._scale),
                        (0, 0, self._scale, self._scale))

        tx = int(ceil(self._win_width / self._scale_t))
        ty = int(ceil(self._win_height / self._scale_t))
        for i in range(0, tx):
            for j in range(0, ty):
                if (i not in range(1, tx - 1)) or (j not in range(1, ty - 1)):
                    bg.blit(tree, (i * self._scale_t, j * self._scale_t))
        return bg

    def add_bonus(self, x, y, bonus):
        self._bonus_list[(x, y)] = bonus

    def remove_bonus(self, x, y):
        self._bonus_list.pop((x, y))

    def add_bomb(self, x, y, power):
        self._bomb_list[(x, y)] = power

    def explode_bomb(self, x, y):
        self._explosion_list[(x, y)] = self._bomb_list[(x, y)]
        self._bomb_list.pop((x, y))
        threading.Thread(target=self._explosion_timer, args=((x, y),)).start()
        if self._effect:
            self._explosion_effect.play()

    def _explosion_timer(self, e):
        time.sleep(0.6)
        # b = self._explosion_list[e]
        # self._destroy_blocks(b[0], b[1], b[2])
        self._explosion_list.pop(e)
        if self._effect:
            self._explosion_effect.stop()

    def _destroy_blocks(self, x, y):
        self._map[y + 1][x] = 0
        # for i in range(1, p + 1):
        #     if x + i < self._map_width:
        #         block = int(self._map[y + 1][x + i])
        #         if block == 1:
        #             self._map[y + 1][x + i] = 0
        #             break
        #         elif block != 0:
        #             break
        # for i in range(1, p + 1):
        #     if x - i >= 0:
        #         block = int(self._map[y + 1][x - i])
        #         if block == 1:
        #             self._map[y + 1][x - i] = 0
        #             break
        #         elif block != 0:
        #             break
        # for i in range(1, p + 1):
        #     if y + i < self._map_height:
        #         block = int(self._map[(y + 1) + i][x])
        #         if block == 1:
        #             self._map[(y + 1) + i][x] = 0
        #             break
        #         elif block != 0:
        #             break
        # for i in range(1, p + 1):
        #     if y - i >= 0:
        #         block = int(self._map[(y + 1) - i][x])
        #         if block == 1:
        #             self._map[(y + 1) - i][x] = 0
        #             break
        #         elif block != 0:
        #             break

    def update(self):
        self._window.blit(self._background, (0, 0))

        for i, h in enumerate(self._map, 1):
            for j, w in enumerate(h):
                if w == "1":
                    self._window.blit(
                        self._box, (self._scale_t + (j * self._scale), self._scale_t + ((i - 2) * self._scale)))
                if w == "2":
                    self._window.blit(
                        self._bush, (self._scale_t + (j * self._scale), self._scale_t + ((i - 2) * self._scale)))

        for key, value in self._bonus_list.items():
            if value == 0:
                self._window.blit(
                    self._bonus_0, (key[0] * self._scale + self._scale_t, key[1] * self._scale + self._scale_t - 3))
            elif value == 1:
                self._window.blit(
                    self._bonus_1, (key[0] * self._scale + self._scale_t, key[1] * self._scale + self._scale_t - 3))
            elif value == 2:
                self._window.blit(
                    self._bonus_2, (key[0] * self._scale + self._scale_t, key[1] * self._scale + self._scale_t - 3))

        for b in self._bomb_list.keys():
            self._window.blit(
                self._bomb, (b[0] * self._scale + self._scale_t, b[1] * self._scale + self._scale_t - 3))

        for key, value in self._explosion_list.items():
            self._window.blit(
                self._explosion, (key[0] * self._scale + self._scale_t, key[1] * self._scale + self._scale_t - 3))
            for i in range(1, value + 1):
                if key[0] + i < self._map_width:
                    block = int(self._map[key[1] + 1][key[0] + i])
                    if block != 2:
                        self._window.blit(self._explosion, ((
                            key[0] + i) * self._scale + self._scale_t, key[1] * self._scale + (self._scale_t - 3)))  # RIGHT
                    if block == 1 or block == 2:
                        break
            for i in range(1, value + 1):
                if key[0] - i >= 0:
                    block = int(self._map[key[1] + 1][key[0] - i])
                    if block != 2:
                        self._window.blit(self._explosion, ((
                            key[0] - i) * self._scale + self._scale_t, key[1] * self._scale + (self._scale_t - 3)))  # LEFT
                    if block == 1 or block == 2:
                        break
            for i in range(1, value + 1):
                if key[1] + i < self._map_height:
                    block = int(self._map[(key[1] + 1) + i][key[0]])
                    if block != 2:
                        self._window.blit(
                            self._explosion, (key[0] * self._scale + self._scale_t, (key[1] + i) * self._scale + (self._scale_t - 3)))  # BOTTOM
                    if block == 1 or block == 2:
                        break
            for i in range(1, value + 1):
                if key[1] - i >= 0:
                    block = int(self._map[(key[1] + 1) - i][key[0]])
                    if block != 2:
                        self._window.blit(
                            self._explosion, (key[0] * self._scale + self._scale_t, (key[1] - i) * self._scale + (self._scale_t - 3)))  # TOP
                    if block == 1 or block == 2:
                        break
