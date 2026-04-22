from __future__ import annotations

import weakref
from dataclasses import dataclass, fields
from typing import Dict, Generic, Optional, Type, TypeVar

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


@dataclass
class Field(HasParent):
    """寄存器字段"""

    range: tuple[int, int] = (0, 0)
    width: int = 0
    default: int = 0

    @property
    def uReg(self) -> Register:
        return self._find_up(Register)

    @property
    def uGup(self) -> RegGroup:
        return self._find_up(RegGroup)


@dataclass
class Register(HasParent):
    address: int

    def __post_init__(self):
        for f in fields(self):
            if f.name in ["address"]:
                continue
            attr = getattr(self, f.name)
            if isinstance(attr, Field):
                attr.set_parent(self)


@dataclass
class RegGroup(HasParent):
    range: tuple[int, int] = (0, 0)

    def __post_init__(self):
        for f in fields(self):
            if f.name in ["range"]:
                continue
            attr = getattr(self, f.name)
            if isinstance(attr, Register):
                attr.set_parent(self)


# use


@dataclass
class GLB_CTL(Register):
    address: int = 0x1234_5678
    MODE: Field = Field(range=(3, 0), width=4, default=0b0000)
    SPEED_SEL: Field = Field(range=(15, 4), width=12, default=0b1000_0000_0000)
    ID: Field = Field(range=(31, 16), width=16, default=0b0000_0000_0000_0000)


@dataclass
class SPI_CTL(Register):
    address: int = 0x1234_5600
    MODE_SEL: Field = Field(range=(3, 0), width=4, default=0b0000)
    SPEED_SEL: Field = Field(range=(15, 4), width=12, default=0b1000_0000_0000)
    SUB_ADDR: Field = Field(range=(31, 16), width=16, default=0b0000_0000_0000_0000)


@dataclass
class STM32_REG_GROUP(RegGroup):
    range: tuple[int, int] = (0, 0xFFFFFFFF)
    GLB_CTL: GLB_CTL = GLB_CTL()
    SPI_CTL: SPI_CTL = SPI_CTL()


STM32_REG = STM32_REG_GROUP()


reg = STM32_REG.GLB_CTL
print(f"{reg.address = }")
print(f"{reg.SPEED_SEL.default = }")
