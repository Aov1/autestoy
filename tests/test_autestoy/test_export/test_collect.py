import autestoy.export.collect as collect
from autestoy.protocols.ssh import SSH, Channel, RemoteConfig


def test_collect():
    t = RemoteConfig(user="u0_a210", ip="192.168.0.32", port=8022, password="0402")
    t1 = SSH(t, timeout=5)
    ch1 = t1.create_channel()
    ch2 = t1.create_channel()
    ch3 = t1.create_channel()
    t2 = SSH(t.set_name("TEST2"))
    ch4 = t2.create_channel()
    ch5 = Channel(t2)
    for k, v in collect.SSH_record.items():
        print(k, v)

    for k, v in collect.Channel_record.items():
        print(k, v)
