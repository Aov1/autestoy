from __future__ import annotations

# import asyncio
# import queue
import re
import threading as td
import time
import warnings
from typing import Self, Union, overload

# import asyncssh as assh
import paramiko as pk

from ..export.collect import Channel_record, SSH_record, collect
from ..tools.ansi import remove_ansi
from ..tools.result import CmdRecord, CmdRecording


class RemoteConfig:
    """远程配置类，用于配置远程主机的连接信息"""

    def __init__(self, user: str, ip: str, password: str, port: int = 22) -> None:
        self.user = user
        self.ip = ip
        self.password = password
        self.port = port
        self.name = f"{user}@{ip}"

    def set_name(self, name: str) -> Self:
        """设置远程主机的名称，不设置默认使用user名称"""
        self.name = name
        return self


@collect(SSH_record)
class SSH:
    """SSH协议类，用于连接远程主机"""

    def __init__(
        self, remote_config: RemoteConfig, timeout: float | None = None
    ) -> None:
        self.remote_config: RemoteConfig = remote_config
        self.name = self.remote_config.name
        self.remote = pk.SSHClient()
        self.remote.set_missing_host_key_policy(pk.AutoAddPolicy())
        self.timeout: None | float = timeout
        self.channels: list[Channel] = []
        self.cmds: list[CmdRecord] = []
        self.global_path: str | None = None
        self.temp_path: str | None = None
        self.base_path: str | None = None
        try:
            self._connect()
        except Exception as e:
            warnings.warn(f"Failed to connect to {self.remote_config.name}: {e}")

        if self.is_connected():
            _, stdout, _ = self.remote.exec_command("pwd")
            self.base_path = stdout.read().decode().strip()
            print(self.base_path)

    def is_connected(self) -> bool:
        """判断是否已连接到远程主机"""
        return (
            True if (tmp := self.remote.get_transport()) and tmp.is_active() else False
        )

    def _connect(self):
        """连接到远程主机"""
        self.remote.connect(
            hostname=self.remote_config.ip,
            username=self.remote_config.user,
            password=self.remote_config.password,
            port=self.remote_config.port,
            timeout=self.timeout,
        )

    def create_channel(self, name: str | None = None) -> Channel:
        """创建ssh通道，用作交互式终端"""
        tmp = Channel(self, name)
        self.channels.append(tmp)
        return tmp

    def set_global_path(self, path: str) -> None:
        """设置全局路径，所有后续命令都会在该路径下执行"""
        self.global_path = path

    def with_path(self, path: str) -> Self:
        """设置当前命令路径，只生效一次，可以链式调用\n
        ```python
        remote_config = RemoteConfig(user="user",ip="192.168.0.32",password="this_is_password",port=8022,).set_name("HUAWEI MATEPAD 12.2")
        pc = SSH(remote_config)
        pc.with_path("project/test").exec_run("ls") # 基于默认路径（一般是home）进行访问
        pc.with_path("/deta/data/com.termux/files/home/project/test").exec_run("ls") # 基于完整路径访问
        ```
        实现方式是在cmd前嵌入cd命令，等效于 `f"cd {temp_path} && {cmd}"` 。所以可以实现从默认路径相对访问和完整路径访问其他路径

        在任何ssh的run方法执行后清除（其实是self._path_process处理后清除），优先级高于global_path"""
        self.temp_path = path
        return self

    def cd(self, path: str) -> CmdRecord:
        """改变当前路径，作用于global_path，但是受到with_path方法维护的temp_path的影响\n
        当temp_path非空执行cd后清除temp_path，优先级高于global_path\n
        """
        head_path_info, _ = self._path_process("")
        record = CmdRecord(
            f"cd {path}",
            f"[{self.name}]{head_path_info} $",
        )
        self.cmds.append(record)
        record.start_time = time.time()
        print(record.get_fmt_prompt())
        record.stdin, stdout, stderr = self.remote.exec_command(f"cd {path} && pwd")

        while True:
            if res := stderr.readline():
                print(res.strip())
                record.record_result(res.strip())
                break
            if res := stdout.readline():
                self.global_path = res.strip()
                break
        record.record_end()
        return record

    def _path_process(self, cmd: str) -> tuple[str, str]:
        """处理路径逻辑，供给需要路径解算的方法，内部调用\n
        返回类维护的路径以及添加了cd命令的cmd"""
        head_path_info = ""
        if self.temp_path:
            processed_cmd = f"cd {self.temp_path} && {cmd}"
            head_path_info = self.temp_path
            self.temp_path = None
        elif self.global_path:
            processed_cmd = f"cd {self.global_path} && {cmd}"
            head_path_info = self.global_path
        else:
            processed_cmd = cmd
        return head_path_info, processed_cmd

    def exec_run(self, cmd: str) -> CmdRecord:
        """exec_run，执行命令，返回输出信息记录类CmdRecord
        ```python
        remote_config = RemoteConfig(
            user="user",
            ip="192.168.0.32",
            password="this_is_password",
            port=8022,
        ).set_name("HUAWEI MATEPAD 12.2")
        remote_pc = SSH(remote_config)
        remote_pc.exec_run('pwd')
        # [1]:[HUAWEI MATEPAD 12.2] $ pwd
        # /data/data/com.termux/files/home
        ```
        实现方式为exec_command方法，每次执行都相当于开启一个新的通道，因此没有上下文保持（例如cd到新的路径后，在下一个exec_run中又进入到默认路径)

        SSH类实现了with_path和set_global_path方法，用于exec_run设置临时路径和全局路径
        """
        head_path_info, processed_cmd = self._path_process(cmd)

        record = CmdRecord(
            cmd,
            f"[{self.name}]{head_path_info} $",
        )
        self.cmds.append(record)
        print(record.get_fmt_prompt())
        record.start_time = time.time()
        record.stdin, stdout, _stderr = self.remote.exec_command(
            processed_cmd, get_pty=True
        )
        out_str = ""
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                tmp_out = stdout.channel.recv(1024).decode()
                out_str += tmp_out
                print(tmp_out, end="")
            time.sleep(0.01)
        else:
            if stdout.channel.recv_ready():
                tmp_out = stdout.channel.recv(1024).decode()
                out_str += tmp_out
                print(tmp_out, end="")
        record.record_end()
        record.record_result(out_str)
        return record

    def _long_running_task(self, cmd: str, record: CmdRecording):
        record.stdin, stdout, _stderr = self.remote.exec_command(cmd, get_pty=True)

        while not record.stop_event.is_set():
            line = stdout.readline()
            if line != "":
                print(f"[{record.id}]:", line, end="")
                record.result.append(line)
                record.fifo.put(line)
            time.sleep(0.005)
        else:
            record.record_end()
            # dbg
            print("task end")

    def long_running(self, cmd: str, wait_time: float = 0.5) -> CmdRecording:
        head_path_info, processed_cmd = self._path_process(cmd)

        record = CmdRecording(
            cmd,
            f"[{self.name}]{head_path_info} $",
        )

        self.cmds.append(record)
        print(record.get_fmt_prompt())
        task = td.Thread(target=self._long_running_task, args=(processed_cmd, record))
        task.daemon = True
        record.long_running_task = task
        record.start_time = time.time()  # record start time
        task.start()
        time.sleep(wait_time)
        # task.join()
        return record


@collect(Channel_record)
class Channel:
    """通道类，用于管理SSH通道"""

    class_id = 0  # 用于给没有指定名称的通道生成id
    # prompt_pattern_default = r"(?:[\w@\-\.\[\]]+[:~/\w\-\. ]*)?[\$#]\s*$"  # 终端提示符捕获的正则表达式，如果不能适用请在创建Channel时指定
    prompt_pattern_default = r"(?:[\w@\-\.\[\]]+[:~/\w\-\. ]*|[:~/\w\-\. ]+)?[\$#]\s*$"

    @classmethod
    def id_generator(cls):
        """生成通道id"""
        cls.class_id += 1
        return cls.class_id

    def __init__(
        self,
        ssh: SSH,
        name: str | None = None,
        prompt_pattern: str = prompt_pattern_default,
        show_welcome_info: bool = False,
    ):
        """初始化通道，需要指定SSH"""
        self.shell = ssh.remote.invoke_shell()
        self.name = name if name else "ch_" + str(Channel.id_generator())
        self.prompt_complie = re.compile(prompt_pattern)
        self.cmds: list[CmdRecord] = []
        # 处理初始化通道时产生的默认输出，并获终端取提示符
        string = ""
        while True:
            if self.shell.recv_ready():
                welcome_info = self.shell.recv(65535).decode()
                string += welcome_info

                if show_welcome_info:
                    print(welcome_info)

                if tmp := self.prompt_complie.search(remove_ansi(string)):
                    break
            time.sleep(0.01)
        prompt = tmp.group().replace("\r", "")

        self.f_get_prompt = True if self.prompt_complie.search(prompt) else False
        self.prompt_now = prompt
        print(f"DBG:prompt_now = {prompt}")

    def set_name(self, name: str):
        """设置通道名称"""
        self.name = name

    def run(self, cmd: str) -> CmdRecord:
        """执行命令，使用正则匹配终端提示符判断是否结束"""
        # bug fix 速度过快会有遗留输出
        if self.shell.recv_ready():
            self.shell.recv(65535)
        buf = b""  # 处理缓冲区
        cmd_lines = (
            cmd.replace("\r\n", "\n").replace("\r", "").strip().split("\n")
        )  # 对于多行命令的处理
        f_cmd_lines_skip = False  # 是否处理完发送的命令
        f_prompt_received = False  # 是否匹配终端提示符
        res = ""  # 有效输出

        record = CmdRecord(cmd, f"[{self.name}]{self.prompt_now}")
        print(record.get_fmt_prompt())
        self.shell.send(
            bytes(cmd + "\r\n", "utf-8")
        )  # 发送的字符同样会进入接收当中，需要去重

        while True:
            if self.shell.recv_ready():  # 缓冲非空
                rcv = self.shell.recv(65535)  # 接收

                buf += rcv  # 存入buf
                # print(
                #     f"DBG : BUF IN RUN : {buf.decode().replace('\r\n', '[rn]').replace('\r', '[r]')}"
                # )
                while b"\r\n" in buf or b"\n" in buf:  # buf中有换行符就一直处理
                    buf = buf.replace(b"\r\n", b"\n")  # 统一换行符
                    line_b, buf = buf.split(b"\n", 1)  # 获取buf中的第一行
                    line = line_b.decode().strip().replace("\r", "")
                    # dbg
                    # print(f"DBG: LINE: {line}")

                    if (
                        len(cmd_lines) == 0 and not f_cmd_lines_skip
                    ):  # 未处理的多行命令为空并且命令处理完成标志未置位
                        f_cmd_lines_skip = True  # 标志置位

                    if (
                        not f_cmd_lines_skip  # 命令处理完成标志未置位
                        and cmd_lines[0] == remove_ansi(line)  # 命令行与当前行相等
                        and len(cmd_lines) > 0  # 命令行未处理完毕
                    ):
                        # print(f"DBG: pop cmd_lines = {cmd_lines}")
                        cmd_lines.pop(0)  # 弹出处理完的命令
                        continue
                    # print(f"DBG: rm ansi line = {remove_ansi(line)}")
                    if self.prompt_complie.search(
                        remove_ansi(line)
                    ):  # 当前行与命令行提示符匹配
                        self.prompt_now = remove_ansi(line).strip(
                            "\r\n "
                        )  # 更新命令行提示符
                        f_prompt_received = True  # 命令行提示符处理完成标志置位
                        break
                    # else:
                    # print("NOT MATCH BREAK")
                    print(line)  # 处理时实时输出
                    res += line + "\r\n"  # 累积输出
                # else:
                #     print("???????")
                if f_prompt_received:
                    break

            time.sleep(0.01)
        record.record_end()
        record.record_result(res)
        self.cmds.append(record)
        return record

    @overload
    def run_lines(self, cmds: list[str]) -> list[CmdRecord]:
        """执行多行命令，返回命令记录列表"""
        ...

    @overload
    def run_lines(self, cmds: str) -> list[CmdRecord]:
        """执行多行命令，输入是带有换行符的字符串

        如果无换行符，会调用self.run执行单行命令，统一返回list[CmdRecord]
        """
        ...

    def run_lines(self, cmds: Union[list[str], str]) -> list[CmdRecord]:
        if isinstance(cmds, list):
            return [self.run(cmd) for cmd in cmds]
        elif isinstance(cmds, str):
            if "\n" in cmds or "\r\n" in cmds:
                # 转换多行字符串命令为列表
                cmd_list = cmds.replace("\r\n", "\n").split("\n")
                # 去除空行
                cmd_list = [cmd.strip() for cmd in cmd_list if cmd.strip() != ""]
                # 递归调用run_lines
                return self.run_lines(cmd_list)
            else:  # 命令只有一行，统一列表返回格式
                return [self.run(cmds)]
