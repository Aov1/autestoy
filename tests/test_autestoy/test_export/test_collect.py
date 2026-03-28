import autestoy.export.collect as collect
from autestoy.protocols.ssh import SSH, Channel


def test_collect(remote):
    t1 = SSH(remote, timeout=5)
    t1.create_channel()
    t1.create_channel()
    t1.create_channel()
    t2 = SSH(remote.set_name("TEST2"))
    t2.create_channel()
    Channel(t2)
    for k, v in collect.SSH_record.items():
        print(k, v)

    for k, v in collect.Channel_record.items():
        print(k, v)
