# -*- coding: utf-8 -*-

from math import ceil

import pygame

step_right = [(103, 2), (21, 34)]
step_left = [(73, 2), (21, 34)]
step_up = [(36, 2), (23, 34)]
step_down = [(2, 2), (23, 34)]


class Player(pygame.sprite.Sprite):
    def __init__(self, window, scale, x, y, nb):
        pygame.sprite.Sprite.__init__(self)
        self._window = window

        self._step_size = scale
        self._scale = (scale / 32) + 0.2
        self._player_img = pygame.image.load(
            "ressources/players/player_" + str((nb % 4) + 1) + ".png")
        self._player_img = pygame.transform.scale(
            self._player_img, (int(128 * self._scale), int(40 * self._scale)))

        self._perso = self._player_img
        self._pos = self._player_img.get_rect()
        self._pos.move_ip((int(scale * 1.5) + 3) +
                          (scale * x), (scale) * (y + 1))

        self._step_right = [[int(x * self._scale)for x in y]
                            for y in step_right]
        self._step_left = [[int(x * self._scale) for x in y]
                           for y in step_left]
        self._step_up = [[int(x * self._scale) for x in y] for y in step_up]
        self._step_down = [[int(x * self._scale) for x in y]
                           for y in step_down]

        self._right = False
        self._left = False
        self._up = False
        self._down = True

        self.num = nb
        self.alive = True

        self.x = x
        self.y = y

    def __repr__(self):
        return ("Player: %d, Alive: %r, X: %d, Y: %d" % (self.num, self.alive, self.x, self.y))

    def move(self, x, y):
        if self.alive:
            if self.y < y:
                self._down = True
                self._right = False
                self._left = False
                self._up = False
            elif self.y > y:
                self._up = True
                self._right = False
                self._left = False
                self._down = False
            elif self.x < x:
                self._right = True
                self._left = False
                self._up = False
                self._down = False
            elif self.x > x:
                self._left = True
                self._right = False
                self._up = False
                self._down = False
        self._pos.x = (int(self._step_size * 1.5) + 3) + (self._step_size * x)
        self._pos.y = (self._step_size) * (y + 1)
        self.y = y
        self.x = x

    def update(self):
        if self.alive:
            if self._left:
                self._window.blit(self._player_img, self._pos,
                                  (self._step_left[0], self._step_left[1]))

            elif self._right:
                self._window.blit(self._player_img, self._pos,
                                  (self._step_right[0], self._step_right[1]))

            elif self._up:
                self._window.blit(self._player_img, self._pos,
                                  (self._step_up[0], self._step_up[1]))

            elif self._down:
                self._window.blit(self._player_img, self._pos,
                                  (self._step_down[0], self._step_down[1]))
