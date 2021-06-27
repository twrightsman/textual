from __future__ import annotations

import logging

import asyncio
from time import time
from tracemalloc import start
from typing import Callable

from dataclasses import dataclass

from ._timer import Timer
from ._types import MessageTarget


EasingFunction = Callable[[float], float]

# https://easings.net/
EASING = {
    "none": lambda x: 1.0,
    "round": lambda x: 0.0 if x < 0.5 else 1.0,
    "linear": lambda x: x,
    "in_cubic": lambda x: x * x * x,
    "in_out_cubic": lambda x: 4 * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 3) / 2,
    "out_cubic": lambda x: 1 - pow(1 - x, 3),
}


log = logging.getLogger("rich")


@dataclass
class Animation:
    obj: object
    attribute: str
    start_time: float
    duration: float
    start_value: float
    end_value: float
    easing_function: EasingFunction

    def __call__(self, time: float) -> bool:

        if self.duration == 0:
            value = self.end_value
        else:
            progress = min(1.0, (time - self.start_time) / self.duration)
            if self.end_value > self.start_value:
                eased_progress = self.easing_function(progress)
                value = (
                    self.start_value
                    + (self.end_value - self.start_value) * eased_progress
                )
            else:
                eased_progress = 1 - self.easing_function(progress)
                value = (
                    self.end_value
                    + (self.start_value - self.end_value) * eased_progress
                )

        setattr(self.obj, self.attribute, value)
        return value == self.end_value


class BoundAnimator:
    def __init__(self, animator: Animator, obj: object) -> None:
        self._animator = animator
        self._obj = obj

    def __call__(
        self,
        attribute: str,
        value: float,
        *,
        duration: float | None = None,
        speed: float | None = None,
        easing: EasingFunction | str = "in_out_cubic",
    ) -> None:
        easing_function = EASING[easing] if isinstance(easing, str) else easing
        self._animator.animate(
            self._obj,
            attribute=attribute,
            value=value,
            duration=duration,
            speed=speed,
            easing=easing_function,
        )


class Animator:
    def __init__(self, target: MessageTarget, frames_per_second: int = 30) -> None:
        self._animations: dict[tuple[object, str], Animation] = {}
        self._timer = Timer(target, 1 / frames_per_second, target, callback=self)

    async def start(self) -> None:
        asyncio.get_event_loop().create_task(self._timer.run())

    async def stop(self) -> None:
        self._timer.stop()

    def bind(self, obj: object) -> BoundAnimator:
        return BoundAnimator(self, obj)

    def animate(
        self,
        obj: object,
        attribute: str,
        value: float,
        *,
        duration: float | None = None,
        speed: float | None = None,
        easing: EasingFunction = EASING["in_out_cubic"],
    ) -> None:

        start_time = time()

        animation_key = (obj, attribute)
        if animation_key in self._animations:
            self._animations[animation_key](start_time)

        start_value = getattr(obj, attribute)
        if duration is not None:
            animation_duration = duration
        else:
            animation_duration = abs(value - start_value) / (speed or 50)

        animation = Animation(
            obj,
            attribute=attribute,
            start_time=start_time,
            duration=animation_duration,
            start_value=start_value,
            end_value=value,
            easing_function=easing,
        )
        self._animations[animation_key] = animation
        self._timer.resume()

    async def __call__(self) -> None:
        if not self._animations:
            self._timer.pause()
        else:
            animation_time = time()
            animation_keys = list(self._animations.keys())
            for animation_key in animation_keys:
                animation = self._animations[animation_key]
                if animation(animation_time):
                    del self._animations[animation_key]