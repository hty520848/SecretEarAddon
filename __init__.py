'''
Description: 
Date: 2024-01-11 19:03:07
LastEditTime: 2024-01-11 22:46:21
FilePath: /SecretEarAddon/__init__.py
'''
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
'''
打磨模块:
    该模块主要使用 右耳(导入文件名)  DamoReset  DamoCopy
    右耳是当前操作的物体,DamoReset主要用于重置打磨的物体,DamoCopy主要用于保存打磨的最后操作,主要用于模块间切换到打磨模式时的恢复

局部加厚模块:
    该模块主要使用 右耳(导入文件名)  LocalThickCompare   LocalThickCopy 三个模型
    右耳是当前操作的物体,LocalThickCompare主要用来作为加厚过程中的模型对比,LocalThickCopy主要用来重置局部加厚模块和模块切换间局部加厚的恢复

切割模块:
    环切:  该模块主要使用 右耳(导入文件名)  Tours   Circle  右耳huanqieCompare
           右耳是当前操作的物体,Tours时可用于操作和移动的圆环,Circle主要用来切割且由Tours生成,右耳huanqieCompare则是用于对比的透明物体
    侧切： 该模块主要使用 右耳(导入文件名) StepCutsphere1, StepCutsphere2,StepCutsphere3,StepCutsphere4,右耳ceqieCompare
           右耳是当前操作的物体, StepCutsphere是用于操作的四个圆球, StepCutplane是用于切割的平面,右耳ceqieCompare则是用于对比的透明物体
'''
import bpy
from . import (
    damo,
    jiahou,
    ui,
    prop,
    public_operation,
    qiege,
    label,
    handle,
    point
)
bl_info = {
    "name": "SecretEar",
    "author": "HDU",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


if "bpy" in locals():
    import importlib
    reloadable_modules = [
        "ui",
        "prop"
        "damo"
        "jiahou"
        "public_operation"
        "qiege"
        "tool"
        "label"
        "handle"
        "point"
    ]
    # reload()函数重新载入模块，调试时加载的模块发生改变时，
    for module in reloadable_modules:
        if module in locals():
            importlib.reload(locals()[module])


# 导入同级目录下的.py文件


def register():
    ui.register()
    damo.register()
    jiahou.register()
    prop.register()
    public_operation.register()
    qiege.register()
    label.register()
    handle.register()
    point.register()


def unregister():
    ui.unregister()
    damo.unregister()
    jiahou.unregister()
    public_operation.unregister()
    qiege.unregister()
    label.unregister()
    handle.unregister()
    point.unregister()


if __name__ == "__main__":
    register()
