from __future__ import annotations

import weakref
from dataclasses import dataclass, fields
from typing import Optional, Type, TypeVar

from .datatype import Addr32, Addr64, Bits

T = TypeVar("T")


class HasParent:
    """混入类，提供父节点引用（弱引用）"""

    _parent: Optional[weakref.ref] = None

    def set_parent(self, parent):
        self._parent = weakref.ref(parent)

    @property
    def parent(self):
        if self._parent is None:
            raise ValueError("Parent not set")
        return self._parent()

    def _find_up(self, parent_type: Type[T]) -> T:
        """向嵌套上级查找"""
        obj = self.parent
        while obj:
            if isinstance(obj, parent_type):
                return obj
            obj = obj.parent
        raise ValueError(f"No parent of type {parent_type} found")


@dataclass(slots=True)
class Field(HasParent):
    """寄存器字段"""

    bit_range: tuple[int, int]
    default: Bits = Bits(None)
    select: dict[Bits, str] = {}
    R: Optional[bool] = None
    W: Optional[bool] = None
    info: str = ""

    @property
    def width(self) -> int:
        return abs(self.bit_range[0] - self.bit_range[1]) + 1

    @property
    def uReg(self) -> Register:
        return self._find_up(Register)

    @property
    def uGup(self) -> RegGroup:
        return self._find_up(RegGroup)


@dataclass(slots=True)
class Register(HasParent):
    address: Addr32 | Addr64 | Bits
    info: str = ""
    _default_value: Bits = Bits(None)
    _default_pattern: Bits = Bits(None)
    _offset_from_base: Bits = Bits(None)

    @property
    def offset(self) -> Bits:
        if self._offset_from_base == Bits(None):
            raise ValueError("offset_from_base is not set")
        return self._offset_from_base

    def __post_init__(self):
        for f in fields(self):
            if f.name in [
                "address",
                "info",
                "_default_value",
                "_default_pattern",
                "_offset_from_base",
            ]:
                continue
            attr = getattr(self, f.name)
            if isinstance(attr, Field):
                attr.set_parent(self)

    @property
    def uGup(self) -> RegGroup:
        return self._find_up(RegGroup)

    @property
    def default(self) -> tuple[Bits, Bits]:
        """获取Field的默认值，返回tuple[default_pattern，default_value]"""
        self._default_value = Bits(None)
        self._default_pattern = Bits(None)
        for f in fields(self):
            if f.name in [
                "address",
                "info",
                "_default_value",
                "_default_pattern",
                "_offset_from_base",
            ]:
                continue
            attr = getattr(self, f.name)
            if isinstance(attr, Field):
                dft = attr.default
                if dft != Bits(None):
                    self._default_value.append(dft)
                    self._default_pattern.append(Bits(0, dft.width).max())
                else:
                    self._default_value.append(Bits(0, dft.width))
                    self._default_pattern.append(Bits(0, dft.width))
        return self._default_pattern, self._default_value


@dataclass(slots=True)
class RegGroup(HasParent):
    """寄存器组，支持嵌套类本身"""

    base_address: Addr32 | Addr64 | Bits
    end_address: Addr32 | Addr64 | Bits

    @property
    def range(self):
        return self.base_address, self.end_address

    def __post_init__(self):
        for f in fields(self):
            if f.name in ["range"]:
                continue
            attr = getattr(self, f.name)
            if isinstance(attr, (Register, RegGroup)):
                attr.set_parent(self)
            if isinstance(attr, Register):
                attr._offset_from_base = attr.address - self.base_address


user_help = """
本文件中的类用于定义地址空间枚举，参照了CH32H417 4GB inline address space 结构
结构：
Class-AddressSpace:
    .base_address : Addr32 | Addr64 | Bits
    .end_address : Addr32 | Addr64 | Bits
    .range : tuple[Addr32 | Addr64 | Bits, Addr32 | Addr64 | Bits]
    Class-RegGroup(s):
        .range : tuple[Addr32 | Addr64 | Bits, Addr32 | Addr64 | Bits]
        .base_address : Addr32 | Addr64 | Bits
        Class-Register:
            .address : Addr32 | Addr64 | Bits
            .offset : Bits
            .info : str
            .default : tuple[Bits, Bits]
            Class-Field:
                .bit_range : tuple[int,int]
                .default : Bits
                .info : str
                .select : dict[Bits,str]
    Class-MemGroup(s):
        .range : tuple[Addr32 | Addr64 | Bits, Addr32 | Addr64 | Bits]
        .base_address : Addr32 | Addr64 | Bits



"""
