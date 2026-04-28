from .timestamp import Timestamp

GLOBAL_has_init: bool = False
GLOBAL_timebase: Timestamp | None = None


def is_global_time_base_initialized() -> bool:
    return GLOBAL_has_init


def get_global_time_base() -> Timestamp | None:
    return GLOBAL_timebase


def time_base_init():
    global GLOBAL_has_init
    global GLOBAL_timebase
    GLOBAL_has_init = True
    GLOBAL_timebase = Timestamp()
    return GLOBAL_timebase


def get_global_time_base_or_init() -> Timestamp:
    global GLOBAL_timebase
    if GLOBAL_timebase is None:
        return time_base_init()
    return GLOBAL_timebase
