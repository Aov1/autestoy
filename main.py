import autestoy as att

remote_conf = att.RemoteConfig(
    user="aoiiix",
    ip="192.168.51.12",
    password="0402",
).set_name("vDebian13")

with (
    att.SSH(remote_conf) as debain,
    debain.create_channel() as fast_channel,
):
    debain.set_global_path("/home/aoiiix/tmp_file")
    debain.exec_run("pwd")

    fast_channel.run_lines("pwd\n" * 10)
