# 简介

一个尝试用于特定场景的不专业(指作者)的原型验证自动化测试工具

名称一拍脑袋 auto+test+toy

处于早早早早期阶段

## 设计理念

- 协议支持保持可移植性，不应引入具体的细节支持，例如支持特定产品
- 考虑到使用环境，数据类切片应靠近verilog语法

# 项目结构

## 目前的src树


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

# 未来规划

- 尽快完善基础功能，至少完成一条完整的测试-显示-导出报告的流程
- 多环境测试
- 打包发布

### 畅想（coding过程中的灵光一动）
- 实现字段类，将寄存器拆为多个字段直接控制

# 快速开始
无

# 具体细节
（想到哪写到哪）

## protocols

### ssh

#### class SSH

- SSH

SSH实现了两套方法，一种是基于ssh连接的exec_run，每运行一次会创建一个通道，运行结束后销毁，所以无法保持上下文、路径等，运行效率稍低，但方便处理；
```python
remote_config = RemoteConfig(...)
dut = SSH(remote_config)
dut.exec_run('cd path') # 每次exec_run都会创建一个新的通道，因此这条cd命令只在此次命令中有效
# home/path/
dut.exec_run('pwd') # 再次运行pwd目录恢复到创建channel时的默认路径
# home
dut.set_globel_path('./path') # global_path是类内部维护的一个全局路径，等同于在所有命令前加入cd命令
dut.exec_run('pwd') # 等同于 "cd ./path && pwd"
# home/path/
dut.with_path('home/another_path/').exec_run('pwd') # with_path会设置一个只能执行一次的临时路径，使用exec_run后消失
# /home/another_path
dut.exec_run('pwd')
# /home/path
dut.cd('new_path') # cd方法作用于global_path，切换全局路径
dut.exec_run('pwd')
# /home/path/new_path
```
还实现了long_running即长时间后台运行命令，通过threading库实现多线程运行，以达成不阻塞后续命令运行的效果。使用fifo在进程间传递命令的输出，可以做到实时处理输出特征。
```python
process = dut.long_running('python create_log.py') # 设想这是一条可以持续产生log的脚本
tail_res = dut.long_running('tail -f log.txt') # 实时显示log输出
# 粗糙的处理流程，待改进
now = time.time()
while time.time() - now < 10: # 10s后退出
    if not tail_res.fifo.enpty() and 'fail' in tail_res.fifo.get(): # fifo非空且'fail' 在fifo中，则退出
        break
# 杀死进程：内部先使用stdin发送ctrl-c给远程退出信号，再运行td.Event.set()结束本地线程。
process.task_kill()
tail_res.task_kill()
# 查看进程状态，如果命令阻塞可能无法响应td.Event事件
print(process.long_running_task.is_alive())
print(tail_res.long_running_task.is_alive())
```

另一种是基于channel的交互式run方法，所有命令基于一个channel，可以保持上下文，效率高，但是处理复杂，需要自行识别命令行提示符号，不支持花里胡哨的命令行提示符。

channel的处理逻辑是根据正则表达式捕获命令行提示符，如果命令输出刚好匹配到了该正则，会导致输出处理提前结束，并影响后续命令。目前没有很好的解决方法。

```python
remote_config = RemoteConfig(...)
dut = SSH(remote_config)
dut_ch1 = dut.create_channel() 
# 如果远程环境使用了花里胡哨的终端，例如zsh {    ~/Project/autestoy ... ✔  autestoy  }这样子的提示符，并且在初始化channel时卡处
# 可以尝试设置insert_cmd参数，将在自动匹配终端提示符前发送一条命令
# 例如 ch1 = dut.create_channel(insert_cmd="bash")，这将切换为bash环境
dut_ch1.run('pwd')
# home
dut_ch1.run('cd path') # 在同一channel中运行，上下文继承
dut_ch1.run('pwd') 
# home/path
```

基于channel的实现无long_running方法，实现long_running即会占用该通道，不如直接创建新通道运行。

- 关于term输出的时间戳

时间戳大部分在获取返回内容并处理完成后输出时添加，所以并不代表命令输出的实际精确时间。但也可以一定程度上反映多线程语句输出的前后关系。

## tools

### datatype

#### class Bits

- 创建Bits：

Bits是为可以快速创建和修改特定位的数据类。以特定的切片格式快速访问和修改单个bit或bit字段。

1. 从int创建：

int无法反映数据宽度，必须指定width参数
```python
reg = Bits( 65535  , 16 ) # 0xFFFF      16bits
reg = Bits( 0x1234 , 8  ) # 0x34         8bits :发生高位截断
reg = Bits( 0b1111 , 32 ) # 0x0000_000F 32bits :高位补0
```
2. 从str创建：

带有位数标识的字符串可以省略width，也可以使用width重新指定宽度；

没有位数标识的字符串必须指定width；

```python
reg = Bits( "0x1234_u8"     ) # 0x34         8bits :字符串解析也会造成截断
reg = Bits( "0x1234_i8" , 16) # 0x0034      16bits :width指定宽度在字符串解析后作用，因此这种写法会并不会防止截断
reg = Bits( "0x1234"    , 32) # 0x0000_1234 32bits :字符串无宽度标识时，需要指定宽度
reg = Bits( "8'hFF"     , 8 ) # 0xFF         8bits :str支持verilog近似的语法，分隔副使用英文单引号，因此字符串使用双引号括起
reg = Bits( "2.5E4"     , 16) # 2500        16bits :科学计数法解析结果为float的字符串如果转换为int值不变，也可以被Bits接受
reg = Bits( "3.0E2_u8"      ) # 0x2C         8bits :也支持科学计数法+标注位数，可以不指定width，当然也受到截断影响
```
目前"u8"、"i8"等有符号/无符号标识没有作区别处理。

3. 从可迭代对象创建：

可迭代对象的子类型可以是任意上述创建方法，需要指定宽度的传入元组携带参数，返回所有对象的拼接Bits
```python
reg = Bits([ "8'hFF" , (0xAB,8) , ("255",8) , "0b0001_0010_i8"])
# reg -> 0xFFAB_FF12 32bits , 
```
- Bits切片：

Bits切片遵循类似verilog的语法。

1. Bits[n] 返回单比特，默认右侧低位
```python
reg = Bits(0b0001_0000 , 8)
reg[3]  -> Bits(0b0,1) # 默认右侧低位，第4位
reg[3:] -> Bits(0b0,1) # 指定右侧低位，第4位
reg[:3] -> Bits(0b1,1) # 指定左侧低位，第4位
```
2. Bits[a:b] a>b 右侧为低位 ； a<b 左侧为低位
```python
reg = Bits( 0x1234_5678 , 32 )
reg[15:0] == res[16:31] == Bits( 0x5678 , 16 )
reg[0:15] == reg[31:16] == Bits( 0x1234 , 16 )
```
3. Bits[ a:b , c ...] 混合切片拼接
```python
reg = Bits( 0x1234_5678 , 32 )
# 单bit拼接
reg[ 3 , 2 , 1 , 0 ] == reg[ 3: , 2: , 1: , 0: ] == reg[3:0] == Bits( 0x8 , 4 )
# 切片拼接
reg[ 7:0 , 0:7] == Bits( 0x7812 , 16 )
# 混合拼接
reg[ :0 , 1:2 , :3 ] == reg[0:3] == Bits( 0x1 , 4 )
```


# ToDoList

- [ ] 为ssh-Channel.run/SSH.exec_run实现短交互命令，例如sudo登陆
- [x] ssh-SSH/Channel类初始化添加时间戳记录，考虑新的Record类:MataRecord?

- [ ] 统一测试文件，运行时使用ftp传输运行脚本到远程被测试端，测试完成后删除
	- [ ] ftp服务
  	- [x] 继承并添加Record
	- [ ] 文件hash校验

- [x] 记录每一行命令输出的时间戳
	- [x] Result-CmdRecord、CmdRecording为每一行输出添加时间戳
	- [x] 更改print函数->可拓展是否显示时间戳，更改样式
	- [x] 实现Timestamp类，替代time.time()

- [ ] 数据类-完善
	- [x] np.array(uint8) 数据转换，bit切片转换 -> numpy引入处理复杂度，无极端速度需求，去除
	- [ ] Bits
  	- [ ] 切片
    - [ ] 段赋值
	- [ ] Binary(Bits)
	- [ ] Hexadecimal(Bits)
	- [ ] Decimal(Bits)
	- [ ] Field(Bits)：寄存器子字段Bits
	- [ ] Register(Bits+)：带有字段的定长，
	- [ ] Packet(Bits)：带有字段的数据包类

- [x] BUG:ssh的channel模式run方法，概率性出现回显去除失败。
- [x] BUG:ssh-create_channel遇到zsh等进行了美化的终端时获取不到prompt死循环->嵌入bash

# 已知问题

- SFTP.remove(path) always Fail at Huawei Matepad
-
