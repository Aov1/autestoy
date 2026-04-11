from pprint import pprint

from autestoy.tools.record import CmdRecord


def test_cnt_fields():
    record = CmdRecord("", "")
    output = """ID\tName\tAge\tsex
 0\tasd \t10 \t男
 1\tfgh \t14 \t女
 2\tzxc \t18 \t男
 3\tqwe \t99 \t男
 4\trty \t17 \t女
 5\tvbn \t22 \t男"""
    cmp: list[list] = []
    for line in output.split("\n"):
        record.result_append(line)
        cmp.append(line.split("\t"))

    res = record.cut_fields(0)
    pprint(res)
    for e, c in zip(res, cmp):
        assert e == c
    res = record.cut_fields(1, 4)
    pprint(res)
    for e, c in zip(res, cmp):
        assert e == [c[0], c[3]]

    res = record.cut_characters((4, 7), (9, 11))
    pprint(res)
    for e, c in zip(res, cmp):
        assert e == [c[1], c[2]]
