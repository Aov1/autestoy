import time

from autestoy.tools.timestamp import TryTime


def test_TryTime():
    print()
    ts = TryTime(5)
    while ts:
        # pass
        print("while try time test !")
        time.sleep(0.8)

    # with TryTime(2) as ts:
    #     print("with try time test !")
    #     time.sleep(10)
    #     print("with try time test Fial!")
