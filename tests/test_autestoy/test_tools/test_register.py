from autestoy.tools.datatype import Addr32, Bits
from autestoy.tools.register import Field, RegGroup, Register, dataclass


@dataclass(slots=True)
class R32_PWR_CTLR(Register):
    VSEL_VIO18 = Field(
        bit_range=(12, 10),
        default=Bits(0, 3),
        select={
            Bits(0b000, 3): "1.2V",
            Bits(0b001, 3): "1.8V",
            Bits(0b010, 3): "2.5V",
            Bits(0b011, 3): "3.3V",
            Bits(0b100, 3): "VIO18 断电，且有 10mA 放电",
            Bits(0b101, 3): "VIO18 断电，输出浮空",
            Bits(0b110, 3): "VIO18 断电，输出浮空",
            Bits(0b111, 3): "VIO18 断电，输出浮空",
        },
        R=True,
        W=True,
        info="""VIO18 电源调节位;注：VIO18 由低压切换到高压时，VDDIO 引脚电容须远大于VIO18 引脚的累计电容量，以减缓 VIO18 升压瞬间 VDDIO 的电压跌落,且 VDD33 须不小于 2.7V。""",
    )
    VIO_SW_CR = Field(
        bit_range=(9, 9),
        default=Bits(0, 1),
        select={
            Bits(True): "通过 VSEL_VIO18 软件配置",
            Bits(False): "XO 外部下拉电阻硬件配置",
        },
        R=True,
        W=True,
        info="VIO18 电源调节方式选择位;",
    )
    DBP = Field(
        bit_range=(8, 8),
        default=Bits(0, 1),
        select={
            Bits(True): "使能对后备区域的寄存器的访问",
            Bits(False): "禁止对后备区域的寄存器的访问",
        },
        R=True,
        W=True,
        info="""后备区域的写使能：在复位状态下，后备区域的寄存器均受到写访问保护。必须将此位置 1 才能对这些寄存器进行写访问。""",
    )
    PLS = Field(
        bit_range=(7, 5),
        default=Bits(0, 3),
        select={
            Bits(0b000, 3): "上升沿 2.54V/下降沿 2.44V",
            Bits(0b001, 3): "上升沿 2.6V/下降沿 2.49V",
            Bits(0b010, 3): "上升沿 2.7V/下降沿 2.59V",
            Bits(0b011, 3): "上升沿 2.8V/下降沿 2.69V",
            Bits(0b100, 3): "上升沿 2.9V/下降沿 2.79V",
            Bits(0b101, 3): "上升沿 3.0V/下降沿 2.89V",
            Bits(0b110, 3): "上升沿 3.1V/下降沿 2.99V",
            Bits(0b111, 3): "上升沿 3.2V/下降沿 3.09V",
        },
        R=True,
        W=True,
        info="""PVD 电压监测阈值设置。详细说明见数据手册中电气特性部分。""",
    )
    PVDE = Field(
        bit_range=(4, 4),
        default=Bits(0, 1),
        select={
            Bits(True): "电压调节器工作在低功耗模式",
            Bits(False): "电压调节器工作在正常模式",
        },
        R=True,
        W=True,
        info="""电源电压监测功能使能位""",
    )
    LPDS = Field(
        bit_range=(0, 0),
        default=Bits(0, 1),
        select={
            Bits(True): "电压调节器工作在低功耗模式",
            Bits(False): "电压调节器工作在正常模式",
        },
        R=True,
        W=True,
        info="""停止模式下，电压调节器工作模式选择位。""",
    )


@dataclass(slots=True)
class ALL_GROUP(RegGroup):
    R32_PWR_CTLR = R32_PWR_CTLR(address=Addr32(0x4000_7000), info="电源控制寄存器")


Reg = ALL_GROUP(Addr32(0), Addr32(0x1FFF_FFFF))


Reg.R32_PWR_CTLR.VIO_SW_CR.select
