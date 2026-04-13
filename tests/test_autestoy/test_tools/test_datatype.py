import numpy as np
import pytest

from autestoy.tools.datatype import (
    Bits,
    fmt_in_base,
    insert_every_n,
    num2bytes,
    str2num,
    width_in_base,
)


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


def test_insert_every_n():
    assert insert_every_n("12345678", 4, " ") == "1234 5678"
    assert insert_every_n("12345678", 2, ":") == "12:34:56:78"
    assert insert_every_n("12345678", 1, ",") == "1,2,3,4,5,6,7,8"
    assert insert_every_n("12345678", 3, "_") == "12_345_678"


def test_fmt_in_base():
    assert fmt_in_base(0b11110000, 8, 2, "_", 4, False) == "0b1111_0000"
    assert fmt_in_base(0b11110000, 8, 2, "_", 4, True) == "8'b1111_0000"
    assert fmt_in_base(0b11110000, 10, 2, "_", 4, False) == "0b00_1111_0000"
    assert fmt_in_base(0b11110000, 10, 2, "_", 4, True) == "10'b00_1111_0000"
    assert fmt_in_base(0x1234ABCD, 32, 16, "_", 4, False) == "0x1234_ABCD"
    assert fmt_in_base(0x1234ABCD, 32, 16, "_", 4, True) == "32'h1234_ABCD"


def test_Bits_init():
    t = Bits(0x12345678, 32)
    assert t.value == 0x12345678
    assert t.width == 32
    # assert t.bytes_cnt == 4
    # assert t.bytes.all() == np.array([0x78, 0x56, 0x34, 0x12], dtype=np.uint8).all()

    t = Bits("0b111110101010", 8)
    assert t.value == 0xAA
    assert t.width == 8
    # assert t.bytes_cnt == 1
    # assert t.bytes.all() == np.array([0xAA], dtype=np.uint8).all()

    t = Bits("32'h1234ABCD")
    assert t.value == 0x1234ABCD
    assert t.width == 32
    # assert t.bytes_cnt == 4
    # assert t.bytes.all() == np.array([0xCD, 0xAB, 0x34, 0x12], dtype=np.uint8).all()

    t = Bits("16'h1234ABCD")
    assert t.value == 0xABCD
    assert t.width == 16
    # assert t.bytes_cnt == 2
    # assert t.bytes.all() == np.array([0xCD, 0xAB], dtype=np.uint8).all()

    t = Bits("0x12345678_u32", 16)
    assert t.value == 0x5678
    assert t.width == 16

    t = Bits("0x1234_u16", 32)
    assert t.value == 0x1234
    assert t.width == 32

    t = Bits(t, 8)
    assert t.value == 0x34
    assert t.width == 8

    t = Bits(t)
    assert t.value == 0x34
    assert t.width == 8

    t = Bits(["4'b1111", Bits(0b1010, 4), (0xF0, 8)])
    assert t.value == 0b1111_1010_1111_0000
    assert t.width == 16

    print("Bits.__init__() ok")


def test_Bits_getitem():
    t = Bits(0b1011_0101, 8)

    assert t[3].value == 0
    assert t[3].width == 1
    assert t[4].value == 1
    assert t[4].width == 1

    assert t[0:3].value == t[7:4].value == 0b1011
    assert t[0:3].width == t[7:4].width == 4
    assert t[3:0].value == t[3:0].value == 0b0101
    assert t[3:0].width == t[3:0].width == 4

    assert t[3:].value == 0
    assert t[3:].width == 1
    assert t[:3].value == 1
    assert t[:3].width == 1

    t = Bits(0x0123_4567_89AB_CEDF, 64)
    assert t[7:0, 15:8].value == 0xDFCE
    assert t[7:0, 15:8].width == 16
    assert t[7, 6, 5, 4, 3, 2, 1, 0].value == 0xDF
    assert t[7, 6, 5, 4, 3, 2, 1, 0].width == 8
    assert t[:0, :1, :2, :3, :4, :5, :6, :7].value == 0x01
    assert t[:0, :1, :2, :3, :4, :5, :6, :7].width == 8


def test_Bits_str():
    t = Bits(0x0123_4567_89AB_CEDF, 64)
    Bits.set_str_type(16)
    assert str(t) == "0x0123456789ABCEDF"
    t = Bits(0o123_456_765, 25)
    Bits.set_str_type(8)
    assert str(t) == "0o123456765"


def test_Bits_fix():
    Bits.set_str_type(16)
    t = Bits(0x0123_4567_89AB_CEDF, 64)
    assert str(t) == "0x0123456789ABCEDF"
    t.value = 0x87654321
    assert str(t) == "0x0000000087654321"
    t.width = 8
    assert str(t) == "0x21"


def test_Bits__split_range():
    t = Bits(0x1234_5678, 32)
    assert t._split_range(0) == ((31, 0x1234_5678 >> 1), (0, 0))
    assert t._split_range(15) == ((16, 0x1234), (15, 0x5678 & (0xFFFF >> 1)))
    assert t._split_range((0, 15)) == ((0, 0), (16, 0x5678))
    assert t._split_range((15, 0)) == ((16, 0x1234), (0, 0))
    assert t._split_range((12, 15)) == ((12, 0x123), (16, 0x5678))
    assert t._split_range((15, 12)) == ((16, 0x1234), (12, 0x678))


def test_Bits_set_bits():
    t = Bits(0x1234_5670, 32)
    t.set_bits(0, 0x8765_4321)
    assert t.value == 0x1234_5671

    t = Bits(0x1234_5678, 32)
    t.set_bits((0, 15), 0x4321)
    assert t.value == 0x4321_5678

    t = Bits(0x1234_5678, 32)
    t.set_bits((15, 0), 0x8765)
    assert t.value == 0x1234_8765

    t = Bits(0x1234_5678, 32)
    t.set_bits((12, 15), 0xF)
    assert t.value == 0x123F_5678

    t = Bits(0x1234_5678, 32)
    t.set_bits((15, 12), 0xF)
    assert t.value == 0x1234_F678

    t = Bits(0x1234_5670, 32)
    t.set_bits(0, "0x8765_4321")
    assert t.value == 0x1234_5671

    t = Bits(0x1234_5678, 32)
    t.set_bits((0, 15), "16'h4321")
    assert t.value == 0x4321_5678

    t = Bits(0x1234_5678, 32)
    t.set_bits((0, 15), "12'h4321")
    assert t.value == 0x0321_5678

    t = Bits(0x1234_5678, 32)
    t.set_bits((15, 0), "0x8765")
    assert t.value == 0x1234_8765

    t = Bits(0x1234_5678, 32)
    t.set_bits((12, 15), "0b1111")
    assert t.value == 0x123F_5678

    t = Bits(0x1234_5678, 32)
    t.set_bits((15, 12), "0xFF")
    assert t.value == 0x1234_F678


def test_Bits___setitem__():
    t = Bits(0x1234_5678, 32)
    t[0] = 1
    assert t.value == 0x1234_5679

    t = Bits(0x1234_5678, 32)
    t[15:0] = 0xFFFF
    assert t.value == 0x1234_FFFF

    t = Bits(0x1234_5678, 32)
    t[0:15] = Bits("16'hffff")
    assert t.value == 0xFFFF_5678

    t = Bits(0x1234_5678, 32)
    t[0:15] = "16'hffffff"
    assert t.value == 0xFFFF_5678

    t = Bits(0x1234_5678, 32)
    t[0:15] = "32'hffff_ffff"
    assert t.value == 0xFFFF_5678

    t = Bits(0x0000_0000, 32)
    t[0] = 1  # Bits(0x0000_0001, 32)
    assert t.value == 0x0000_0001
    t[4:] = 1  # Bits(0x0000_0011, 32)
    assert t.value == 0x0000_0011
    t[:3] = 1  # Bits(0x1000_0011, 32)
    assert t.value == 0x1000_0011


def test_Bits_split_iter():
    t = Bits(0x1234_5678, 32)
    it = t.split_iter(4)
    assert next(it) == Bits("0x1_u4")
    assert next(it) == Bits("0x2_i4")
    assert next(it) == Bits("4'h3")
    assert next(it) == Bits("4'b0100")
    assert next(it) == Bits("0x5_u4")
    assert next(it) == Bits("0x6_u4")
    assert next(it) == Bits("0x7_u4")
    assert next(it) == Bits("0x8_u4")
    with pytest.raises(StopIteration):
        next(it)

    t = Bits(0b10_1010_1010_1010_1010_1010_1010_10101, 31)
    it = t.split_iter(3, right_align=False)
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b1_u1")
    with pytest.raises(StopIteration):
        next(it)

    t = Bits(0b101_010_101_1, 10)
    it = t.split_iter(3, right_align=False, from_left=False)
    assert next(it) == Bits("0b1_u1")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    with pytest.raises(StopIteration):
        next(it)

    t = Bits(0b1_101_010_101, 10)
    it = t.split_iter(3, from_left=False)
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b010_u3")
    assert next(it) == Bits("0b101_u3")
    assert next(it) == Bits("0b1_u1")
    with pytest.raises(StopIteration):
        next(it)
