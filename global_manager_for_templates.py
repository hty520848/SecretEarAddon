import bpy
import json
import os
import inspect
import sys
from typing import Dict, Any, List


class GlobalVarManager:
    _instance = None
    _registered_vars: Dict[str, Dict[str, Any]] = {}  # 格式: {模块名: {变量名: 值}}
    _registered_scene_props: List[str] = []  # 要保存的场景属性名列表

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, var_name: str, value: Any, module_name: str = None):
        """注册需要保存的普通全局变量"""
        if module_name is None:
            frame = inspect.currentframe().f_back
            module_name = frame.f_globals['__name__']

        if module_name not in self._registered_vars:
            self._registered_vars[module_name] = {}

        self._registered_vars[module_name][var_name] = value

    def register_scene_prop(self, prop_name: str):
        """注册需要保存的场景属性"""
        if prop_name not in self._registered_scene_props:
            self._registered_scene_props.append(prop_name)
            print(f"已注册场景属性: {prop_name}")

    def save_to_json(self, filename: str):
        """保存所有注册的变量和场景属性"""
        try:
            data = {
                'registered_vars': self._registered_vars,
                'scene_props': {}
            }
            
            # 收集已注册的场景属性
            scene = bpy.context.scene
            for prop_name in self._registered_scene_props:
                if hasattr(scene, prop_name):
                    data['scene_props'][prop_name] = getattr(scene, prop_name)
                else:
                    print(f"警告: 场景属性 {prop_name} 不存在，跳过保存")
            
            with open(filename, 'w', encoding='utf-8') as f:  # 注意是二进制写入模式
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"所有注册变量和场景属性已保存到 {filename}")
            return True
            
        except Exception as e:
            print(f"保存json文件失败: {e}")
            return False

    def load_from_json(self, filename: str):
        """加载所有注册的变量和场景属性"""
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"文件 {filename} 不存在")
            if os.path.getsize(filename) == 0:
                raise ValueError(f"文件 {filename} 为空")
                
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 恢复普通变量
            if 'registered_vars' in data:
                for module_name, vars_dict in data['registered_vars'].items():
                    if module_name in sys.modules:
                        module = sys.modules[module_name]
                        for var_name, value in vars_dict.items():
                            if hasattr(module, var_name):
                                setattr(module, var_name, value)
                                if module_name in self._registered_vars:
                                    self._registered_vars[module_name][var_name] = value
            
            # 恢复场景属性
            if 'scene_props' in data:
                scene = bpy.context.scene
                for prop_name, value in data['scene_props'].items():
                    if hasattr(scene, prop_name):
                        setattr(scene, prop_name, value)
                    if prop_name not in self._registered_scene_props:
                        self._registered_scene_props.append(prop_name)
            
            print(f"已从 {filename} 加载所有数据")
            return True
            
        except Exception as e:
            print(f"加载失败: {e}")
            return False


# 创建全局单例管理器
global_var_manager = GlobalVarManager()