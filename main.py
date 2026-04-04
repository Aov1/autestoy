# from pprint import pprint


import autestoy as at

pad = at.RemoteConfig(
    user="u0_a210",
    ip="192.168.18.6",
    password="0402",
    port=8022,
).set_name("Huawei Matepad")

local = at.RemoteConfig(user="aoiiix", ip="127.0.0.1", password="0402").set_name(
    "Local"
)

dut_workpath = "project/"
loc_workpath = "/home/aoiiix/Code/Test/"
pyrun = "pyrun.py"
with open(loc_workpath + pyrun, "a") as f:
    f.writelines(
        [
            "import time\n",
            "import sys\n",
            "import random\n",
            "args = sys.argv\n",
            "if len(args) >= 3:\n",
            "    t = float(args[1])\n",
            "    n = int(args[2])\n",
            "else:\n",
            "    t = 0.2\n",
            "    n = 5\n",
            "for i in range(n):\n",
            '    print(f"Times{i:>5}: {random.randint(0,0xFFFF_FFFF)}")\n',
            "    time.sleep(t)\n",
        ]
    )


with at.SSH(pad) as dut, at.SSH(local) as loc:
    dut.set_global_path(dut_workpath)
    loc.set_global_path(loc_workpath)
    loc.exec_run("rm -rf autestoy_test")
    dut.exec_run("rm -rf autestoy_test")
    loc.exec_run("mkdir autestoy_test")
    loc.exec_run(f"mv {pyrun} autestoy_test")

    with dut.create_ftp() as ftp:
        ftp.chdir(dut_workpath)
        ftp.mkdir("autestoy_test")
        ftp.put(
            loc_workpath + "autestoy_test/" + pyrun,
            "autestoy_test/" + pyrun,
        )
        ftp.listdir("autestoy_test")
        sh = ftp.open("autestoy_test/test.sh", "w")
        f = sh.result[0][1].get()
        f.write("echo hello world!\n")
        f.close()
        ftp.chmod("autestoy_test/test.sh", 0o777)

    res = dut.exec_run("ls autestoy_test")
    dut.exec_run("./autestoy_test/test.sh")

    res = dut.exec_run("python autestoy_test/pyrun.py 0.2 10")
    for t, r in res.result:
        print(t, r.get())
    loc.exec_run("rm -rf autestoy_test")
    dut.exec_run("rm -rf autestoy_test")
    loc.exec_run("ls")
    dut.exec_run("ls")


cmd_all: list[at.CmdRecord] = []
for name, ssh in at.SSH_collect.items():
    for cmd in ssh.cmds:
        cmd_all.append(cmd)
for name, channel in at.Channel_collect.items():
    for cmd in channel.cmds:
        cmd_all.append(cmd)
for name, sftp in at.SFTP_collect.items():
    for cmd in sftp.cmds:
        cmd_all.append(cmd)

cmd_all.sort(key=lambda x: x.start_time.to_float())
for e in cmd_all:
    print(e.id, e.start_time, e.end_time, e.cmd)
