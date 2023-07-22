from enum import Enum
from dataclasses import dataclass
from typing import Callable, List, Literal, NewType, Tuple
from PySide6.QtCore import QDate, QDateTime, QTime, QTimer
from random import Random
from math import floor, inf
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
    def get_time_of_day(self, time: QTime) -> Literal["morning", "midday", "evening"]:
        day_length = (
            self.day_end.msecsSinceStartOfDay() - self.day_start.msecsSinceStartOfDay()
        )
        morning_start = self.day_start.msecsSinceStartOfDay()
        evening_start = morning_start + EVENING_START * day_length
        midday_start = morning_start + (MORNING_START + MORNING_LENGTH) * day_length
        time_ms = time.msecsSinceStartOfDay()

        if time_ms > evening_start:
            return "evening"
        if time_ms > midday_start:
            return "midday"
        return "morning"

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
    config: SchedulerConfig

    def __init__(self, config: SchedulerConfig) -> None:
        self.todos = {}
        self.timers = []
        self.config = config
        rng = Random(config.seed)
        for todo in config.todos:
            for _ in range(todo.times_per_day):
                self.allocate_todo(todo, config, rng)

    def is_time_avaliable(self, time: QTime, cooldown: QTimeAmount) -> bool:
        for todo_time, _ in self.todos.items():
            time_from_todo = abs(time.msecsTo(todo_time))
            if time_from_todo < cooldown.msecsSinceStartOfDay():
                return False
        return True

    def allocate_todo(self, todo: Todo, config: SchedulerConfig, rng: Random) -> None:
        time = todo.get_random_time(rng, config.day_start, config.day_end)
        while not self.is_time_avaliable(time, config.cooldown_period):
            time = todo.get_random_time(rng, config.day_start, config.day_end)
        self.todos[time] = todo

    def find_first_todo(self) -> Tuple[QTime, Todo] | None:
        """
        Find the first todo past the current time
        """
        closest_pair: Tuple[QTime, Todo] | None = None
        closest_msecs = inf
        cur_time = QTime.currentTime()
        for todo_time, todo in self.todos.items():
            time_amount = cur_time.msecsTo(todo_time)
            if time_amount < 0 or time_amount > closest_msecs:
                continue
            closest_pair = (todo_time, todo)
            closest_msecs = time_amount
        return closest_pair

    timers: List[QTimer]

    def queue_todo(self, action: Callable[[Todo, QTime], None]):
        first_todo_pair = self.find_first_todo()
        if first_todo_pair is None:
            return
        (todo_time, todo) = first_todo_pair

        timer = QTimer()

        timer.singleShot(
            (
                todo_time.msecsSinceStartOfDay()
                - QTime.currentTime().msecsSinceStartOfDay()
            ),
            lambda: action(todo, todo_time),
        )
        self.timers.append(timer)

    def cancel_queued(self):
        for timer in self.timers:
            timer.stop()
        self.timers.clear()
