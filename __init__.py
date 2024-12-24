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
    该模块主要使用 右耳(导入文件名)  LocalThickCompare   LocalThickCopy  LocalThickLast四个模型
    右耳是当前操作的物体,LocalThickCompare主要用来作为加厚过程中的模型对比,LocalThickCopy主要用来重置局部加厚模块和模块切换间局部加厚的恢复
    LocalThickLast则用来记录最后的状态
切割模块:
    环切:  该模块主要使用 右耳(导入文件名)  Tours   Circle  右耳huanqieCompare
           右耳是当前操作的物体,Tours时可用于操作和移动的圆环,Circle主要用来切割且由Tours生成,右耳huanqieCompare则是用于对比的透明物体
    侧切： 该模块主要使用 右耳(导入文件名) StepCutsphere1, StepCutsphere2,StepCutsphere3,StepCutsphere4,右耳ceqieCompare
           右耳是当前操作的物体, StepCutsphere是用于操作的四个圆球, StepCutplane是用于切割的平面,右耳ceqieCompare则是用于对比的透明物体
'''
bl_info = {
    "name" : "SecretEar",
    "author" : "HDU",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

if "bpy" in locals():
    import importlib
    reloadable_modules = [
         "ui",
         "prop",
         "damo",
         "jiahou",
         "public_operation",
         "qiege",
         "tool",
         "label",
         "handle",
         "support",
         "sound_canal",
         "vent_canal",
         "casting",
         "sprue",
    ]
    #reload()函数重新载入模块，调试时加载的模块发生改变时，
    for module in reloadable_modules:
        if module in locals():
            importlib.reload(locals()[module])


#导入同级目录下的.py文件
from . import  (
    damo,
    jiahou,
    ui,
    prop,
    public_operation,
    label,
    handle,
    support,
    sound_canal,
    vent_canal,
    casting,
    sprue,
    last_damo,
    offset_cut
    )
from .create_tip import qiege, circle_smooth, step_smooth, cut_mould
from .create_mould import point, create_mould, collision
from .create_mould.hard_eardrum import hard_eardrum_offset_cut, hard_eardrum_bottom_fill
from .create_mould.soft_eardrum import thickness_and_fill, soft_eardrum_offset_cut
from .create_mould.frame_style_eardrum import frame_eardrum_offset_cut, frame_fill_inner_face
from .create_mould.shell_eardrum import shell_canal
from .create_mould.shell_eardrum import shell_eardrum_bottom_fill
# from .pymesh import pymesh
# from .tool import output_redirect

from .damo import register_damo_tools
from .jiahou import register_jiahou_tools
from .create_tip.qiege import register_qiege_tools
from .create_mould.point import register_point_tools
from .create_mould.create_mould import register_createmould_tools
from .create_mould.shell_eardrum.shell_canal import register_shellcanal_tools
from .create_mould.collision import register_collision_tools
from .sound_canal import register_soundcanal_tools
from .vent_canal import register_ventcanal_tools
from .label import register_label_tools
from .handle import register_handle_tools
from .support import register_support_tools
from .casting import register_casting_tools
from .sprue import register_sprue_tools
from .last_damo import register_lastdamo_tools
from .create_tip.cut_mould import register_cutmould_tools


def register():
    ui.register()
    damo.register()
    jiahou.register()
    prop.register()
    public_operation.register()
    qiege.register()
    label.register()
    handle.register()
    support.register()
    thickness_and_fill.register()
    point.register()
    create_mould.register()
    sound_canal.register()
    vent_canal.register()
    casting.register()
    sprue.register()
    last_damo.register()
    hard_eardrum_offset_cut.register()
    hard_eardrum_bottom_fill.register()
    # pymesh.register()
    circle_smooth.register()
    step_smooth.register()
    offset_cut.register()
    # soft_eardrum_offset_cut.register()
    cut_mould.register()
    # frame_eardrum_offset_cut.register()
    # frame_fill_inner_face.register()
    collision.register()
    shell_canal.register()
    shell_eardrum_bottom_fill.register()

    register_damo_tools()
    register_jiahou_tools()
    register_qiege_tools()
    register_label_tools()
    register_handle_tools()
    register_support_tools()
    register_point_tools()
    register_createmould_tools()
    register_soundcanal_tools()
    register_ventcanal_tools()
    register_casting_tools()
    register_sprue_tools()
    register_lastdamo_tools()
    register_cutmould_tools()
    register_shellcanal_tools()
    register_collision_tools()


def unregister():
    ui.unregister()
    damo.unregister()
    jiahou.unregister()
    public_operation.unregister()
    qiege.unregister()
    label.unregister()
    handle.unregister()
    support.unregister()
    thickness_and_fill.unregister()
    point.unregister()
    sound_canal.unregister()
    vent_canal.unregister()
    casting.unregister()
    sprue.unregister()
    last_damo.unregister()
    create_mould.unregister()
    hard_eardrum_offset_cut.unregister()
    hard_eardrum_bottom_fill.unregister()
    # pymesh.unregister()
    circle_smooth.unregister()
    step_smooth.unregister()
    offset_cut.unregister()
    # soft_eardrum_offset_cut.unregister()
    cut_mould.unregister()
    # frame_eardrum_offset_cut.unregister()
    # frame_fill_inner_face.unregister()
    collision.unregister()
    shell_canal.unregister()
    shell_eardrum_bottom_fill.unregister()


if __name__ == "__main__":
    register()
    # output_redirect()

