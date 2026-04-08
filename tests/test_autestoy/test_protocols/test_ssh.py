import re
import time
from pprint import pprint

from conftest import log

from autestoy.export.term import Term
from autestoy.protocols.ssh import SSH, Channel, RemoteConfig
from autestoy.tools.control import ulog
from autestoy.tools.record import CmdRecord


def test_RemoteConfig():
    log("test_RemoteConfig")
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
    log("test_SSH")
    """测试SSH连接 与 执行命令"""
    remote_pad = SSH(remote, timeout=60)
    assert remote_pad.is_connected(), "SSH连接失败"

    res = remote_pad.exec_run("pwd")
    ulog("exit code :", res.exit_code)
    res = remote_pad.exec_run("a_cmd_nononononoerr")
    ulog("exit code :", res.exit_code)

    res = remote_pad.with_path("project/autestoy_sim").exec_run("python t10s.py")
    ulog("exit code :", res.exit_code)


def test_Channel(ssh: SSH):
    log("test_Channel")
    test_channel = ssh.create_channel("test_channel")
    assert test_channel.f_get_prompt, f"prompt not found in {test_channel.prompt_now}"

    test_channel.run("ls")
    test_channel.run("cd project/autestoy_sim")
    test_channel.run("python t10s.py")


def test_SSH_long_running(ssh: SSH):
    log("test_SSH_long_running")
    ssh.set_global_path("/data/data/com.termux/files/home/project/autestoy_sim")
    infer_cmd = ssh.long_running("python infer_log.py")
    tail_cmd = ssh.long_running("tail -f ./log.txt")

    st_time = time.time()
    while time.time() - st_time < 10:
        if not tail_cmd.fifo.empty() and "line:10" in tail_cmd.fifo.get():
            break

    infer_cmd.task_kill()
    tail_cmd.task_kill()

    time.sleep(0.5)

    print(infer_cmd.long_running_task.is_alive())
    print(tail_cmd.long_running_task.is_alive())

    print(infer_cmd.end_time)
    print(tail_cmd.end_time)

    ssh.exec_run("cat log.txt")
    ssh.exec_run("rm -rf log.txt")

    for cmdr in ssh.cmds:
        pprint(cmdr.get_result())


def test_Channel_prompt():
    log("test_Channel_prompt")
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


def test_Channel_run_lines(ssh: SSH):
    log("test_Channel_run_lines")
    ch = ssh.create_channel()
    cmds = """
    ls
    cd project
    ls
    cd autestoy_sim
    ls
    pwd
    ps
    ps -aux
    """
    res = ch.run_lines(cmds)
    assert isinstance(res, list)
    for r in res:
        assert isinstance(r, CmdRecord)

    cmds_list = [
        "ls",
        "cd ..",
        "ls",
        "cd ..",
        "ls",
        "pwd",
        "ps",
        "ps -aux",
    ]
    res = ch.run_lines(cmds_list)
    assert isinstance(res, list)
    for r in res:
        assert isinstance(r, CmdRecord)


def test_cd(ssh: SSH):
    log("test_cd")
    ssh.cd("project")
    ssh.exec_run("ls")
    ssh.cd("..")
    ssh.exec_run("ls")
    ssh.cd("a_err_path")
    ssh.exec_run("ls")


def test_exec_run(ssh: SSH):
    log("test_exec_run")
    ssh.exec_run("ls")
    ssh.with_path("project/autestoy_sim").exec_run("python t10s.py")

    Term.sw_absolute_timestamp = True
    ssh.exec_run("ls")
    ssh.with_path("project/autestoy_sim").exec_run("python t10s.py")

    Term.sw_timestamp = False
    ssh.exec_run("ls")
    ssh.with_path("project/autestoy_sim").exec_run("python t10s.py")


def test_Channel_get_exit_code(ssh: SSH):
    ch = ssh.create_channel()
    res = ch.run("ls")
    assert res.exit_code == 0
    res = ch.run("pwd")
    assert res.exit_code == 0
    res = ch.run("abcdeefefe")
    assert res.exit_code == 127
