import autestoy.export.collect as collect
from autestoy.protocols.ssh import SSH, Channel


def test_collect(remote):
    t1 = SSH(remote, timeout=5)
    ch1 = t1.create_channel()
    ch2 = t1.create_channel()
    ch3 = t1.create_channel()
    t2 = SSH(remote.set_name("TEST2"))
    ch4 = t2.create_channel()
    ch5 = Channel(t2)
    for k, v in collect.SSH_record.items():
        print(k, v)

    for k, v in collect.Channel_record.items():
        print(k, v)
