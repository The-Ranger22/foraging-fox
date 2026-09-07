from typing import Dict, List
from src.game.scene import AbstractScene


class SceneManager:
    scenes: Dict[str, AbstractScene]
    next_scene: str
    curr_scene: str

    def __init__(self):
        self.scenes = dict()
        self.next_scene = ""
        self.curr_scene = ""

    @property
    def active_scene(self) -> AbstractScene:
        return self.scenes[self.curr_scene]

    def add_scene(self, scene: AbstractScene):
        self.scenes[scene.name] = scene

    def swap_scene(self, scene_name: str) -> bool:
        if scene_name in self.scenes.keys():
            self.curr_scene = scene_name
            return True
        return False
