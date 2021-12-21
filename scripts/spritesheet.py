import pygame
import os
import json

# for parsing images from sprite sheets
class SpriteSheet:
    def __init__(self, filepath):
        dirname = os.path.dirname(__file__)
        sprite_path = os.path.join(dirname, filepath)
        self.sprite_sheet = pygame.image.load(sprite_path).convert()
        meta_data_path = sprite_path.replace('png', 'json')
        with open(meta_data_path) as f:
            self.data = json.load(f)
        f.close()

    def get_image_from_sprite(self, x, y, w, h):
        image = pygame.Surface((w, h))
        image.set_colorkey((0,0,0))
        image.blit(self.sprite_sheet,(0, 0),(x, y, w, h))
        return image

    def parse_sprite(self, name):
        s = self.data['frames'][name]
        x, y, w, h = s["x"], s["y"], s["w"], s["h"]
        image = self.get_image_from_sprite(x, y, w, h)
        return image