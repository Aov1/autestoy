# import threading as td
import time

from ..export.collect import Meta_record, collect


@collect(Meta_record)
class TryTime:
    """
    TryTime用于创建超时测试，较为鸡肋，如果do_something阻塞不会退出。
    ```python
    tt = TryTime(5)
    while tt:
        do_something()
    ```
    得到输出
    ```bash
    TryTime [1]@5s start at 1774676789.2699938
    TryTime [1]@5s Time Out 1774676794.2699955
    ```

    """

    _try_time_id = 0

    @classmethod
    def _id_generator(cls) -> int:
        cls._try_time_id += 1
        return cls._try_time_id

    def __init__(self, timeout_second: float):
        # self._task: td.Thread | None = None
        self.id = self._id_generator()
        self.timeout = timeout_second
        self.end_time: float
        self.start_time = time.time()
        self.name = self.start_time
        print(f"TryTime [{self.id}]@{self.timeout}s start at {self.start_time}")

    def _check(self) -> bool:
        tmp = time.time() - self.start_time < self.timeout
        if not tmp:
            self.end_time = time.time()
            print(f"TryTime [{self.id}]@{self.timeout}s Time Out {self.end_time}")
        return tmp

    # def _check_task(self):
    #     kill = td.Event()
    #     while not kill.is_set():
    #         if not self._check():
    #             kill.set()

    def __bool__(self):
        return self._check()

    # def __enter__(self):
    #     task = td.Thread(target=self._check_task)
    #     task.daemon = True
    #     # self._task = task
    #     task.start()
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     return True
