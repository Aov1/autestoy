import autestoy as att
from autestoy.export.messageio import (
    Message,
    MessageBus,
    MessageSource,
    MessageType,
    data_LOG,
)
from autestoy.export.term import MessageTerminal
from autestoy.tools.timestamp import Timestamp

remote_conf = att.RemoteConfig(
    user="aoiiix",
    host="192.168.51.12",
    password="0402",
).set_name("vDebian13")

msgterm = MessageTerminal()

with (
    att.SSH(remote_conf) as debain,
    debain.create_channel() as fast_channel,
):
    debain.set_global_path("/home/aoiiix/tmp_file")
    debain.exec_run("pwd")

    fast_channel.run_lines("pwd\n" * 100)

    msg = Message(
        type=MessageType.LOG,
        source=MessageSource.USER,
        timestamp=Timestamp(),
        data=data_LOG(name="main_dbg", log="This is a test message"),
    )
    MessageBus.publish(msg)
