import pickle
import inspect
import sys
from typing import Dict, Any


class GlobalVarManager:
    _instance = None
    _registered_vars: Dict[str, Dict[str, Any]] = {}  # 格式: {模块名: {变量名: 值}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, var_name: str, value: Any, module_name: str = None):
        """注册需要保存的全局变量"""
        if module_name is None:
            # 自动获取调用者的模块名
            frame = inspect.currentframe().f_back
            module_name = frame.f_globals['__name__']

        if module_name not in self._registered_vars:
            self._registered_vars[module_name] = {}

        self._registered_vars[module_name][var_name] = value

    def save_to_pickle(self, filename: str):
        """将所有注册的变量保存到pickle文件"""
        try:
            with open(filename, 'wb') as f:  # 注意是二进制写入模式
                pickle.dump(self._registered_vars, f)
            print(f"所有全局变量已保存到 {filename}")
        except Exception as e:
            print(f"保存pickle文件失败: {e}")
            return False
        return True

    def load_from_pickle(self, filename: str):
        """从pickle文件加载变量值"""
        try:
            with open(filename, 'rb') as f:  # 注意是二进制读取模式
                data = pickle.load(f)

            # 更新已注册的变量值
            for module_name, vars_dict in data.items():
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    for var_name, value in vars_dict.items():
                        if hasattr(module, var_name):
                            setattr(module, var_name, value)
                            # 更新管理器中的值
                            if module_name in self._registered_vars:
                                self._registered_vars[module_name][var_name] = value

            print(f"已从 {filename} 加载全局变量")
            return True
        except FileNotFoundError:
            print(f"警告: 文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"加载pickle文件失败: {e}")
            return False


# 创建全局单例管理器
global_manager = GlobalVarManager()