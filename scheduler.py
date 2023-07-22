from enum import Enum
from dataclasses import dataclass
from typing import List, NewType
from PySide6.QtCore import QDateTime, QTime
from random import Random
from math import floor
from camel import CamelRegistry
import datetime

todo_types = CamelRegistry()

QTimeAmount = NewType("QTimeAmount", QTime)

MORNING_START = 0
MORNING_LENGTH = 0.3
EVENING_START = 0.7
EVENING_LENGTH = 0.3


class TodoBias(Enum):
    NONE = 0
    MORNING = 1
    MORNING_ONLY = 2
    EVENING = 3
    EVENING_ONLY = 4
    MIDDAY = 5

    def get_biased_rng(self, rng: Random) -> float:
        match self:
            case TodoBias.NONE:
                # *Slight* midday bias
                return rng.betavariate(1.02, 1.02)
            case TodoBias.MIDDAY:
                return rng.betavariate(5, 5)
            case TodoBias.MORNING:
                return rng.betavariate(1, 1.35)
            case TodoBias.EVENING:
                return rng.betavariate(1.35, 1)
            case TodoBias.MORNING_ONLY:
                return MORNING_START + rng.betavariate(1.15, 1) * MORNING_LENGTH
            case TodoBias.EVENING_ONLY:
                return EVENING_START + rng.betavariate(1, 1.15) * EVENING_LENGTH

    def __str__(self) -> str:
        return self.name.replace("_", " ").capitalize()


@dataclass
class Todo:
    title: str
    times_per_day: int
    bias: TodoBias
    column_order = ["title", "times_per_day", "bias"]
    column_names = ["Title", "# per day", "Bias"]

    def get_random_time(self, rng: Random, day_start: QTime, day_end: QTime) -> QTime:
        time_period_float = self.bias.get_biased_rng(rng)
        time_period = QTime.fromMSecsSinceStartOfDay(
            day_start.msecsSinceStartOfDay()
            + floor(time_period_float * day_start.msecsTo(day_end))
        )

        return time_period


@todo_types.dumper(Todo, "todo", version=1)
def _todo_dump(todo: Todo):
    return dict(
        title=todo.title,
        times_per_day=todo.times_per_day,
        bias=todo.bias.value,
    )


@todo_types.loader("todo", version=1)
def _todo_loader(data: dict, version: int):
    return Todo(
        title=data["title"],
        times_per_day=data["times_per_day"],
        bias=TodoBias(data["bias"]),
    )


@dataclass
class SchedulerConfig:
    day_start: QTime
    day_end: QTime
    last_opened: QDateTime
    cooldown_period: QTimeAmount
    seed: int
    todos: List[Todo]

    @staticmethod
    def make_default_config():
        return SchedulerConfig(
            day_start=QTime.currentTime(),
            day_end=QTime(22, 0),
            last_opened=QDateTime.currentDateTime(),
            cooldown_period=QTimeAmount(QTime(0, 5)),
            seed=0,
            todos=[],
        )

    def update_morning(self):
        if self.last_opened.date().toPython() >= datetime.date.today():  # type: ignore
            return
        self.last_opened = QDateTime.currentDateTime()
        self.day_start = self.last_opened.time()


@todo_types.dumper(SchedulerConfig, "scheduler_config", version=1)
def _schedconf_dumper(config: SchedulerConfig):
    return dict(
        day_start=config.day_start.msecsSinceStartOfDay(),
        day_end=config.day_end.msecsSinceStartOfDay(),
        last_opened=config.last_opened.toPython(),
        cooldown_period=config.cooldown_period.msecsSinceStartOfDay(),
        seed=config.seed,
        todos=config.todos,
    )


@todo_types.loader("scheduler_config", version=1)
def _schedconf_loader(data: dict, version: int):
    return SchedulerConfig(
        day_start=QTime.fromMSecsSinceStartOfDay(data["day_start"]),
        day_end=QTime.fromMSecsSinceStartOfDay(data["day_end"]),
        last_opened=QDateTime.fromMSecsSinceEpoch(
            floor(data["last_opened"].timestamp() * 1000)
        ),
        cooldown_period=QTimeAmount(
            QTime.fromMSecsSinceStartOfDay(data["cooldown_period"])
        ),
        seed=data["seed"],
        todos=data["todos"],
    )


class Schedule:
    todos: dict[QTime, Todo]

    def __init__(self, config: SchedulerConfig) -> None:
        rng = Random(config.seed)
        for todo in config.todos:
            for _ in range(todo.times_per_day):
                self.allocate_todo(todo, config, rng)

    def is_time_avaliable(self, time: QTime, cooldown: QTimeAmount) -> bool:
        for time, _ in self.todos.items():
            time_from_todo = abs(time.msecsTo(time))
            if time_from_todo < cooldown.msecsSinceStartOfDay():
                return False
        return True

    def allocate_todo(self, todo: Todo, config: SchedulerConfig, rng: Random) -> None:
        time = todo.get_random_time(rng, config.day_start, config.day_end)
        while not self.is_time_avaliable(time, config.cooldown_period):
            time = todo.get_random_time(rng, config.day_start, config.day_end)
        self.todos[time] = todo
