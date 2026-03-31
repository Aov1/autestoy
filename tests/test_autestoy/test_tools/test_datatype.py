import numpy as np

from autestoy.tools.datatype import Bits, num2bytes, str2num


def test_str2num():
    print()
    assert str2num("1_234_000") == (0, 1234000)
    assert str2num("123") == (0, 123)
    assert str2num("123_u8") == (8, 123)
    assert str2num("123_i8") == (-8, 123)
    print("整数字符串 ok")

    assert str2num("1.0") == (0, 1.0)
    assert str2num("-1.5") == (0, -1.5)
    assert str2num("+1.5") == (0, 1.5)
    assert str2num("1_000.0") == (0, 1000)
    assert str2num("1000 0000.0000 0001") == (0, 10000000.0000_0001)
    assert str2num("1.0_f32") == (32, 1.0)
    assert str2num("-1.5_fp32") == (32, -1.5)
    assert str2num("+1.5_bf32") == (32, 1.5)
    print("浮点字符串 ok")

    assert str2num("1e6") == (0, 1000000)
    assert str2num("1.5e-3") == (0, 0.0015)
    assert str2num("-2.33E4") == (0, -23300.0)
    print("科学计数法字符串 ok")

    assert str2num("0b110011") == (0, int("0b110011", 2))
    assert str2num("0b11 0011_i32") == (-32, int("0b11_0011", 2))
    assert str2num("0b11 0011_u32") == (32, int("0b11_0011", 2))
    res = str2num("0b11111010101010")
    print(res[0], type(res[1]))
    assert res[0] == 0 and res[1] == int("0b11111010101010", 2)
    print("二进制字符串 ok")

    assert str2num("0o233") == (0, int("0o233", 8))
    assert str2num("0o233_u32") == (32, int("0o233", 8))
    assert str2num("0o233_i32") == (-32, int("0o233", 8))
    print("八进制字符串 ok")

    assert str2num("0d233") == (0, int("233", 10))
    assert str2num("0d233_u32") == (32, int("233", 10))
    assert str2num("0d233_i32") == (-32, int("233", 10))
    print("十进制字符串 ok")

    assert str2num("0x233") == (0, int("0x233", 16))
    assert str2num("0x233_u32") == (32, int("0x233", 16))
    assert str2num("0x233_i32") == (-32, int("0x233", 16))
    print("十六进制字符串 ok")

    assert str2num("True") == (1, 1)
    assert str2num("False") == (1, 0)
    assert str2num("true") == (1, 1)
    assert str2num("F") == (1, 0)
    print("布尔字符串 ok")

    assert str2num("8'b10101010") == (8, int("0b10101010", 2))
    assert str2num("8'sb10101010") == (-8, int("0b10101010", 2))
    assert str2num("8'o15") == (8, int("0o15", 8))
    assert str2num("8'so15") == (-8, int("0o15", 8))
    assert str2num("32'd10101010") == (32, int("10101010", 10))
    assert str2num("32'sd10101010") == (-32, int("10101010", 10))
    assert str2num("32'h1234ABCD") == (32, int("1234ABCD", 16))
    assert str2num("32'sh1234ABCD") == (-32, int("1234ABCD", 16))
    print("位宽字符串 ok")

    assert str2num("8'1") == (8, int("0b11111111", 2))
    assert str2num("'0") == (1, int("0b0", 2))
    print("填充字符串 ok")


def test_num2bits():
    assert num2bytes(1, 1) == np.array([1], dtype=np.uint8)
    assert num2bytes(1, 8) == np.array([1], dtype=np.uint8)
    assert (
        num2bytes(0x12345678, 32).all()
        == np.array([0x78, 0x56, 0x34, 0x12], dtype=np.uint8).all()
    )
    print("num2bits ok")


def test_Bits():
    t = Bits(0x12345678, 32)
    assert t.value == 0x12345678
    assert t.width == 32
    assert t.bytes_cnt == 4
    assert t.bytes.all() == np.array([0x78, 0x56, 0x34, 0x12], dtype=np.uint8).all()

    t = Bits("0b111110101010", 8)
    assert t.value == 0xAA
    assert t.width == 8
    assert t.bytes_cnt == 1
    assert t.bytes.all() == np.array([0xAA], dtype=np.uint8).all()

    t = Bits("32'h1234ABCD")
    assert t.value == 0x1234ABCD
    assert t.width == 32
    assert t.bytes_cnt == 4
    assert t.bytes.all() == np.array([0xCD, 0xAB, 0x34, 0x12], dtype=np.uint8).all()

    t = Bits("16'h1234ABCD")
    assert t.value == 0xABCD
    assert t.width == 16
    assert t.bytes_cnt == 2
    assert t.bytes.all() == np.array([0xCD, 0xAB], dtype=np.uint8).all()
    print("Bits ok")
