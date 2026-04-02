# from pprint import pprint

import autestoy as at

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

    ch.run("cd project/autestoy_sim/")
    with conn.create_ftp() as ftp:
        ftp.chdir("project/autestoy_sim/")
        if "ftp_test" in map(lambda x: x[1].get(), ftp.listdir().result):
            try:
                ftp.getcwd()
                ftp.remove("ftp_test")
            except Exception as e:
                print(e)
                ch.run("rm -rf ./ftp_test")
        ftp.mkdir("ftp_test")
        res = ftp.put("./main.py", "ftp_test/main.py")
        res = ftp.listdir_attr()

        # ftp.aty_channel.run("pwd")

    ch.run("cd ftp_test/")
    ch.run("ls")
