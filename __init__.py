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

import bpy
from . import (
    damo,
    jiahou,
    ui,
    prop,
    test
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
        "test"
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
    test.register()


def unregister():
    ui.unregister()
    damo.unregister()
    jiahou.unregister()
    test.unregister()


if __name__ == "__main__":
    register()
