"""实现脚本输出收集，通过装饰器等"""

from functools import wraps


def collect(storage_dict: dict):
    """
    类装饰器：将每个实例添加到 storage_dict 中。要求类的实例拥有name属性作为字典的键
    """

    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            storage_dict[self.name] = self  # 实例创建后立即保存

        cls.__init__ = new_init
        return cls

    return decorator
