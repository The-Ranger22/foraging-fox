from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Optional, Union
import yaml

import pygame
from pygame import Vector2

from src.game.scene import MainMenu, SceneManager, SceneState, Grid, YouLoseFucker


class FarmSweeperGame:
    scene_manager: SceneManager
    dimensions: Vector2

    @staticmethod
    def load_config(filepath: str) -> dict:
        with open(filepath) as fp:
            return yaml.load(fp, yaml.Loader)

    def __init__(self, config: Optional[Union[Dict, str]] = "game-config.yml"):
        pygame.init()
        pygame.display.set_caption("Foraging Fox")
        pygame.display.set_icon(pygame.image.load("./assets/img/fox.png"))
        if isinstance(config, (Path, str)):
            self.config = self.load_config(config)
        elif isinstance(config, dict):
            self.config = config
        self.screen = pygame.display.set_mode(
            (
                self.config["resolution"]["width"],
                self.config["resolution"]["height"],
            )
        )
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.font = pygame.font.Font("./assets/font/breathe_fire/breathe-fire.otf", 28)
        self.scene_manager = SceneManager(self.screen)
        self.scene_manager.add_scene(MainMenu(self.scene_manager, "menu"))
        self.scene_manager.add_scene(
            Grid(
                self.scene_manager,
                "grid",
                8,
                8,
                20,
                pygame.image.load(
                    Path(self.config["assets"]["sprites"]["directory"])
                    / self.config["assets"]["sprites"]["grid_tiles"]
                ),
                self.font,
            )
        )
        self.scene_manager.swap_scene("menu")

    def run(self):
        # Init
        #   - Load + cache assets
        running = True
        pygame.mixer.init()
        s = pygame.mixer.Sound("./assets/sound/music/main_theme.mp3")
        s.set_volume(0.5)
        s.play(128)

        while running:
            state: SceneState = self.scene_manager.active_scene.loop(
                self.screen, self.clock
            )
            match state:
                case SceneState.NOT_LOADED:
                    pass
                case SceneState.LOADED:
                    pass
                case SceneState.RUNNING:
                    pass
                case SceneState.UNLOAD:
                    s.play(128)
                    pass
                case _:
                    raise ValueError("Unimplemented state!")
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            # Render
            pygame.display.flip()
            self.dt = self.clock.tick(60) / 1000
        pygame.quit()


if __name__ == "__main__":
    FarmSweeperGame().run()
