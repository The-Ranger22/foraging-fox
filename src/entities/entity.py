from abc import ABC, abstractmethod

from pygame import Vector2


class Entity(ABC):
    uid: int
    position: Vector2
