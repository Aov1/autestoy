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


def test_SSH(remote):
    """测试SSH连接 与 执行命令"""
    remote_pad = SSH(remote, timeout=10)
    assert remote_pad.is_connected(), "SSH连接失败"

    res = remote_pad.exec_run("pwd")
    res = remote_pad.exec_run("a_cmd_nononononoerr")

    res = remote_pad.with_path("project/autestoy_sim").exec_run("python t10s.py")

    test_channel = remote_pad.create_channel("test_channel")
    assert test_channel.f_get_prompt

    res = test_channel.run("ls")
    res = test_channel.run("cd project/autestoy_sim")
    res = test_channel.run("python t10s.py")

    remote_pad.set_global_path("/data/data/com.termux/files/home/project/autestoy_sim")
    infer_cmd = remote_pad.long_running("python infer_log.py")
    tail_cmd = remote_pad.long_running("tail -f ./log.txt")

    st_time = time.time()
    while time.time() - st_time < 10:
        if not tail_cmd.fifo.empty() and "line:10" in tail_cmd.fifo.get():
            break

    infer_cmd.task_kill()
    tail_cmd.task_kill()

    # test_channel.run("rm log.txt")
    input("enter quit")

    print(infer_cmd.long_running_task.is_alive())
    print(tail_cmd.long_running_task.is_alive())

    print(infer_cmd.end_time)
    print(tail_cmd.end_time)

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
