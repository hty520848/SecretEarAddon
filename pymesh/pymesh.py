# import pymeshlab as ml
# import trimesh
import os
import shutil
import bpy
import bmesh
from mathutils import Vector
from ..tool import moveToRight, moveToLeft, getOverride, getOverride2
from ..public_operation import draw_font
from ..register_tool import register_tools
from pathlib import Path
from ..global_manager import global_manager
from ..public_operation import register_public_operation_globals
from ..damo import register_damo_globals
from ..jiahou import register_jiahou_globals
from ..create_tip.qiege import register_qiege_globals, load_qiege_globals
from ..sound_canal import register_soudncanal_globals
from ..vent_canal import register_ventcanal_globals
from ..handle import register_handle_globals
from ..label import register_label_globals
from ..casting import register_casting_globals
from ..support import register_support_globals
from ..sprue import register_sprue_globals
from ..create_tip.cut_mould import register_cut_mould_globals
from ..parameter import set_switch_flag, get_soft_modal_start, get_shell_modal_start, register_parameter_globals, \
    set_soft_modal_start, set_shell_modal_start, update_template_selection
from ..create_mould.create_mould import register_create_mould_globals
from ..create_mould.parameters_for_create_mould import register_parameter_for_create_mould_globals
from ..create_mould.hard_eardrum.hard_eardrum_cut import register_hard_eardrum_cut_globals
from ..create_mould.soft_eardrum.thickness_and_fill import register_soft_eardrum_globals, load_soft_eardrum_globals
from ..create_mould.shell_eardrum.shell_eardrum_bottom_fill import register_shell_globals, load_shell_globals
from ..create_mould.collision import register_collision_globals, load_collision_globals, initCube
from ..create_mould.shell_eardrum.shell_canal import register_shell_canal_globals
# from .fix_watertight_and_volume import fix_watertight_and_volume
from ..global_manager_for_templates import global_var_manager
from ..parameters_for_templates import register_create_mould_scene_variables
from ..back_and_forward import record_state

is_initial = False  # 防止工具类重复注册


def delete_useless_fragments(cur_obj):
    '''
    删除导入导入模型中的一些无用小碎块
    '''
    has_fragments = False
    vertex_indices = [v.index for v in cur_obj.data.vertices]
    #首先判断是否存在模型小碎片,不存在则不进行处理
    if(len(vertex_indices) != 0):
        area_begin_vert_index = vertex_indices[0]  # 处理的初始顶点
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')     # 将初始顶点选中并选中连通项
        if (cur_obj != None and cur_obj.type == 'MESH'):
            me = cur_obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            vert = bm.verts[area_begin_vert_index]
            vert.select_set(True)
            bm.to_mesh(me)
            bm.free()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_linked()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.object.mode_set(mode='OBJECT')    #反选顶点后若存在选中的顶点,则说明存在碎片
        me = cur_obj.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for vert in bm.verts:
            if(vert.select == True):
                has_fragments = True
        bm.to_mesh(me)
        bm.free()

        # 存在加厚区域的时候
        if (has_fragments):

            #将物体根据连通区域划分为多个部分
            bpy.ops.object.select_all(action='DESELECT')
            cur_obj.select_set(True)
            bpy.context.view_layer.objects.active = cur_obj
            continuous_area = []  # 存放连续区域对象信息(左右耳模型的顶点索引)
            unprocessed_vertex_index = vertex_indices  # 获取离散区域中的所有顶点作为未处理顶点
            # 处理所有选中顶点,一次循环生成一个连通区域
            while unprocessed_vertex_index:
                area_index = []  # 存放该区域内的顶点(离散区域的顶点索引)
                area_begin_vert_index = unprocessed_vertex_index[0]  # 处理的初始顶点
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')  # 将初始顶点选中并选中连通项
                if (cur_obj != None and cur_obj.type == 'MESH'):
                    me = cur_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(me)
                    bm.verts.ensure_lookup_table()
                    vert = bm.verts[area_begin_vert_index]
                    vert.select_set(True)
                    bm.to_mesh(me)
                    bm.free()
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_linked()
                bpy.ops.object.mode_set(mode='OBJECT')
                if (cur_obj != None and cur_obj.type == 'MESH'):
                    me = cur_obj.data
                    bm = bmesh.new()
                    bm.from_mesh(me)
                    bm.verts.ensure_lookup_table()
                    for vert in bm.verts:
                        if (vert.select == True):
                            area_index.append(vert.index)
                    bm.to_mesh(me)
                    bm.free()
                # 将划分过的顶点从未处理顶点数组中移除
                unprocessed_vertex_index = [x for x in unprocessed_vertex_index if x not in area_index]
                continuous_area.append(area_index)

            #只保存模型中顶点数最多的部分,将其它碎块部分删除
            largest_region = max(continuous_area, key=len)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            mesh = cur_obj.data
            bm = bmesh.from_edit_mesh(mesh)
            bm.verts.ensure_lookup_table()
            for vert_index in largest_region:
                vert = bm.verts[vert_index]
                vert.select_set(True)
            bmesh.update_edit_mesh(mesh)
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

class Huier_OT_Pymesh(bpy.types.Operator):
    bl_idname = "huier.pymesh"
    bl_label = "pymesh重网格化"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        files_dir = os.path.join(os.path.dirname(__file__))

        # 创建保存待处理stl的文件夹
        OldFolder = os.path.join(files_dir, "mesh")
        OldFolder = unixifyPath(OldFolder)
        if not os.path.exists(OldFolder):
            os.makedirs(OldFolder)

        # 创建保存减少顶点数后stl的文件夹
        # ReduceFolder = os.path.join(files_dir, "reduce_mesh")
        # ReduceFolder = unixifyPath(ReduceFolder)
        # if not os.path.exists(ReduceFolder):
        #     os.makedirs(ReduceFolder)

        # 创建保存初始化后stl的文件夹
        InitFolder = os.path.join(files_dir, "init_mesh")
        InitFolder = unixifyPath(InitFolder)
        if not os.path.exists(InitFolder):
            os.makedirs(InitFolder)

        # 创建保存均匀化后stl的文件夹
        MeanFolder = os.path.join(files_dir, "mean_mesh")
        MeanFolder = unixifyPath(MeanFolder)
        if not os.path.exists(MeanFolder):
            os.makedirs(MeanFolder)

        # 创建保存细分后stl的文件夹
        # SubFolder = os.path.join(files_dir, "subdivide_mesh")
        # SubFolder = unixifyPath(SubFolder)
        # if not os.path.exists(SubFolder):
        #     os.makedirs(SubFolder)

        # 导出摆正后的物体到待处理的文件夹
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.select_all(action='DESELECT')
            if bpy.data.objects.get('右耳'):
                bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
                bpy.data.objects['右耳'].select_set(True)
                export_path = os.path.join(OldFolder, "right.stl")
                export_path = unixifyPath(export_path)
                bpy.ops.export_mesh.stl(filepath=export_path, use_selection=True)

        override = getOverride2()
        with bpy.context.temp_override(**override):
            bpy.ops.object.select_all(action='DESELECT')
            if bpy.data.objects.get('左耳'):
                bpy.context.view_layer.objects.active = bpy.data.objects['左耳']
                bpy.data.objects['左耳'].select_set(True)
                export_path = os.path.join(OldFolder, "left.stl")
                export_path = unixifyPath(export_path)
                bpy.ops.export_mesh.stl(filepath=export_path, use_selection=True)

        # 初始化并保存到init_mesh文件夹中
        init_mesh_files = init(OldFolder, InitFolder)

        # 细分并保存到subdivide_mesh文件夹中
        # subdivide_mesh_files = subdivide(mean_mesh_files, SubFolder)

        # 减少顶点数并保存到reduce_mesh文件夹中
        # reduce_mesh_files = reduce_vertex_number(init_mesh_files, ReduceFolder)

        # 均匀化并保存到mean_mesh文件夹中
        mean(init_mesh_files, MeanFolder)

        # 导出到3DModel场景
        all_objs = bpy.data.objects
        # 删除原有物体
        for selected_obj in all_objs:
            bpy.data.objects.remove(selected_obj, do_unlink=True)

        for file in os.listdir(MeanFolder):
            stl_file_path = os.path.join(MeanFolder, file)
            bpy.ops.wm.stl_import(filepath=stl_file_path)
            active_obj = context.active_object

            bm = bmesh.new()
            bm.from_mesh(active_obj.data)
            if bm.verts.layers.float_vector.get('OriginVertex'):
                float_vector_layer = bm.verts.layers.float_vector.get('OriginVertex')
                bm.verts.layers.float_vector.remove(float_vector_layer)
            float_vector_layer = bm.verts.layers.float_vector.new('OriginVertex')
            for v in bm.verts:
                v[float_vector_layer] = Vector([v.co.x, v.co.y, v.co.z])
            if bm.verts.layers.float_vector.get('OriginNormal'):
                float_vector_layer = bm.verts.layers.float_vector.get('OriginNormal')
                bm.verts.layers.float_vector.remove(float_vector_layer)
            float_vector_layer = bm.verts.layers.float_vector.new('OriginNormal')
            for v in bm.verts:
                v[float_vector_layer] = Vector([v.normal.x, v.normal.y, v.normal.z])
            bm.to_mesh(active_obj.data)

            if active_obj.name == 'right':
                active_obj.name = '右耳'
                bpy.context.scene.transparent2R = True
                moveToRight(active_obj)
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.geometry.color_attribute_add(name="Color", color=(0, 0.25, 1, 1))
                    # todo: 更改颜色
                    # bpy.ops.geometry.color_attribute_add(name="Color", color=(0.053, 0.266, 0.436, 1))
                    active_obj.data.materials.clear()
                    active_obj.data.materials.append(bpy.data.materials['YellowR'])

                    active_obj.lock_location[0] = True
                    active_obj.lock_location[1] = True
                    active_obj.lock_location[2] = True
                    active_obj.lock_rotation[0] = True
                    active_obj.lock_rotation[1] = True
                    active_obj.lock_rotation[2] = True

                    #删除模型中的无用小碎块
                    delete_useless_fragments(active_obj)

                # 复制一份用于匹配模板位置
                duplicate_obj = active_obj.copy()
                duplicate_obj.data = active_obj.data.copy()
                duplicate_obj.animation_data_clear()
                duplicate_obj.name = active_obj.name + "OriginForFitPlace"
                bpy.context.collection.objects.link(duplicate_obj)
                duplicate_obj.hide_set(True)

                # 加到右耳集合
                collection = bpy.data.collections['Right']
                collection.objects.link(duplicate_obj)
                if duplicate_obj.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj)

                # 复制一份用于最原始物体的展示
                duplicate_obj2 = active_obj.copy()
                duplicate_obj2.data = active_obj.data.copy()
                duplicate_obj2.animation_data_clear()
                duplicate_obj2.name = active_obj.name + "OriginForShow"
                duplicate_obj2.data.materials.clear()
                duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_green_r"))
                bpy.context.collection.objects.link(duplicate_obj2)
                duplicate_obj2.hide_set(True)

                # 加到右耳集合
                collection = bpy.data.collections['Right']
                collection.objects.link(duplicate_obj2)
                if duplicate_obj2.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj2)

                # 复制一份用于打磨时的厚度计算
                # duplicate_obj3 = active_obj.copy()
                # duplicate_obj3.data = active_obj.data.copy()
                # duplicate_obj3.animation_data_clear()
                # duplicate_obj3.name = active_obj.name + "DamoCompare"
                # bpy.context.collection.objects.link(duplicate_obj3)
                # duplicate_obj3.hide_set(True)

                # 加到右耳集合
                # collection = bpy.data.collections['Right']
                # collection.objects.link(duplicate_obj3)
                # if duplicate_obj3.name in bpy.context.scene.collection.objects:
                #     bpy.context.scene.collection.objects.unlink(duplicate_obj3)

                # 复制一份用于打磨的重置
                duplicate_obj4 = active_obj.copy()
                duplicate_obj4.data = active_obj.data.copy()
                duplicate_obj4.animation_data_clear()
                duplicate_obj4.name = active_obj.name + "DamoReset"
                bpy.context.collection.objects.link(duplicate_obj4)
                duplicate_obj4.hide_set(True)

                collection = bpy.data.collections['Right']
                collection.objects.link(duplicate_obj4)
                if duplicate_obj4.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj4)

            elif active_obj.name == 'left':
                active_obj.name = '左耳'
                bpy.context.scene.transparent2L = True
                moveToLeft(active_obj)
                if os.path.isfile(context.scene.rightEar_path):   # 判断右耳是否存在，如果不存在则左耳目前在主窗口
                    override = getOverride2()
                    with bpy.context.temp_override(**override):
                        bpy.ops.geometry.color_attribute_add(name="Color", color=(0, 0.25, 1, 1))
                        # todo: 更改颜色
                        # bpy.ops.geometry.color_attribute_add(name="Color", color=(0.053, 0.266, 0.436, 1))
                        active_obj.data.materials.clear()
                        active_obj.data.materials.append(bpy.data.materials['YellowL'])

                        active_obj.lock_location[0] = True
                        active_obj.lock_location[1] = True
                        active_obj.lock_location[2] = True
                        active_obj.lock_rotation[0] = True
                        active_obj.lock_rotation[1] = True
                        active_obj.lock_rotation[2] = True

                        # 删除模型中的无用小碎块
                        delete_useless_fragments(active_obj)

                else:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.geometry.color_attribute_add(name="Color", color=(0, 0.25, 1, 1))
                        # todo: 更改颜色
                        # bpy.ops.geometry.color_attribute_add(name="Color", color=(0.053, 0.266, 0.436, 1))
                        active_obj.data.materials.clear()
                        active_obj.data.materials.append(bpy.data.materials['YellowL'])

                        active_obj.lock_location[0] = True
                        active_obj.lock_location[1] = True
                        active_obj.lock_location[2] = True
                        active_obj.lock_rotation[0] = True
                        active_obj.lock_rotation[1] = True
                        active_obj.lock_rotation[2] = True

                        # 删除模型中的无用小碎块
                        delete_useless_fragments(active_obj)

                # 复制一份用于匹配模板位置
                duplicate_obj = active_obj.copy()
                duplicate_obj.data = active_obj.data.copy()
                duplicate_obj.animation_data_clear()
                duplicate_obj.name = active_obj.name + "OriginForFitPlace"
                bpy.context.collection.objects.link(duplicate_obj)
                duplicate_obj.hide_set(True)

                # 加到左耳集合
                collection = bpy.data.collections['Left']
                collection.objects.link(duplicate_obj)
                if duplicate_obj.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj)

                # 复制一份用于展示最原始物体的展示
                duplicate_obj2 = active_obj.copy()
                duplicate_obj2.data = active_obj.data.copy()
                duplicate_obj2.animation_data_clear()
                duplicate_obj2.name = active_obj.name + "OriginForShow"
                duplicate_obj2.data.materials.clear()
                duplicate_obj2.data.materials.append(bpy.data.materials.get("tran_green_l"))
                bpy.context.collection.objects.link(duplicate_obj2)
                duplicate_obj2.hide_set(True)

                # 加到左耳集合
                collection = bpy.data.collections['Left']
                collection.objects.link(duplicate_obj2)
                if duplicate_obj2.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj2)

                # 复制一份用于打磨时的厚度计算
                # duplicate_obj3 = active_obj.copy()
                # duplicate_obj3.data = active_obj.data.copy()
                # duplicate_obj3.animation_data_clear()
                # duplicate_obj3.name = active_obj.name + "DamoCompare"
                # bpy.context.collection.objects.link(duplicate_obj3)
                # duplicate_obj3.hide_set(True)

                # 加到左耳集合
                # collection = bpy.data.collections['Left']
                # collection.objects.link(duplicate_obj3)
                # if duplicate_obj3.name in bpy.context.scene.collection.objects:
                #     bpy.context.scene.collection.objects.unlink(duplicate_obj3)

                # 复制一份用于打磨的重置
                duplicate_obj4 = active_obj.copy()
                duplicate_obj4.data = active_obj.data.copy()
                duplicate_obj4.animation_data_clear()
                duplicate_obj4.name = active_obj.name + "DamoReset"
                bpy.context.collection.objects.link(duplicate_obj4)
                duplicate_obj4.hide_set(True)

                collection = bpy.data.collections['Left']
                collection.objects.link(duplicate_obj4)
                if duplicate_obj4.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj4)

        clear_folder_list = [OldFolder, InitFolder, MeanFolder]
        clear(clear_folder_list)

        if bpy.data.objects.get('右耳'):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects['右耳']
            bpy.data.objects['右耳'].select_set(True)
        else:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = bpy.data.objects['左耳']
            bpy.data.objects['左耳'].select_set(True)

        global is_initial
        if not is_initial:
            is_initial = True
            draw_font()
            record_state()
            # 如果左右耳都存在，还需记录左耳的状态
            if bpy.data.objects.get('右耳') and bpy.data.objects.get('左耳'):
                bpy.context.scene.leftWindowObj = '左耳'
                record_state()
                bpy.context.scene.leftWindowObj = '右耳'
            # bpy.ops.object.createmouldinit('INVOKE_DEFAULT')
            # bpy.ops.object.createmouldcut('INVOKE_DEFAULT')
            # bpy.ops.object.createmouldfill('INVOKE_DEFAULT')
            bpy.ops.object.msgbuscallback('INVOKE_DEFAULT')

            register_tools()

            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        
        # 获取所有以 "use_template_" 开头的变量, 根据选择的模板加载参数
        template_props = [
            prop for prop in dir(context.scene)
            if prop.startswith("use_template_")
        ]

        for prop in template_props:
            selected_template = getattr(context.scene, prop)
            if selected_template:
                template_name = prop.replace("use_template_", "")
                if template_name == "HDU":
                    pass
                else:
                    template_enum_name = f"template_{template_name}"
                    template_enum = getattr(context.scene, template_enum_name)
                    json_file_name = str(template_enum) + ".json"
                    json_path = os.path.join(os.path.expanduser('~/Documents'), "3DModel", "Templates", template_name, json_file_name)
                    global_var_manager.load_from_json(json_path)
        return {'FINISHED'}


def import_sed_file():
    global is_initial
    if not is_initial:
        is_initial = True
        draw_font()
        bpy.ops.object.msgbuscallback('INVOKE_DEFAULT')

        register_tools()

        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    bpy.context.scene.pressfinish = False
    name = bpy.context.scene.earname
    appdata_path = Path(os.getenv('APPDATA'))
    file_path = name + ".pkl"
    pickle_path = appdata_path / "3DModel" / file_path
    global_manager.load_from_pickle(pickle_path)
    load_qiege_globals()
    load_soft_eardrum_globals()
    load_shell_globals()
    load_collision_globals()
    process = bpy.context.scene.lastprocess
    restart_modal(process)


class Close_Sed(bpy.types.Operator):
    bl_idname = "close.sed"
    bl_label = "关闭Sed文件"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        global is_initial
        return_to_default()
        is_initial = False


class Save_Template(bpy.types.Operator):
    bl_idname = "save.template"
    bl_label = "保存模板"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # 文件路径属性

    def execute(self, context):
        pass
        # register_create_mould_scene_variables()
        # global_var_manager.save_to_json(self.filepath)
        return {'FINISHED'}
    

class Fix_Mesh(bpy.types.Operator):
    bl_idname = "fix.mesh"
    bl_label = "修复mesh文件"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # 文件路径属性

    def execute(self, context):
        if os.path.exists(self.filepath):
            mesh = trimesh.load_mesh(self.filepath)
            fix_mesh = fix_watertight_and_volume(mesh)
            fix_file_path = self.filepath.replace('.stl', '_fixed.stl')
            fix_mesh.export(fix_file_path)
        return {'FINISHED'}


def return_to_default():
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    pickle_dir = os.path.join(script_dir, "io_mesh_stl\default.pkl")
    global_manager.load_from_pickle(pickle_dir)
    load_qiege_globals()
    load_soft_eardrum_globals()
    load_shell_globals()
    load_collision_globals()

    bpy.context.screen.areas[0].spaces.active.context = 'RENDER'
    bpy.context.screen.areas[0].spaces.active.context = 'RENDER'
    bpy.context.scene.frame_preview_start = 0


def register_globals():
    register_parameter_globals()
    register_public_operation_globals()
    register_damo_globals()
    register_jiahou_globals()
    register_qiege_globals()
    register_create_mould_globals()
    register_parameter_for_create_mould_globals()
    register_hard_eardrum_cut_globals()
    register_soft_eardrum_globals()
    register_shell_globals()
    register_collision_globals()
    register_shell_canal_globals()
    register_soudncanal_globals()
    register_ventcanal_globals()
    register_handle_globals()
    register_label_globals()
    register_casting_globals()
    register_support_globals()
    register_sprue_globals()
    register_cut_mould_globals()


def init_template_folder():
    user_documents = os.path.expanduser('~/Documents')
    template_dir = os.path.join(user_documents, "3DModel", "Templates")
    if not os.path.exists(template_dir):
        os.makedirs(template_dir, exist_ok=True)
    template_folders = [f for f in os.listdir(template_dir)
                        if os.path.isdir(os.path.join(template_dir, f))]
    # 默认模板路径创建
    if len(template_folders) == 0:
        default_template_dir = os.path.join(template_dir, "Huier")
        if not os.path.exists(default_template_dir):
            os.makedirs(default_template_dir, exist_ok=True)
            template_folders.append("Huier")
    for folder in template_folders:
        prop_name = f"use_template_{folder}"  # 变量名，如 "use_template_character"
        if not hasattr(bpy.types.Scene, prop_name):
            setattr(
                bpy.types.Scene,
                prop_name,
                bpy.props.BoolProperty(
                    name=f"Use {folder}",
                    description=f"Enable {folder} template",
                    default=False,
                    update=update_template_selection,
                )
            )

        templates = []
        templates_dir = os.path.join(template_dir, folder)
        for template_file in os.listdir(templates_dir):
            if template_file.endswith(".json"):
                file_name = os.path.splitext(template_file)[0]
                templates.append((file_name, file_name, f"Template: {template_file}"))
        prop_name = f"template_{folder}"
        if hasattr(bpy.types.Scene, prop_name):
            continue  # 避免重复注册

        setattr(
            bpy.types.Scene,
            prop_name,
            bpy.props.EnumProperty(
                name=f"{folder} Templates",
                description=f"Available {folder} templates",
                items=templates,
            )
        )


def init_shape_folder():
    user_documents = os.path.expanduser('~/Documents')
    shapes_dir = os.path.join(user_documents, "3DModel", "Shapes")
    if not os.path.exists(shapes_dir):
        os.makedirs(shapes_dir, exist_ok=True)
    shape_folders = [f for f in os.listdir(shapes_dir)
                     if os.path.isdir(os.path.join(shapes_dir, f))]
    # 电池形状路径创建
    if len(shape_folders) == 0:
        default_shape_dir = os.path.join(shapes_dir, "Battery")
        if not os.path.exists(default_shape_dir):
            os.makedirs(default_shape_dir, exist_ok=True)
            shape_folders.append("Battery")
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        script_dir = os.path.join(script_dir, "io_mesh_stl\\create_mould\\shell_eardrum\\shell_battery_stl")
        for battery_file in os.listdir(script_dir):
            if battery_file.endswith(".stl") and not battery_file.startswith("battery"):
                src_path = os.path.join(script_dir, battery_file)
                dst_path = os.path.join(shapes_dir, "Battery", battery_file)
                if not os.path.exists(dst_path):
                    shutil.copy(src_path, dst_path)
    for folder in shape_folders:
        shapes = []
        shape_dir = os.path.join(shapes_dir, folder)
        for shape_file in os.listdir(shape_dir):
            if shape_file.endswith(".stl"):
                file_name = os.path.splitext(shape_file)[0]
                shapes.append((file_name, file_name, f"Shape: {shape_file}"))
        prop_name = f"shape_{folder}"
        if hasattr(bpy.types.Scene, prop_name):
            continue  # 避免重复注册

        setattr(
            bpy.types.Scene,
            prop_name,
            bpy.props.EnumProperty(
                name=f"{folder} Shapes",
                description=f"Available {folder} shapes",
                items=shapes,
                # update=change_battery_selection,
            )
        )


def write_to_pickle():
    name = bpy.context.scene.earname
    file_path = name + ".pkl"
    appdata_path = Path(os.getenv('APPDATA'))
    app_dir = appdata_path / "3DModel"
    app_dir.mkdir(parents=True, exist_ok=True)
    pickle_path = app_dir / file_path
    global_manager.save_to_pickle(pickle_path)


def restart_modal(process):
    var = bpy.context.scene.var
    if (process == '打磨'):
        if var == 1:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.thickening('INVOKE_DEFAULT')
        elif var == 2:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.thinning('INVOKE_DEFAULT')
        elif var == 3:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.smooth('INVOKE_DEFAULT')
    elif (process == '局部加厚'):
        if var == 5:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.obj.localthickeningaddarea('INVOKE_DEFAULT')
        elif var == 6:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.obj.localthickeningreducearea('INVOKE_DEFAULT')
        elif var == 7:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.obj.localthickeningthick('INVOKE_DEFAULT')
    elif (process == '切割'):
        if var == 55:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.circlecut('INVOKE_DEFAULT')
        elif var == 56:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.stepcut('INVOKE_DEFAULT')
    elif (process == '创建模具'):
        if get_soft_modal_start():
            set_soft_modal_start(False)
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.softeardrumcirclecut('INVOKE_DEFAULT')
        elif get_shell_modal_start():
            set_shell_modal_start(False)
            override = getOverride()
            with bpy.context.temp_override(**override):
                initCube()
                bpy.ops.object.shell_switch('INVOKE_DEFAULT')
        if var == 19:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.pointqiehuan('INVOKE_DEFAULT')
        elif var == 20:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.dragcurve('INVOKE_DEFAULT')
        elif var == 21:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.smoothcurve('INVOKE_DEFAULT')
    elif (process == '传声孔'):
        if var == 23:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')
    elif (process == '通气孔'):
        if var == 26:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
    elif (process == '耳膜附件'):
        if var != 16:
            if var == 14:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.object.handleswitch('INVOKE_DEFAULT')
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")
    elif (process == '编号'):
        if var != 43:
            if var == 41:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.object.labelswitch('INVOKE_DEFAULT')
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
    elif (process == '铸造法软耳模'):
        pass
    elif (process == '支撑'):
        if var != 78:
            if var == 77:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.object.supportswitch('INVOKE_DEFAULT')
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="my_tool.support_initial")
    elif (process == '排气孔'):
        if var != 89:
            if var == 87:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.object.sprueswitch('INVOKE_DEFAULT')
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
    elif (process == '后期打磨'):
        if var == 111:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.last_thickening('INVOKE_DEFAULT')
        elif var == 112:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.last_thinning('INVOKE_DEFAULT')
        elif var == 113:
            override = getOverride()
            with bpy.context.temp_override(**override):
                bpy.ops.object.last_smooth('INVOKE_DEFAULT')
    elif (process == '切割模具'):
        if var != 91:
            if var == 90:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")
            else:
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch2")


def unixifyPath(path):
    path = path.replace('\\', '/')
    return path


def init(Folder_pathin, Folder_pathout):  # 初始化
    init_mesh_files = []
    for temp_file in os.listdir(Folder_pathin):
        ms = ml.MeshSet()  # 创建一个新的MeshSet对象
        ms.load_new_mesh(os.path.join(Folder_pathin, temp_file))  # 加载临时文件

        # # 选择非流形边
        # ms.apply_filter('compute_selection_by_non_manifold_edges_per_face')
        # # 删除选中的顶点
        # ms.apply_filter('meshing_remove_selected_vertices')
        # 选择非流形顶点
        ms.apply_filter('compute_selection_by_non_manifold_per_vertex')
        # 删除选中的顶点
        ms.apply_filter('meshing_remove_selected_vertices')

        temp_file_path = os.path.join(Folder_pathout, temp_file)  # 临时文件的完整路径
        ms.save_current_mesh(temp_file_path)  # 保存初始化后的网格
        init_mesh_files.append(temp_file_path)  # 将路径添加到列表中

    return init_mesh_files


def mean(init_mesh_files, Folder_pathout):  # 均匀化
    for temp_file in init_mesh_files:
        ms = ml.MeshSet()  # 创建一个新的MeshSet对象
        ms.load_new_mesh(temp_file)  # 加载初始化处理后的临时文件
        filename = os.path.basename(temp_file)  # 获取临时文件名

        files_dir = os.path.join(os.path.dirname(__file__))
        filter_dir = os.path.join(files_dir, 'Isotropic_Explicit_Remeshing.mlx')
        filter_dir = unixifyPath(filter_dir)
        ms.load_filter_script(filter_dir)
        ms.apply_filter_script()

        temp_file_path = os.path.join(Folder_pathout, filename)  # 临时文件的完整路径
        ms.save_current_mesh(temp_file_path)  # 保存均匀化处理后的网格


# def subdivide(mean_mesh_files, Folder_pathout):
#     subdivided_mesh_files = []
#     for temp_file in mean_mesh_files:
#         ms = ml.MeshSet()  # 创建一个新的MeshSet对象
#         ms.load_new_mesh(temp_file)  # 加载均匀化处理后的临时文件
#         filename = os.path.basename(temp_file)  # 获取临时文件名

#         files_dir = os.path.join(os.path.dirname(__file__))
#         filter_dir = os.path.join(files_dir, 'subdivide_midpoint.mlx')
#         filter_dir = unixifyPath(filter_dir)
#         ms.load_filter_script(filter_dir)
#         while True:
#             ms.apply_filter_script()
#             m = ms.current_mesh()
#             if m.vertex_number() >= 15000:
#                 break

#         temp_file_path = os.path.join(Folder_pathout, filename)  # 临时文件的完整路径
#         ms.save_current_mesh(temp_file_path)  # 保存细分处理后的网格
#         subdivided_mesh_files.append(temp_file_path)  # 将路径添加到列表中

#     return subdivided_mesh_files

# def reduce_vertex_number(init_mesh_files, Folder_pathout):
#     reduce_mesh_files = []
#     for temp_file in init_mesh_files:
#         ms = ml.MeshSet()  # 创建一个新的MeshSet对象
#         ms.load_new_mesh(temp_file)  # 加载细分处理后的临时文件
#         filename = os.path.basename(temp_file)  # 获取临时文件名

#         m = ms.current_mesh()  # 获取当前网格
#         print(f'Input mesh {filename} has', m.vertex_number(), 'vertex and', m.face_number(), 'faces')

#         # 目标顶点数
#         TARGET = 15000

#         # 估计面数以达到100 + 2 * TARGET的顶点数，使用欧拉公式
#         numFaces = 100 + 2 * TARGET

#         # 简化网格。只有第一次简化会比较激进
#         while ms.current_mesh().vertex_number() > TARGET:
#             ms.apply_filter('meshing_decimation_quadric_edge_collapse', targetfacenum=numFaces, preservenormal=True)
#             print(f"Decimated to {numFaces} faces; mesh {filename} has", ms.current_mesh().vertex_number(), "vertices")
#             # 细化估计以逐渐接近目标顶点数
#             numFaces -= (ms.current_mesh().vertex_number() - TARGET)

#         m = ms.current_mesh()  # 获取简化后的网格
#         print(f'Output mesh {filename} has', m.vertex_number(), 'vertex and', m.face_number(), 'faces')
#         temp_file_path = os.path.join(Folder_pathout, filename)  # 临时文件的完整路径
#         ms.save_current_mesh(temp_file_path)  # 保存简化后的网格到输出目录
#         reduce_mesh_files.append(temp_file_path)  # 将路径添加到列表中

#     return reduce_mesh_files


def clear(clear_folder_list):
    for folder in clear_folder_list:
        shutil.rmtree(folder)  # 删除文件夹(包括文件夹中的内容)


def register():
    # init_template_folder()
    # init_shape_folder()
    bpy.utils.register_class(Huier_OT_Pymesh)
    bpy.utils.register_class(Close_Sed)
    bpy.utils.register_class(Save_Template)
    bpy.utils.register_class(Fix_Mesh)


def unregister():
    bpy.utils.unregister_class(Huier_OT_Pymesh)
    bpy.utils.unregister_class(Close_Sed)
    bpy.utils.unregister_class(Save_Template)
    bpy.utils.unregister_class(Fix_Mesh)
