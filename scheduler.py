class Todo:
    title: str
    times_per_day: int
    column_order = ["title", "times_per_day"]
    column_names = ["Title", "# per day"]

    def __init__(self, title: str, times_per_day: int) -> None:
        self.title = title
        self.times_per_day = times_per_day
