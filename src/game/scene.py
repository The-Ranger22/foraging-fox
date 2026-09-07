from abc import abstractmethod, ABC
from itertools import cycle
from random import randint, seed
import random
from types import SimpleNamespace
from typing import Dict, List, Literal, Tuple
from enum import Enum, auto
import time
from pygame import Surface, Vector2
import pygame
from pygame.time import Clock


from src.entities.button import Button


class SceneState(Enum):
    NOT_LOADED = auto()
    LOADED = auto()
    RUNNING = auto()
    UNLOAD = auto()
    DEFEAT = auto()


class AbstractScene(ABC):
    state: SceneState
    name: str
    background: pygame.Surface
    entities: list
    audio: list

    def __init__(self, manager, name: str):
        self.manager = manager
        self.name = name
        self.entities = list()
        self.state = SceneState.NOT_LOADED

    @abstractmethod
    def loop(self, screen: Surface, clock: Clock) -> SceneState:
        pass

    @abstractmethod
    def render(self, screen: Surface):
        pass


class SceneManager:
    scenes: Dict[str, AbstractScene]
    screen: Surface
    next_scene: str
    curr_scene: str

    def __init__(self, screen: Surface):
        self.scenes = dict()
        self.screen = screen
        self.next_scene = ""
        self.curr_scene = ""
        self.left_click_held = False
        self.right_click_held = False

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


class FogTileEnum(Enum):
    TOTAL = auto()
    ONE_SIDE = auto()
    TWO_SIDE = auto()
    TWO_SIDE_O = auto()
    THREE_SIDE = auto()
    ALL_SIDES = auto()
    NONE = auto()


class GameState(Enum):
    RUNNING = auto()
    WIN = auto()
    LOST = auto()


class Grid(AbstractScene):
    TILE_SIZE = 40

    class FogTileSheet:
        def __init__(self, sheet: pygame.Surface):
            self.sheet = sheet

        def get_sprite(
            self,
            position,
            fog_tile: FogTileEnum,
            scale_size: int,
            orientation: Literal[0, 90, 180, 270] = 0,
        ):
            sprite = pygame.Surface([20, 20])

            area = tuple()
            match fog_tile:
                case FogTileEnum.TOTAL:
                    xy_coord = (0, 40)
                    pass
                case FogTileEnum.ONE_SIDE:
                    xy_coord = (20, 0)
                    pass
                case FogTileEnum.TWO_SIDE:
                    xy_coord = (40, 20)
                    pass
                case FogTileEnum.TWO_SIDE_O:
                    xy_coord = (40, 0)
                    pass
                case FogTileEnum.THREE_SIDE:
                    xy_coord = (0, 20)
                    pass
                case FogTileEnum.ALL_SIDES:
                    xy_coord = (20, 20)
                    pass
                case FogTileEnum.NONE:
                    xy_coord = (0, 0)
            area = (*xy_coord, 20, 20)
            sprite.blit(self.sheet, position, area)
            sprite = pygame.transform.rotate(sprite, float(orientation))
            sprite = pygame.transform.scale(sprite, (scale_size, scale_size))
            return sprite

    class Tile:
        uid: int
        position: Vector2
        is_target: bool
        is_revealed: bool
        others: dict

        def __init__(self, uid: int, position: Vector2, is_target: bool):
            self.uid = uid
            self.position = position
            self.is_target = is_target
            self.is_revealed = False
            self.is_flagged = False
            self.value = 0

        def to_str(self):
            return f"Tile<{self.position}>[{self.value}][{self.is_target}]"

    def __init__(
        self,
        manager: SceneManager,
        name: str,
        grid_width: int,
        grid_height: int,
        num_star_root: int,
        grid_tile_sheet: pygame.Surface,
        font: pygame.font.Font,
        rand_seed: int = 1,
    ):
        seed(rand_seed)
        super().__init__(manager, name)
        self.num_star_root = num_star_root
        self.dimensions = Vector2(grid_width, grid_height)
        self.grid_sheet = self.FogTileSheet(grid_tile_sheet)
        self.background = pygame.image.load("./assets/img/forestBackground.png")
        self.font = font

        self.sprites = pygame.sprite.Group()
        self.tiles = list()
        self.game_state = GameState.RUNNING
        self.timeout = 0
        self.sounds = {
            "win": pygame.mixer.Sound("./assets/sound/voice/wow.mp3"),
            "lose": pygame.mixer.Sound("./assets/sound/voice/rats.mp3"),
            "left_click": pygame.mixer.Sound("./assets/sound/effects/fog.mp3"),
            "right_click": pygame.mixer.Sound("./assets/sound/effects/dig.mp3"),
            "game_over": pygame.mixer.Sound("./assets/sound/music/game_over.mp3"),
        }
        screen_size = self.manager.screen.get_size()
        center_x = screen_size[0] / 2 - self.TILE_SIZE * (grid_width / 2)
        center_y = screen_size[1] / 2 - self.TILE_SIZE * (grid_height / 2)

        c = 0
        uid_count = 1
        for idx in range(int(self.dimensions.x)):
            col = list()
            for jdx in range(int(self.dimensions.y)):
                col.append(self.Tile(uid_count, Vector2(idx, jdx), False))
                uid_count += 1
            self.tiles.append(col)

        used_coordinates = []
        sr_count = 0
        while sr_count < self.num_star_root:
            x_coord = randint(0, int(self.dimensions.x) - 1)
            y_coord = randint(0, int(self.dimensions.y) - 1)

            if (x_coord, y_coord) not in used_coordinates:
                sr_count += 1
                self.tiles[x_coord][y_coord].is_target = True

        for idx in range(int(self.dimensions.x)):
            for jdx in range(int(self.dimensions.y)):
                pos = (center_x + self.TILE_SIZE * idx, center_y + self.TILE_SIZE * jdx)

                # Check adjacent
                self.tiles[idx][jdx].value = self.get_adjacent_target_count(idx, jdx)

                if (
                    self.tiles[idx][jdx].value == 0
                    and not self.tiles[idx][jdx].is_target
                ):
                    self.tiles[idx][jdx].is_revealed = True
                self.sprites.add(
                    Button(
                        self.grid_sheet.get_sprite(
                            (0, 0),
                            FogTileEnum.TOTAL,
                            self.TILE_SIZE,
                        ),
                        self.TILE_SIZE,
                        self.TILE_SIZE,
                        pos,
                        (idx, jdx),
                        self.tiles[idx][jdx].uid,
                    )
                )
                c += 1
        # for idx in range(int(self.dimensions.x)):
        #     for jdx in range(int(self.dimensions.y)):
        #         print(self.tiles[idx][jdx].to_str(), end=" ")
        #     print("", sep="\n")

    def has_won(self) -> bool:
        num_revealed = 0
        target = self.dimensions.x * self.dimensions.y - self.num_star_root
        for idx in range(int(self.dimensions.x)):
            for jdx in range(int(self.dimensions.y)):
                if not (tile := self.tiles[idx][jdx]).is_target:
                    num_revealed += tile.is_revealed
        return num_revealed == target

    def get_adjacent_target_count(self, idx, jdx) -> int:
        base = Vector2(idx, jdx)
        values = list(
            map(
                lambda x: Vector2(*x),
                [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
            )
        )
        count = 0

        for v in values:
            index = base + v
            if not (
                index.x < 0
                or index.y < 0
                or index.x >= self.dimensions.x
                or index.y >= self.dimensions.y
            ):
                count += self.tiles[int(index.x)][int(index.y)].is_target
        return count

    def get_adjacent_tile_states(self, idx, jdx) -> Tuple[FogTileEnum, int]:
        if not self.tiles[idx][jdx].is_revealed:
            return FogTileEnum.TOTAL, 0
        base = Vector2(idx, jdx)
        values = list(
            map(
                lambda x: Vector2(*x),
                [(-1, 0), (0, -1), (0, 1), (1, 0)],
            )
        )

        positions = {k: v for k, v in zip(["tc", "ll", "rr", "bc"], values)}
        foggy = list()

        for k, v in positions.items():
            index = base + v
            if not (
                index.x < 0
                or index.y < 0
                or index.x >= self.dimensions.x
                or index.y >= self.dimensions.y
            ):
                if not self.tiles[int(index.x)][int(index.y)].is_revealed:
                    foggy.append(k)
        match foggy:
            case ["tc"]:
                return FogTileEnum.ONE_SIDE, 90
            case ["rr"]:
                return FogTileEnum.ONE_SIDE, 180
            case ["bc"]:
                return FogTileEnum.ONE_SIDE, 270
            case ["ll"]:
                return FogTileEnum.ONE_SIDE, 0
            case ["tc", "rr"]:
                return FogTileEnum.TWO_SIDE, 180
            case ["rr", "bc"]:
                return FogTileEnum.TWO_SIDE, 270
            case ["ll", "bc"]:
                return FogTileEnum.TWO_SIDE, 0
            case ["tc", "ll"]:
                return FogTileEnum.TWO_SIDE, 90
            case ["tc", "bc"]:
                return FogTileEnum.TWO_SIDE_O, 90
            case ["ll", "rr"]:
                return FogTileEnum.TWO_SIDE_O, 0
            case ["tc", "rr", "bc"]:
                return FogTileEnum.THREE_SIDE, 270
            case ["ll", "rr", "bc"]:
                return FogTileEnum.THREE_SIDE, 0
            case ["tc", "ll", "bc"]:
                return FogTileEnum.THREE_SIDE, 90
            case ["tc", "ll", "rr"]:
                return FogTileEnum.THREE_SIDE, 180
            case ["tc", "ll", "rr", "bc"]:
                return FogTileEnum.ALL_SIDES, 0
            case []:
                return FogTileEnum.NONE, 0
            case _:
                return FogTileEnum.TOTAL, 0

    def render(self, screen: Surface):
        screen.blit(self.background, (0, 0))
        screen.blit(
            self.font.render("Left Click - Clear Fog", True, "black"),
            (40, 50),
        )
        screen.blit(
            self.font.render("Right Click - Mark Star Root", True, "black"),
            (410, 50),
        )
        #
        self.sprites.draw(screen)

    def loop(self, screen: Surface, clock: Clock) -> SceneState:
        self.render(screen)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_0]:
            self.manager.swap_scene("menu")
        mouse_rect = SimpleNamespace()
        mouse_rect.rect = pygame.Rect(*(*pygame.mouse.get_pos(), 1, 1))
        left_click, _, right_click = pygame.mouse.get_pressed()
        if self.game_state == GameState.LOST:
            if self.timeout >= 360:
                self.manager.swap_scene("menu")
                return SceneState.UNLOAD
            self.timeout += 1
            x_win, y_win = self.manager.screen.get_size()
            txt = self.font.render("Game Over", True, "black")
            screen.blit(txt, (x_win / 2, y_win / 2))
            return SceneState.RUNNING
        if self.game_state == GameState.WIN:
            if self.timeout >= 360:
                self.manager.swap_scene("menu")
            self.timeout += 1
            txt = self.font.render("YOU WIN", True, "yellow")
            x_win, y_win = self.manager.screen.get_size()
            screen.blit(txt, (x_win / 2, y_win / 2))
            return SceneState.RUNNING

        if not left_click:
            self.manager.left_click_held = False
        if not right_click:
            self.manager.right_click_held = False

        for sprite in self.sprites.sprites():
            if hasattr(sprite, "grid_coords"):
                x_idx = sprite.grid_coords[0]
                y_idx = sprite.grid_coords[1]
                tile = self.tiles[x_idx][y_idx]
                if pygame.sprite.collide_rect(sprite, mouse_rect):
                    if (
                        left_click
                        and not self.manager.left_click_held
                        and not tile.is_flagged
                    ):
                        self.sounds["left_click"].play()
                        self.manager.left_click_held = True
                        if tile.is_target:
                            self.game_state = GameState.LOST
                            pygame.mixer.fadeout(1)
                            self.sounds["game_over"].play()
                            self.sounds["game_over"].fadeout(10000)
                        if not tile.is_revealed:
                            tile.is_revealed = True
                    if right_click and not self.manager.right_click_held:
                        self.sounds["right_click"].play()
                        self.manager.right_click_held = True
                        if not tile.is_revealed:
                            tile.is_flagged = not tile.is_flagged
                tile_type, orientation = self.get_adjacent_tile_states(x_idx, y_idx)
                new_img = self.grid_sheet.get_sprite(
                    (0, 0),
                    tile_type,
                    self.TILE_SIZE,
                    orientation,
                )
                if tile.is_target and tile.is_revealed:
                    star_sprite = pygame.image.load("./assets/img/starroot-dead.png")
                    x_offset = (self.TILE_SIZE - 16) / 2
                    new_img.blit(star_sprite, (x_offset, 0))
                elif tile.is_flagged:
                    flag_sprite = pygame.image.load("./assets/img/starroot.png")
                    x_offset = (self.TILE_SIZE - 16) / 2
                    new_img.blit(flag_sprite, (x_offset, 0))
                elif tile.is_revealed and tile.value > 0:
                    colors = {
                        1: "blue",
                        2: "green",
                        3: "yellow",
                        4: "orange",
                        5: "red",
                        6: "red",
                        7: "red",
                        8: "red",
                    }
                    num_sprite = self.font.render(
                        str(tile.value), 0, colors[tile.value]
                    )
                    bounds = num_sprite.get_rect()
                    x_offset = (self.TILE_SIZE - bounds.width) / 2
                    y_offset = (self.TILE_SIZE - bounds.height) / 2
                    new_img.blit(num_sprite, (x_offset, y_offset))

                sprite.update(new_img)
        if self.has_won():
            self.game_state = GameState.WIN
            self.sounds["win"].play()
        return SceneState.RUNNING


class MainMenu(AbstractScene):
    def __init__(self, manager: SceneManager, name: str):
        super().__init__(manager, name)
        self.background = pygame.image.load("./assets/img/mountain_sunset.png")
        self.title = pygame.image.load("./assets/img/titleJustInCase.png")
        self.title = pygame.transform.scale_by(self.title, 2.0)
        self.title_pos = (
            Vector2(self.manager.screen.get_size())
            - Vector2(self.title.get_width(), self.title.get_height() + 200)
        ) / 2
        self.is_hover = False
        self.sprites = pygame.sprite.Group()
        self.font = pygame.font.Font("./assets/font/breathe_fire/breathe-fire.otf", 32)
        self.sprites.add(
            Button(
                self.font.render("PLAY", True, "yellow"), 0, 0, (400, 350), (0, 0), 1
            )
        )
        self.sprites.add(
            Button(
                self.font.render("QUIT", True, "yellow"), 0, 0, (400, 400), (0, 0), 2
            )
        )
        self.game_state = GameState.RUNNING
        self.timeout = 0

    def render(self, screen: Surface):
        screen.blit(self.background, (0, 0))
        screen.blit(self.title, self.title_pos)
        self.sprites.draw(screen)

    def loop(self, screen: Surface, clock: Clock) -> SceneState:
        self.render(screen)
        left_click, _, _ = pygame.mouse.get_pressed()
        mouse_rect = SimpleNamespace()
        mouse_rect.rect = pygame.Rect(*(*pygame.mouse.get_pos(), 1, 1))
        if self.game_state == GameState.LOST:
            if self.timeout >= 120:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            self.timeout += 1
            return SceneState.RUNNING

        if not left_click or self.manager.left_click_held:
            self.manager.left_click_held = False
            return SceneState.RUNNING
        self.manager.left_click_held = True

        for sprite in self.sprites.sprites():
            if is_collision := pygame.sprite.collide_rect(sprite, mouse_rect):
                if is_collision and not self.is_hover:
                    s = pygame.mixer.Sound("./assets/sound/effects/menu.mp3")
                    s.play()
                if sprite.uid == 1:
                    # s = pygame.mixer.Sound(
                    #     "./assets/sound/music/game_music{0}.mp3".format(randint(1, 3))
                    # )
                    # s.play(loops=64)
                    self.manager.add_scene(
                        Grid(
                            self.manager,
                            "grid",
                            8,
                            8,
                            16,
                            pygame.image.load(
                                "./assets/img/groundTilesPlusFog-Sheet.png"
                            ),
                            self.font,
                            int(time.time()),
                        )
                    )
                    self.manager.swap_scene("grid")
                if sprite.uid == 2:
                    s = pygame.mixer.Sound("./assets/sound/voice/byebye.mp3")
                    s.play()
                    self.game_state = GameState.LOST

        return SceneState.RUNNING


class YouLoseFucker(AbstractScene):
    def __init__(self, manager, name: str):
        super().__init__(manager, name)
        self.background = "black"

    def loop(self, screen: Surface, clock: Clock) -> SceneState:
        self.render(screen)
        return SceneState.RUNNING

    def render(self, screen: Surface):
        screen.fill(self.background)


class PauseMenu(AbstractScene):
    pass


class Settings(AbstractScene):
    pass
