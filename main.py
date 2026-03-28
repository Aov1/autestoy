import sys
import time


def test_print(n):
    for i in range(n):
        print(f"{i:X>50}")


def test_write(n):
    for i in range(n):
        sys.stdout.write(f"{i:X>50}\n")


n = 1000000

start = time.time()
test_print(n)
res = time.time() - start

start = time.time()
test_write(n)
res2 = time.time() - start

print(f"print: {res:.6f} seconds")
print(f"write: {res2:.6f} seconds")

print("FLOW EDITOR")
 