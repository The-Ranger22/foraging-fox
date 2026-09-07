from pygame import Vector2
import pygame


class Button(pygame.sprite.Sprite):
    def __init__(
        self,
        img,
        width,
        height,
        pos,
        grid_coords,
        uid,
    ) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.uid = uid
        self.grid_coords = grid_coords
        # self.image = pygame.Surface([width, height])
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def update(self, new_img) -> None:
        self.image = new_img
        # self.image.fill(next(self.color_cycle))
