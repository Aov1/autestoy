class T:
    def __init__(self) -> None:
        pass

    def __getitem__(self, key):
        print(f"{key = }")
        print(f"{type(key) = }")


t = T()
t["":"":""]

s = slice(30, 10, 2)
length = 32
start, stop, step = s.indices(length)
print(start, stop, step)
