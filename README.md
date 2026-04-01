# 简介

一个尝试用于特定场景的不专业(指作者)的原型验证自动化测试工具

名称一拍脑袋 auto+test+toy

处于早早早早期阶段

## 设计理念
(有时候作者也得看看，要不然写着写着写歪了)

- 协议支持保持可移植性，不应引入具体的细节支持，例如支持特定产品
- 考虑到使用人群，数据类切片应靠近verilog语法

# 项目结构

## 目前的src树

（大部分是空的）

```bash
src
├── autestoy
│   ├── __init__.py       # 暴露API
│   ├── export            # 导出相关功能源码目录
│   │   ├── collect.py        # 收集器，用于记录的收集
│   │   ├── obsidian.py       # obsidian格式(markdown+mermaid)生成器
│   │   ├── pdf.py            # pdf报告生成器
│   │   ├── term.py           # 终端显示、样式、时间戳配置
│   │   └── web.py            # web报告生成器，暂定niegui
│   ├── protocols         # 测试通路协议相关源码目录
│   │   ├── ftp.py            # ftp服务，用于传输下载远程文件
│   │   ├── jtag.py           # jtag通路，作者相关知识储备较少，优先级降低
│   │   ├── serial.py         # 串口连接
│   │   ├── ssh.py            # ssh连接
│   │   └── telnet.py         # telnet协议连接
│   └── tools             # 工具源码目录
│       ├── ansi.py           # 终端显示ansi转义
│       ├── datatype.py       # 数据类，创建易于操作的寄存器值以及数据转换
│       ├── result.py         # 定义协议返回的结果，用于处理与报告生成
│       └── timestamp.py      # 时间戳工具
...
```

## 依赖关系

#todo 

```mermaid_

```


# 未来规划

- 尽快完善基础功能，至少完成一条完整的测试-显示-导出报告的流程
- 多环境测试
- 打包发布

### 畅想（coding过程中的灵光一动，不一定实现）
- 实现字段类，将寄存器拆为多个字段直接控制

# 快速开始
无

# 具体细节
（想到哪写到哪）

- ssh

ssh实现了两套方法，一种是基于ssh连接的exec_run，每运行一次会创建一个通道，运行结束后销毁，所以无法保持上下文、路径等，运行效率稍低，但方便处理；另一种是基于channel的交互式run方法，所有命令基于一个channel，可以保持上下文，效率高，但是处理复杂，需要自行识别命令行提示符号（目前的处理可能有bug）。

基于ssh的exec_run实现了long_running即长时间后台运行命令，通过threading库实现多线程运行，以达成非阻塞后续命令。使用fifo在进程间传递命令的输出，可以做到实时处理输出特征。

基于channel的实现无long_running方法，实现long_running即会占用该通道，不如直接创建新通道运行。

- 关于term输出的时间戳

时间戳大部分在获取返回内容并处理完成后输出时添加，所以并不代表命令输出的实际精确时间。但也可以一定程度上反映多线程语句输出的前后关系。

- Bits切片：
Bits是为可以快速创建和修改特定位的数据类。以特定的切片格式快速访问和修改单个bit或bit字段。

Bits切片遵循
1. Bits[n] 返回单比特，默认右侧低位
eg: reg = Bits(0b0001_0000 , 8)
reg[4]
2. Bits[a:b] a>b 右侧为低位 ； a<b 左侧为低位
例如 reg = Bits( 0x12345678 , 32 )
reg[15:0] == res[16:31] -> Bits( 0x5678 , 16 )
reg[0:15] == reg[31:16] -> Bits( 0x1234 , 16 )

BIts[]



# ToDoList

- [ ] 统一测试文件，运行时使用ftp传输运行脚本到远程被测试端，测试完成后删除
	- [ ] ftp服务
	- [ ] 文件hash校验

- [x] 记录每一行命令输出的时间戳
	- [x] Result-CmdRecord、CmdRecording为每一行输出添加时间戳
	- [x] 更改print函数->可拓展是否显示时间戳，更改样式
	- [x] 实现Timestamp类，替代time.time()

- [ ] 数据类-完善
	- [ ] np.array(uint8) 数据转换，bit切片转换
	- [ ] Bits
  	- [ ] 切片
    - [ ] 
	- [ ] Binary
	- [ ] Hex
	- [ ] Dec

- [x] BUG:ssh的channel模式run方法，概率性出现回显去除失败。
- [ ] 

# 已知问题

- 无
