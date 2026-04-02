from pprint import pprint

import autestoy as at
from autestoy.tools.result import Result

res = Result(123)
print(res.get())
print(res.type())
exit()

conf = at.RemoteConfig(
    user="u0_a210",
    ip="192.168.18.6",
    password="0402",
    port=8022,
).set_name("local")

with at.SSH(conf) as conn:
    conn.exec_run('echo "Hello World"')
    ch = conn.create_channel(insert_cmd=None)
    # print(ch.prompt_now)
    ch.run("ls")
    ch.run("pwd")

    with conn.create_ftp() as ftp:
        ftp.chdir("project/autestoy_sim/")
        if "ftp_test" not in ftp.listdir():
            ftp.mkdir("ftp_test/")
        else:
            at.Term.putsln("ftp_test already exists")
        res = ftp.put("./main.py", "ftp_test/main.py")
        ftp.listdir_attr()
        # ftp.aty_channel.run("pwd")

    ch.run("cd project/autestoy_sim/ftp_test/")
    ch.run("ls")
