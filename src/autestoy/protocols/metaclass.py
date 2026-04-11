"""提供协议绑定、通用方法，需要使用者自行配置"""

from typing import Callable, Type, TypeVar, Union

from .jtag import Jtag
from .serial import Serial
from .ssh import SSH
from .telnet import Telnet

Protocol = Union[SSH, Telnet, Jtag, Serial]
P = TypeVar("P", SSH, Telnet, Jtag, Serial)


class DUTConfiguratorBase:
    """DUT配置器基类，提供协议绑定、通用方法，考虑多个重复类型的协议绑定\n
    应将其视作对于具体产品测试的配置基类\n
    用户继承此类进行产品测试行为细节的规定"""

    def __init__(self, *protocols: Protocol):
        """初始化参数传入需要操作的协议实例"""
        self.protocols: list[Protocol] = list(protocols)  # 存储协议实例
        self.dynamic_methods: dict[str, Callable] = {}  # 存储动态方法

    def get_protocol(self, protocol_type: Type[P]) -> list[P]:
        """获取指定类型的协议实例，实例存在返回所有该类型实例的列表，实例不存在返空列表"""
        res = []
        for p in self.protocols:
            if isinstance(p, protocol_type):
                res.append(p)
        return res

    def get_from_name(self, protocol_type: Type[P], name: str) -> P:
        """通过协议名称获取协议实例，实例存在返回该实例，实例不存在抛出异常"""
        for p in self.protocols:
            if isinstance(p, protocol_type) and p.name == name:
                return p
        raise KeyError(f"No protocol of name '{name}' found")

    def is_protocol_exist(self, protocol_type: Type[P]) -> bool:
        """判断是否存在指定类型的协议实例"""
        for p in self.protocols:
            if isinstance(p, protocol_type):
                return True
        return False

    def __getitem__(self, protocol: Type[P]) -> list[P]:
        """支持通过`self[Protocol]`语法获取协议实例列表\n
        获取失败会抛出异常"""
        res = self.get_protocol(protocol)
        if len(res) == 0:
            raise KeyError(f"No protocol of type {protocol} found")
        return res

    def __contains__(self, protocol_type_or_name: Type[P] | str) -> bool:
        """支持通过`Protocol in self`语法判断是否存在指定类型的协议实例"""
        if isinstance(protocol_type_or_name, str):
            return any(p.name == protocol_type_or_name for p in self.protocols)
        elif isinstance(protocol_type_or_name, type):
            return self.is_protocol_exist(protocol_type_or_name)

        else:
            raise TypeError(
                f"Unsupported type {type(protocol_type_or_name)} for protocol type"
            )
            # return False

    def __getattr__(self, name: str) -> Protocol:
        """支持通过`self.name`语法获取协议实例，实例存在返回该实例，实例不存在抛出异常\n
        需要使用者自行进行类型判断"""
        for p in self.protocols:
            if p.name == name:
                return p
        raise AttributeError(f"No protocol of name '{name}' found")
