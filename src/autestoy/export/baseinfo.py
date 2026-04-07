import inspect
import os


def get_script_full_path():
    return os.path.abspath(inspect.stack()[1].filename)


def get_script_dir():
    return os.path.dirname(get_script_full_path())


def get_script_name():
    return os.path.basename(get_script_full_path())
