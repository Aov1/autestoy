# from autestoy import SSH, RemoteConfig, ulog
# from autestoy.export.obsidian import ObsidianExporter
# from autestoy.tools.local import Local

# pad = RemoteConfig(
#     user="u0_a210",
#     ip="192.168.18.6",
#     password="0402",
#     port=8022,
# ).set_name("Huawei Matepad")


# def main():
#     dut = SSH(pad)
#     pc = Local()
#     ch1 = dut.create_channel()
#     ftp = dut.create_ftp()
#     dut.exec_run("ls")
#     dut.exec_run("pwd")
#     pc.run("ls")
#     pc.run("pwd")
#     ch1.run("pwd")
#     ch1.run("ls")
#     ftp.getcwd()
#     ftp.listdir()
#     pc.run("asdasdasdasd")
#     ulog("END HERE")

#     ObsidianExporter("/home/aoiiix/ObsidianLib/note/").save()


# if __name__ == "__main__":
#     main()


from pprint import pprint

from autestoy import SSH, RemoteConfig, ulog

pad_conf = RemoteConfig(
    user="u0_a210",
    ip="192.168.18.6",
    password="0402",
    port=8022,
).set_name("Huawei Matepad")

dut = SSH(pad_conf)
dut.kill(3956)
ch = dut.create_channel()
ch.run("echo $$")
ulog(ch._get_channel_pid())
res = ch._command("""
ls
ls
ls
pwd
pwd
pwd
""")

pprint(res)
ulog(ch._command("echo $$"))
