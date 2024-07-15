import pymeshlab as ml
import os
import shutil
import bpy
from ..tool import moveToRight, moveToLeft, getOverride, getOverride2


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
            if active_obj.name == 'right':
                active_obj.name = '右耳'
                moveToRight(active_obj)
                override = getOverride()
                with bpy.context.temp_override(**override):
                    bpy.ops.geometry.color_attribute_add(name="Color", color=(0, 0.25, 1, 1))
                    active_obj.data.materials.clear()
                    active_obj.data.materials.append(bpy.data.materials['YellowR'])

                    active_obj.lock_location[0] = True
                    active_obj.lock_location[1] = True
                    active_obj.lock_location[2] = True

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
                bpy.context.scene.transparent2R = True
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
                duplicate_obj3 = active_obj.copy()
                duplicate_obj3.data = active_obj.data.copy()
                duplicate_obj3.animation_data_clear()
                duplicate_obj3.name = active_obj.name + "DamoCompare"
                bpy.context.collection.objects.link(duplicate_obj3)
                duplicate_obj3.hide_set(True)

                # 加到右耳集合
                collection = bpy.data.collections['Right']
                collection.objects.link(duplicate_obj3)
                if duplicate_obj3.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj3)

            elif active_obj.name == 'left':
                active_obj.name = '左耳'
                moveToLeft(active_obj)
                override = getOverride2()
                with bpy.context.temp_override(**override):
                    bpy.ops.geometry.color_attribute_add(name="Color", color=(0, 0.25, 1, 1))
                    active_obj.data.materials.clear()
                    active_obj.data.materials.append(bpy.data.materials['YellowL'])

                    active_obj.lock_location[0] = True
                    active_obj.lock_location[1] = True
                    active_obj.lock_location[2] = True

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
                bpy.context.scene.transparent2L = True
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
                duplicate_obj3 = active_obj.copy()
                duplicate_obj3.data = active_obj.data.copy()
                duplicate_obj3.animation_data_clear()
                duplicate_obj3.name = active_obj.name + "DamoCompare"
                bpy.context.collection.objects.link(duplicate_obj3)
                duplicate_obj3.hide_set(True)

                # 加到左耳集合
                collection = bpy.data.collections['Left']
                collection.objects.link(duplicate_obj3)
                if duplicate_obj3.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(duplicate_obj3)

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

        return {'FINISHED'}


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
    bpy.utils.register_class(Huier_OT_Pymesh)


def unregister():
    bpy.utils.unregister_class(Huier_OT_Pymesh)