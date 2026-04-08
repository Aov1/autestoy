from __future__ import annotations

# 外部库
# import asyncio
# import queue
import re
import threading as td
import time
import warnings
from os import PathLike
from typing import IO, Callable, Iterable, Iterator, Self, TypeAlias, Union, overload

import paramiko as pk
from paramiko.sftp_attr import SFTPAttributes
from paramiko.sftp_file import SFTPFile

# 相对调用
from ..export.collect import CollectObj, CollectType, collect
from ..export.term import Term
from ..tools.ansi import AnsiColor, AnsiReset, remove_ansi
from ..tools.record import CmdRecord, CmdRecording, MetaRecord
from ..tools.result import Result

# import asyncssh as assh
# from ..tools.timestamp import Timestamp


# 这两项是为了兼容paramiko SFTPClient 方法的参数类型
StrOrBytesPath: TypeAlias = str | bytes | PathLike[str] | PathLike[bytes]
_Callback: TypeAlias = Callable[[int, int], object]

# 收集已经被创建的类，稍微丑陋
# SSH_collect: dict[str, Any] = {}  # 记录所有创建的SSH类
# Channel_collect: dict[str, Any] = {}  # 记录所有创建的Channel类
# SFTP_collect: dict[str, Any] = {}  # 记录所有创建的STFP类


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


@collect(CollectType.SSH, CollectObj)
class SSH:
    """SSH协议类，用于连接远程主机"""

    def __init__(
        self,
        remote_config: RemoteConfig,
        timeout: float | None = None,
        raise_when_timeout: bool = True,
    ) -> None:
        # class create reocrd
        self.remote_config: RemoteConfig = remote_config
        self.name = self.remote_config.name
        self.meta_record = MetaRecord(
            type="SSH",
            name=self.name,
            info=f"{self.remote_config.user}@{self.remote_config.ip}",
        )
        # Term.putsln(
        #     f"[{self.meta_record.type}][{self.meta_record.name}][{self.meta_record.info}] Created"
        # )
        # config
        self.remote = pk.SSHClient()
        self.remote.set_missing_host_key_policy(pk.AutoAddPolicy())
        self.timeout: None | float = timeout
        # sub record
        self.channels: list[Channel] = []  # 记录子通道
        self.cmds: list[CmdRecord[str]] = []  # 记录运行的命令
        self.sftp: list[SFTP] = []  # 记录开启的SFTP服务
        # path config
        self.global_path: str | None = None
        self.temp_path: str | None = None
        self.base_path: str | None = None
        # try connect
        try:
            self._connect()
        except Exception as e:
            if raise_when_timeout:
                raise TimeoutError(
                    f"Connect [{self.name}][{self.remote_config.user}@{self.remote_config.ip}] TimeOut!"
                )
            else:
                warnings.warn(
                    f"Failed to connect to {self.remote_config.name}: TimeOut!"
                )
        # check connect
        if self.is_connected():
            self.meta_record.logs.append(
                Term.putsln(f"{self.meta_record.get_fmt_prompt()} Connected")
            )
            self.start_time = self.meta_record.start_time
            _, stdout, _ = self.remote.exec_command("pwd")
            self.base_path = stdout.read().decode().strip()
            # print(self.base_path)
            self.connect_time = time.time()

    def __del__(self):
        if self.is_connected():
            for ch in self.channels:
                if not ch.shell.closed:
                    ch.shell.close()
                    ch.meta_record.logs.append(
                        Term.putsln(f"{ch.meta_record.get_fmt_prompt()} Closed")
                    )
            self.remote.close()
            self.meta_record.logs.append(
                Term.putsln(f"{self.meta_record.get_fmt_prompt()} Disconnected")
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_connected():
            for ch in self.channels:
                if not ch.shell.closed:
                    ch.shell.close()
                    ch.meta_record.logs.append(
                        Term.putsln(f"{ch.meta_record.get_fmt_prompt()} Closed")
                    )
            self.remote.close()
            self.meta_record.logs.append(
                Term.putsln(f"{self.meta_record.get_fmt_prompt()} Disconnected")
            )
        return False

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

    def create_channel(
        self,
        name: str | None = None,
        prompt_pattern: str | None = None,
        show_welcome_info: bool = False,
        insert_cmd: str | None = None,
    ) -> Channel:
        """创建ssh通道，用作交互式终端"""

        tmp = Channel(
            self,
            name=name,
            prompt_pattern=prompt_pattern,
            show_welcome_info=show_welcome_info,
            insert_cmd=insert_cmd,
        )
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

    def cd(self, path: str) -> CmdRecord[str]:
        """改变当前路径，作用于global_path，但是受到with_path方法维护的temp_path的影响\n
        当temp_path非空执行cd后清除temp_path，优先级高于global_path\n
        不管被哪个路径影响，最后根据运行返回的路径覆盖global_path。\n
        路径错误或不存在不会对gloabl_path赋值。
        """
        head_path_info, _ = self._path_process("")
        record = CmdRecord[str](
            f"cd {path}",
            f"[{self.name}]{head_path_info} $",
        )
        self.cmds.append(record)
        # record.start_time = Timestamp()
        Term.putsln(record.get_fmt_prompt())
        record.stdin, stdout, stderr = self.remote.exec_command(f"cd {path} && pwd")

        while True:
            if res := stderr.readline().strip():
                record.result.append(Term.putsln(res))
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

    def exec_run(self, cmd: str) -> CmdRecord[str]:
        """exec_run_bata，执行命令，返回输出信息记录类CmdRecord\n
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

        SSH类实现了with_path、set_global_path和cd方法，用于exec_run设置临时路径和全局路径
        """
        head_path_info, processed_cmd = self._path_process(cmd)

        record = CmdRecord[str](
            cmd,
            f"[{self.name}]{head_path_info} $",
        )
        self.cmds.append(record)
        record.start_time, _ = Term.putsln(record.get_fmt_prompt())
        record.stdin, stdout, _stderr = self.remote.exec_command(
            processed_cmd, get_pty=True
        )
        while not stdout.channel.exit_status_ready():
            if (tmp_out := stdout.readline().strip()) != "":
                record.result.append(Term.putsln(tmp_out))
            time.sleep(0.01)
        else:
            if (tmp_out := stdout.readline().strip()) != "":
                record.result.append(Term.putsln(tmp_out))
            record.exit_code = stdout.channel.recv_exit_status()
        record.record_end()
        return record

    def _long_running_task(self, cmd: str, record: CmdRecording[str]):
        record.stdin, stdout, _stderr = self.remote.exec_command(cmd, get_pty=True)

        while not record.stop_event.is_set():
            line = stdout.readline()
            if line != "":
                line = line.strip()
                record.result.append(
                    Term.putsln(
                        line,
                        insert_str_before_msg=f"{AnsiColor.light_cyan}[{record.id}]{AnsiReset}",
                    )
                )
                record.fifo.put(line)
            time.sleep(0.005)
        else:
            record.record_end()
            record.exit_code = stdout.channel.recv_exit_status()
            # DBGexit_status()
            # Term.putsln(f"[{record.id}] task end")

    def long_running(self, cmd: str, wait_time: float = 0.5) -> CmdRecording[str]:
        """多线程执行，对于命令创建一个线程，不会阻塞主线程执行"""
        head_path_info, processed_cmd = self._path_process(cmd)

        record = CmdRecording[str](
            cmd,
            f"[{self.name}]{head_path_info} $",
        )

        self.cmds.append(record)
        task = td.Thread(target=self._long_running_task, args=(processed_cmd, record))
        task.daemon = True
        record.long_running_task = task
        # record.start_time = time.time()  # record start time
        Term.putsln(record.get_fmt_prompt())
        task.start()
        time.sleep(wait_time)
        # task.join()
        return record

    @overload
    def long_running_list(self, *cmd: str) -> list[CmdRecording[str]]:
        """eg:\n
        ```python
        dut = SSH(conf(...))
        dut.long_running_list('cmd1','cmd2','cmd3',...)
        ```
        """
        ...

    @overload
    def long_running_list(self, *cmd: Iterable) -> list[CmdRecording[str]]:
        """eg:\n
        ```python
        dut = SSH(conf(...))
        dut.long_running_list(['cmd1','cmd2','cmd3',...])
        dut.long_running_list(('cmd1','cmd2','cmd3',...))
        cmds = iter(cmd_iterable)
        dut.long_running_list(cmds)

        ```
        """
        ...

    def long_running_list(self, *cmds: str | Iterable) -> list[CmdRecording[str]]:
        """同时初始化并运行多个多线程命令"""
        res = []
        if len(cmds) == 1 and isinstance(cmds[0], Iterable):
            cmds = tuple(cmds[0])
        for e in cmds:
            res.append(self.long_running(e))
        return res

    def create_ftp(self) -> SFTP:
        """创建sftp"""
        sftp = SFTP(self)
        self.sftp.append(sftp)
        return sftp


@collect(CollectType.Channel, CollectObj)
class Channel:
    """通道类，用于管理SSH通道"""

    class_id = 0  # 用于给没有指定名称的通道生成id
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
        prompt_pattern: str | None = None,
        show_welcome_info: bool = False,
        insert_cmd: str | None = None,
    ):
        """初始化通道，需要指定SSH"""
        # create record
        self.name = name if name else "ch_" + str(Channel.id_generator())
        self.meta_record = MetaRecord(
            type="Channel", name=self.name, info=ssh.meta_record.info
        )
        self.shell = ssh.remote.invoke_shell()
        prompt_pattern = (
            Channel.prompt_pattern_default if prompt_pattern is None else prompt_pattern
        )
        self.prompt_complie = re.compile(prompt_pattern)
        self.cmds: list[CmdRecord[str]] = []

        # 处理初始化通道时产生的默认输出，并获终端取提示符
        string = ""
        self.shell.send(bytes(insert_cmd + "\n", "utf-8")) if isinstance(
            insert_cmd, str
        ) else None
        tmp_timestamp = time.time()
        tmp_timeout = 3
        tmp_f_switched_bash = False
        while True:  # 显示有bug，未测试
            if self.shell.recv_ready():
                welcome_info = self.shell.recv(65535).decode()
                string += welcome_info

                if show_welcome_info:
                    Term.puts_msg(welcome_info)
                    # print(welcome_info)

                if tmp := self.prompt_complie.search(remove_ansi(string)):
                    break
            time.sleep(0.01)
            if time.time() - tmp_timestamp > tmp_timeout and not tmp_f_switched_bash:
                self.shell.send(bytes("bash\n", "utf-8"))
                self.meta_record.logs.append(
                    Term.puts_msg(
                        f"{AnsiColor.yellow}[Warning]{AnsiReset}: prompt not found for {tmp_timeout}s, switching to bash\n"
                    )
                )
                tmp_f_switched_bash = True
                # print()

        prompt = tmp.group().replace("\r", "")

        self.f_get_prompt = True if self.prompt_complie.search(prompt) else False
        self.prompt_now = prompt
        # print(f"DBG:prompt_now = {prompt}")
        self.meta_record.logs.append(
            Term.putsln(f"{self.meta_record.get_fmt_prompt()} Created")
        )

    def set_name(self, name: str):
        """设置通道名称"""
        self.name = name
        self.meta_record.name = name

    def run(self, cmd: str) -> CmdRecord[str]:
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
        # res = ""  # 有效输出

        record = CmdRecord[str](cmd, f"[{self.name}]{self.prompt_now}")
        self.cmds.append(record)
        record.start_time, _ = Term.putsln(record.get_fmt_prompt())
        self.shell.send(
            bytes(cmd + "\r\n", "utf-8")
        )  # 发送的字符同样会进入接收当中，需要去重

        while True:
            if self.shell.recv_ready():  # 缓冲非空
                rcv = self.shell.recv(65535)  # 接收

                buf += rcv  # 存入buf
                while b"\r\n" in buf or b"\n" in buf:  # buf中有换行符就一直处理
                    buf = buf.replace(b"\r\n", b"\n")  # 统一换行符
                    line_b, buf = buf.split(b"\n", 1)  # 获取buf中的第一行
                    line = line_b.decode().strip().replace("\r", "")

                    if (
                        len(cmd_lines) == 0 and not f_cmd_lines_skip
                    ):  # 未处理的多行命令为空并且命令处理完成标志未置位
                        f_cmd_lines_skip = True  # 标志置位

                    if (
                        not f_cmd_lines_skip  # 命令处理完成标志未置位
                        and cmd_lines[0] in remove_ansi(line)  # 命令行与当前行相等
                        and len(cmd_lines) > 0  # 命令行未处理完毕
                    ):
                        cmd_lines.pop(0)  # 弹出处理完的命令
                        continue
                    if self.prompt_complie.search(
                        remove_ansi(line)
                    ):  # 当前行与命令行提示符匹配
                        self.prompt_now = remove_ansi(line).strip(
                            "\r\n "
                        )  # 更新命令行提示符
                        f_prompt_received = True  # 命令行提示符处理完成标志置位
                        break
                    record.result.append(Term.putsln(line))
                if f_prompt_received:
                    break

            time.sleep(0.005)

        record.record_end()
        record.exit_code = self._get_exit_code()
        return record

    @overload
    def run_lines(self, cmds: list[str]) -> list[CmdRecord[str]]:
        """执行多行命令，返回命令记录列表"""
        ...

    @overload
    def run_lines(self, cmds: str) -> list[CmdRecord[str]]:
        """执行多行命令，输入是带有换行符的字符串

        如果无换行符，会调用self.run执行单行命令，统一返回list[CmdRecord]
        """
        ...

    def run_lines(self, cmds: Union[list[str], str]) -> list[CmdRecord[str]]:
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

    def _get_exit_code(self):
        """获取上一条命令的退出码，退出码获取一次后清除\n
        运行echo $?实现，内部调用"""
        self._get_recv_buf()
        self.shell.send(b"echo $?\r\n")
        buf = b""
        got_cmd = False
        got_code = False
        got_end = False
        code = None
        while True:
            if self.shell.recv_ready():
                buf += self.shell.recv(65535)
                buf = buf.replace(b"\r\n", b"\n")
                while b"\n" in buf:
                    line_b, buf = buf.split(b"\n", 1)
                    line = line_b.decode().strip().replace("\r", "")
                    if "echo $?" in remove_ansi(line):
                        got_cmd = True
                        continue

                    if got_cmd and not got_code:
                        code = int(remove_ansi(line))
                        got_code = True
                        continue

                    if self.prompt_complie.search(
                        remove_ansi(line)
                    ):  # 当前行与命令行提示符匹配
                        self.prompt_now = remove_ansi(line).strip(
                            "\r\n "
                        )  # 更新命令行提示符
                        got_end = True  # 命令行提示符处理完成标志置位
                        break
            if got_end:
                break
        if got_code and got_cmd and got_end and code is not None:
            return code

    def _get_recv_buf(self) -> bytes | None:
        if self.shell.recv_ready():
            return self.shell.recv(65535)


@collect(CollectType.SFTP, CollectObj)
class SFTP:
    """继承自paramiko的SFTPClient，实现时间戳记录，用法与SFTPClient基本一致\n
    套壳实现了大部分同名方法，修改了部分有返回值的方法，以保持风格一致"""

    def __init__(self, ssh: SSH):
        self.meta_record = MetaRecord(
            type="SFTP",
            name=ssh.name,
            info=ssh.meta_record.info,
        )
        self.name = ssh.name
        self.ssh = ssh
        # self.tmp_channel = ssh.remote.open_sftp().get_channel()
        self.prompt = f"[{self.meta_record.name}][{self.meta_record.type}] >>>"
        self.cmds: list[CmdRecord] = []
        # self.aty_channel = Channel(ssh)
        self.sftp = ssh.remote.open_sftp()
        self.meta_record.logs.append(
            Term.putsln(self.meta_record.get_fmt_prompt() + " Opened")
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.meta_record.logs.append(
            Term.putsln(self.meta_record.get_fmt_prompt() + " Closed")
        )
        self.sftp.close()
        return False

    # def create_channel(self, *args, **kwargs) -> Channel:
    #     """创建一个新的Channel对象，用于执行命令\n
    #     name: 通道名称，用于标识"""
    #     return Channel(self.aty_ssh, *args, **kwargs)

    def listdir(self, path: str = ".") -> CmdRecord[str]:
        record = CmdRecord[str](
            cmd=f"listdir {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.listdir(path)
        for dir in res:
            record.result.append(Term.putsln(dir))
        record.record_end()
        return record

    def listdir_attr(self, path: str = ".") -> CmdRecord[SFTPAttributes]:
        record = CmdRecord[SFTPAttributes](
            cmd=f"listdir_attr {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.listdir_attr(path)
        for attr in res:
            t, _ = Term.putsln(str(attr))
            record.result.append((t, Result(attr)))
        record.record_end()
        return record

    def listdir_iter(
        self, path: bytes | str = ".", read_aheads: int = 50
    ) -> CmdRecord[Iterator[SFTPAttributes]]:
        record = CmdRecord[Iterator[SFTPAttributes]](
            cmd=f"listdir_iter {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())

        res = self.sftp.listdir_iter(path, read_aheads)
        record.result_append(res)
        record.record_end()
        return record

    def open(
        self, filename: bytes | str, mode: str = "r", bufsize: int = -1
    ) -> CmdRecord[SFTPFile]:
        record = CmdRecord[SFTPFile](
            cmd=f"open {filename} {mode} {bufsize}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.open(filename, mode, bufsize)
        record.result_append(res)
        record.record_end()
        return record

    def remove(self, path: bytes | str) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"remove {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.remove(path)
        record.record_end()
        return record

    def rename(self, oldpath: bytes | str, newpath: bytes | str) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"rename {oldpath} {newpath}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.rename(oldpath, newpath)
        record.record_end()
        return record

    def posix_rename(
        self, oldpath: bytes | str, newpath: bytes | str
    ) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"posix_rename {oldpath} {newpath}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.posix_rename(oldpath, newpath)
        record.record_end()
        return record

    def mkdir(self, path: bytes | str, mode: int = 0o777) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"mkdir {path} {mode}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        self.sftp.mkdir(path, mode)
        record.record_end()
        return record

    def rmdir(self, path: bytes | str) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"rmdir {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.rmdir(path)
        record.record_end()
        return record

    def stat(self, path: bytes | str) -> CmdRecord[SFTPAttributes]:
        record = CmdRecord[SFTPAttributes](
            cmd=f"stat {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.stat(path)
        record.result_append(res)
        record.record_end()
        return record

    def lstat(self, path: bytes | str) -> CmdRecord[SFTPAttributes]:
        record = CmdRecord[SFTPAttributes](
            cmd=f"lstat {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.lstat(path)
        record.result_append(res)
        record.record_end()
        return record

    def symlink(self, source: bytes | str, dest: bytes | str) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"symlink {source} {dest}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.symlink(source, dest)
        record.record_end()
        return record

    def chmod(self, path: bytes | str, mode: int) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"chmod {path} {mode}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.chmod(path, mode)
        record.record_end()
        return record

    def chown(self, path: bytes | str, uid: int, gid: int) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"chown {path} {uid} {gid}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.chown(path, uid, gid)
        record.record_end()
        return record

    def utime(
        self, path: bytes | str, times: tuple[float, float] | None
    ) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"utime {path} {times}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.utime(path, times)
        record.record_end()
        return record

    def truncate(self, path: bytes | str, size: int) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"truncate {path} {size}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        self.sftp.truncate(path, size)
        record.record_end()
        return record

    def readlink(self, path: bytes | str) -> CmdRecord[str | None]:
        record = CmdRecord[str | None](
            cmd=f"readlink {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.readlink(path)
        record.result_append(res)
        record.record_end()
        return record

    def normalize(self, path: bytes | str) -> CmdRecord[str]:
        record = CmdRecord[str](
            cmd=f"normalize {path}",
            prompt=self.prompt,
        )
        self.cmds.append(record)
        Term.putsln(record.get_fmt_prompt())
        res = self.sftp.normalize(path)
        record.result_append(res)
        record.record_end()
        return record

    def chdir(self, path: None | bytes | str = None) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"chdir {path}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        self.sftp.chdir(path)
        record.record_end()
        return record

    def getcwd(self) -> CmdRecord[str | None]:
        record = CmdRecord[str | None](
            cmd="getcwd",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        res = self.sftp.getcwd()
        Term.putsln(str(res))
        record.result_append(res)

        record.record_end()
        return record

    def putfo(
        self,
        fl: IO[bytes],
        remotepath: bytes | str,
        file_size: int = 0,
        callback: _Callback | None = None,
        confirm: bool = True,
    ) -> CmdRecord[SFTPAttributes]:
        record = CmdRecord[SFTPAttributes](
            cmd=f"putfo {remotepath}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        res = self.sftp.putfo(fl, remotepath, file_size, callback, confirm)
        record.result_append(res)
        record.record_end()
        return record

    def put(
        self,
        localpath: StrOrBytesPath,
        remotepath: bytes | str,
        callback: _Callback | None = None,
        confirm: bool = True,
    ) -> CmdRecord[SFTPAttributes]:
        record = CmdRecord[SFTPAttributes](
            cmd=f"put {localpath} {remotepath}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        res = self.sftp.put(localpath, remotepath, callback, confirm)
        Term.putsln(str(res))
        record.result_append(res)
        record.record_end()
        return record

    def getfo(
        self,
        remotepath: bytes | str,
        fl: IO[bytes],
        callback: _Callback | None = None,
        prefetch: bool = True,
        max_concurrent_prefetch_requests: int | None = None,
    ) -> CmdRecord[int]:
        record = CmdRecord[int](
            cmd=f"getfo {remotepath}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        res = self.sftp.getfo(
            remotepath, fl, callback, prefetch, max_concurrent_prefetch_requests
        )
        t, _ = Term.putsln(str(res))
        record.record_end()
        record.result_append(res, t)
        return record

    def get(
        self,
        remotepath: bytes | str,
        localpath: StrOrBytesPath,
        callback: _Callback | None = None,
        prefetch: bool = True,
        max_concurrent_prefetch_requests: int | None = None,
    ) -> CmdRecord[None]:
        record = CmdRecord[None](
            cmd=f"get {remotepath} {localpath}",
            prompt=self.prompt,
        )
        Term.putsln(record.get_fmt_prompt())
        self.cmds.append(record)
        self.sftp.get(
            remotepath, localpath, callback, prefetch, max_concurrent_prefetch_requests
        )
        record.record_end()
        return record

    def auto_mkdir(self, path: str) -> None:
        """自动创建目录，如果目录已存在则不做任何操作"""
