from autestoy.protocols.ssh import (
    SSH,
    Channel,
    Channel_collect,
    SFTP_collect,
    SSH_collect,
)


def test_collect(remote):
    t1 = SSH(remote, timeout=5)
    t1.create_channel()
    t1.create_channel()
    t1.create_channel()
    t2 = SSH(remote.set_name("TEST2"))
    t2.create_channel()
    Channel(t2)
    t1.create_ftp()
    t2.create_ftp()
    for k, v in SSH_collect.items():
        print(k, v.name)

    for k, v in Channel_collect.items():
        print(k, v.name)

    for k, v in SFTP_collect.items():
        print(k, v.name)
