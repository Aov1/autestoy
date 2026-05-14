# import time

import autestoy as att
from autestoy.export.messageio import (
    # Message,
    MessageBus,
    MessageDispatcher,
    # MessageSource,
    # MessageType,
    # data_LOG,
)
from autestoy.export.term import MessageTerminal
from autestoy.tools.timestamp import Timestamp

ip_now = "192.168.110.30"


remote_conf = att.RemoteConfig(
    user="aoiiix",
    # host="192.168.51.12",
    host=ip_now,
    password="0402",
).set_name("vDebian13")

msgterm = MessageTerminal()
disp = MessageDispatcher()
disp.link_line(msgterm).start()
disp.start()

with (
    att.SSH(remote_conf) as debain,
    debain.create_channel("fast channel") as fast_channel,
):
    debain.set_global_path("/home/aoiiix/tmp_file")
    debain.exec_run_lines("pwd\n" * 10)

    fast_channel.run_lines("pwd\n" * 100)
    fast_channel.run_lines("tree ./")

    st = Timestamp()
    for i in range(10):
        MessageBus.ulog(f"This is a test message {i}", name="main_dbg")
    ed = Timestamp()

    sftp = debain.create_sftp()
    sftp.listdir()
    sftp.listdir_attr()
    for i in sftp.listdir_iter().result[0][1].get():
        MessageBus.ulog(str(i), name="main_dbg")
    sftp.close()


#
import subprocess as sp

sp.run("pwd", shell=True)

telnet_conf = att.TelnetConfig(
    host=ip_now,
    port=23,
)
tel = att.TelnetShell(telnet_conf, ("aoiiix", "0402"))

tel.shell_run("ls")

disp.join()
