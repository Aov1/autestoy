import time

from autestoy.tools.timestamp import Timestamp


def test_Timestamp():
    now = time.time()
    ts = Timestamp(now)
    print(ts)
    Timestamp.sw_utc = True
    print(ts)
