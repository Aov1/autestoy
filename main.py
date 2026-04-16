# #!/usr/bin/env python3
# import sys
# import threading
# import time

# import paramiko
# import serial


# def bridge(serial_port, ssh_host, ssh_user, ssh_pass=None, ssh_keyfile=None):
#     """串口与 SSH 之间的双向桥接"""

#     # 1. 打开串口（可根据需要调整波特率等）
#     ser = serial.Serial(
#         port=serial_port,
#         baudrate=115200,
#         timeout=0.1,  # 非阻塞读取
#         parity=serial.PARITY_NONE,
#         stopbits=serial.STOPBITS_ONE,
#         bytesize=serial.EIGHTBITS,
#     )
#     print(f"串口 {serial_port} 已打开")

#     # 2. 建立 SSH 连接
#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     if ssh_keyfile:
#         ssh.connect(ssh_host, username=ssh_user, key_filename=ssh_keyfile)
#     else:
#         ssh.connect(ssh_host, username=ssh_user, password=ssh_pass)
#     # 打开交互式 shell 通道（获得类似终端的流）
#     channel = ssh.invoke_shell(term="xterm")
#     channel.settimeout(0.1)
#     print(f"已连接到 SSH {ssh_user}@{ssh_host}")

#     # 标志，用于停止线程
#     running = [True]

#     # 3. 定义转发函数：串口 → SSH
#     def serial_to_ssh(running):
#         while running[0]:
#             try:
#                 data = ser.read(1024)
#                 if data:
#                     channel.send(data)
#             except Exception as e:
#                 print(f"串口读取错误: {e}")
#                 running[0] = False
#                 break
#         print("串口→SSH 线程结束")

#     # 4. 定义转发函数：SSH → 串口
#     def ssh_to_serial(running):
#         while running[0]:
#             try:
#                 if channel.recv_ready():
#                     data = channel.recv(4096)
#                     if data:
#                         ser.write(data)
#                         ser.flush()
#             except Exception as e:
#                 print(f"SSH 读取错误: {e}")
#                 running[0] = False
#                 break
#         print("SSH→串口 线程结束")

#     # 5. 启动两个线程
#     t1 = threading.Thread(target=serial_to_ssh, args=(running,), daemon=True)
#     t2 = threading.Thread(target=ssh_to_serial, args=(running,), daemon=True)
#     t1.start()
#     t2.start()

#     # 6. 等待用户 Ctrl+C
#     try:
#         while True:
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         print("\n正在关闭桥接...")
#         running = False
#         t1.join(timeout=1)
#         t2.join(timeout=1)
#         channel.close()
#         ssh.close()
#         ser.close()
#         print("已关闭")


# if __name__ == "__main__":
#     # 配置参数
#     SERIAL_PORT = "/dev/tty"  # 你的串口设备（或虚拟串口 /dev/pts/xxx）
#     SSH_HOST = "127.0.0.1"
#     SSH_USER = "aoiiix"
#     SSH_PASS = "0402"  # 或使用密钥文件
#     SSH_KEY = None  # 例如 "/home/user/.ssh/id_rsa"

#     bridge(SERIAL_PORT, SSH_HOST, SSH_USER, SSH_PASS, SSH_KEY)
