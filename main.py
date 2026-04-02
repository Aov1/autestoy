import autestoy as at

conf = at.RemoteConfig(
    user="aoiiix",
    ip="127.0.0.1",
    password="0402",
    port=22,
).set_name("local")
conn = at.SSH(conf)
conn.exec_run('echo "Hello World"')
ch = conn.create_channel(insert_cmd=None)
# print(ch.prompt_now)
ch.run("ls")
ch.run("pwd")
