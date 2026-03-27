import re
import time

from autestoy.protocols.ssh import SSH, Channel, RemoteConfig


def test_RemoteConfig():
    """测试RemoteConfig基础配置 与 方法"""
    host = RemoteConfig("test", "127.0.0.1", "password")
    assert host.user == "test"
    assert host.ip == "127.0.0.1"
    assert host.password == "password"
    assert host.port == 22
    assert host.name == "test@127.0.0.1"

    host.set_name("new_name")
    assert host.name == "new_name"


def test_SSH():
    """测试SSH连接 与 执行命令"""
    host = RemoteConfig(
        user="u0_a210",
        ip="192.168.0.32",
        password="0402",
        port=8022,
    ).set_name("HUAWEI MATEPAD 12.2")
    remote_pad = SSH(host, timeout=10)
    assert remote_pad.is_connected(), "SSH连接失败"

    res = remote_pad.exec_run("pwd")
    res = remote_pad.exec_run("a_cmd_nononononoerr")

    res = remote_pad.with_path("project/autestoy_sim").exec_run("python t10s.py")

    test_channel = remote_pad.create_channel("test_channel")
    assert test_channel.f_get_prompt

    res = test_channel.run("ls")
    res = test_channel.run("cd project/autestoy_sim")
    res = test_channel.run("python t10s.py")
    res.get_start_time()

    remote_pad.set_global_path("/data/data/com.termux/files/home/project/autestoy_sim")
    remote_pad.long_running("python infer_log.py")
    remote_pad.long_running("tail -f ./log.txt")

    input("enter quit")

    test_channel.run("cat log.txt")
    input("enter quit")

    test_channel.run("rm log.txt")


def test_Channel_prompt():
    prompt_compile = re.compile(Channel.prompt_pattern_default)
    test_cases = [
        "$",
        "#",
        "user@host:~$",
        "root@server:/root#",
        "[user@host ~]$",
        "~ $",
        "~/username/project/workspace $",
        "(.venv) ~/username/python_project $",
        "/home/user$",
        "~$",
        "\r\n~ $",
        "virtualenv (env) $",  # 带括号和空格
    ]
    for s in test_cases:
        res = prompt_compile.search(s)
        # print(f"{s} -> {res.group()}") if res else print(f"{s} -> None")
        assert res, f"{Channel.prompt_pattern_default} can not match {s}"
