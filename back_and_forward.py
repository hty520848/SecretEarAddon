import bpy
import bmesh
import datetime
import json
import importlib
import sys
import traceback
from .parameter import set_switch_flag, get_soft_modal_start, get_shell_modal_start, get_soft_modal_start, \
    set_soft_modal_start, set_shell_modal_start, get_process_var_list
from .tool import change_mat_mould, getOverride, track_time, reset_time_tracker
from .create_mould.collision import initCube
from .register_tool import register_tools, unregister_tools

# ---------撤回前进相关逻辑-------------
MAX_HISTORY_SIZE = 6  # 最大撤回/前进步数
_undo_current_state_idx = 0  # 指向当前场景的活跃状态所对应的历史状态索引 (0表示初始状态，无历史)
_undo_max_saved_idx = 0  # 指向当前已保存的历史状态中最大的索引，用来处理撤回后再操作的情况
HISTORY_PREFIX_FORMAT = "_backup_"  # 历史模型的前缀格式，例如: 1_backup_Cube, 2_backup_Sphere
_history_globals = {}  # 兼容旧变量（已迁移到 _undo_state）
is_processing_undo_redo = False  # 标记当前是否正在处理撤回/前进操作

# per-side undo state: 用于分别管理 Left/Right 的索引和历史全局变量
# 结构: { 'Left': {'current': int, 'max': int, 'history_globals': {idx: {...}}}, 'Right': {...} }
_undo_state = {
    'Left': {'current': 0, 'max': 0, 'history_globals': {}},
    'Right': {'current': 0, 'max': 0, 'history_globals': {}},
}


def _get_side():
    """根据场景的 leftWindowObj 推断当前侧。返回 'Left' 或 'Right'。"""
    try:
        name = bpy.context.scene.leftWindowObj
        # 代码历史：当 leftWindowObj == '右耳' 时表示当前为右耳视图
        return 'Right' if name == '右耳' else 'Left'
    except Exception:
        return 'Left'


def _ensure_side_state(side: str):
    if side not in _undo_state:
        _undo_state[side] = {'current': 0, 'max': 0, 'history_globals': {}}
    return _undo_state[side]


def _get_current_idx_for_side(side: str):
    return _ensure_side_state(side)['current']


def _set_current_idx_for_side(side: str, val: int):
    _ensure_side_state(side)['current'] = val


def _get_max_idx_for_side(side: str):
    return _ensure_side_state(side)['max']


def _set_max_idx_for_side(side: str, val: int):
    _ensure_side_state(side)['max'] = val


def _get_history_globals_for_side(side: str):
    return _ensure_side_state(side)['history_globals']

# 需要保存和恢复的全局变量字典（按侧划分）
# 结构建议：{ 'Left': { module_name: [vars...] }, 'Right': { ... }, 'Shared': { ... } }
# 这样可以为左右耳分别指定要记录的模块变量，同时保留 Shared 部分用于通用变量。
# 为了向后兼容，辅助函数会检查是否为旧的平面结构（module -> [vars]）并回退支持。
GLOBAL_VARS_TO_SAVE = {
    'Right': {
        'io_mesh_stl.damo': ['previous_thicknessR'],
        'io_mesh_stl.jiahou': ['is_copy_local_thickening', 'local_thickening_objects_array', 'objects_array_index',
                                'prev_localthick_area_index', 'switch_selected_vertex_index', 'right_is_submit'],
        'io_mesh_stl.create_tip.qiege': ['right_last_radius', 'right_last_loc', 'right_last_ratation','finish'],
        'io_mesh_stl.create_mould.shell_eardrum.shell_eardrum_bottom_fill': ['bottom_right_last_loc', 'bottom_right_last_ratation', 'middle_right_last_loc',
                                                                             'middle_right_last_ratation', 'top_right_last_loc', 'top_right_last_ratation',
                                                                             'battery_right_location', 'battery_right_rotation'],
        'io_mesh_stl.create_mould.shell_eardrum.shell_canal': ['number', 'object_dic', 'shellcanal_data'],
        'io_mesh_stl.create_mould.collision': ['cube1_location', 'cube2_location', 'cube3_location', 'receiver_location',
                                               'cube1_rotation', 'cube2_rotation', 'cube3_rotation', 'receiver_rotation'],
        'io_mesh_stl.create_mould.parameters_for_create_mould': ['right_hard_eardrum_adjust_border', 'right_soft_eardrum_adjust_border',
                                                                 'right_frame_style_eardrum_adjust_border', 'right_frame_style_hole_border',
                                                                 'right_shell_border', 'right_shell_plane_border'],
        'io_mesh_stl.create_mould.soft_eardrum.thickness_and_fill': ['right_last_loc', 'right_last_radius', 'right_last_ratation',
                                                                     'right_last_loc_upper', 'right_last_radius_upper', 'right_last_ratation_upper'],
        'io_mesh_stl.sound_canal': ['number', 'object_dic', 'soundcanal_data', 'soundcanal_finish', 'soundcanal_shape', 'soundcanal_hornpipe_offset',
                                    'is_on_rotate', 'rotete_middle_dis', 'rotate_last_dis', 'rotate_offset'],
        'io_mesh_stl.vent_canal': ['number', 'object_dic', 'ventcanal_data', 'ventcanal_finish'],
        'io_mesh_stl.handle': ['is_on_rotate', 'handle_info_save', 'handle_index'],
        'io_mesh_stl.label': ['default_plane_size_x', 'default_plane_size_y', 'label_info_save', 'label_index'],
        'io_mesh_stl.casting': ['prev_casting_thickness', 'is_casting_submit'],
        'io_mesh_stl.support': ['is_add_support', 'is_on_rotate', 'prev_location_x', 'prev_location_y', 'prev_location_z',
                                'prev_rotation_x', 'prev_rotation_y', 'prev_rotation_z', 'support_enum', 'support_offset'],
        'io_mesh_stl.sprue': ['sprue_info_save', 'sprue_index', 'is_on_rotate'],
    },
    'Left': {
        'io_mesh_stl.damo': ['previous_thicknessL'],
        'io_mesh_stl.jiahou': ['is_copy_local_thickeningL', 'local_thickening_objects_arrayL', 'objects_array_indexL',
                                'prev_localthick_area_indexL', 'switch_selected_vertex_indexL', 'left_is_submit'],
        'io_mesh_stl.create_tip.qiege': ['left_last_radius', 'left_last_loc', 'left_last_ratation','finishL'],
        'io_mesh_stl.create_mould.shell_eardrum.shell_eardrum_bottom_fill': ['bottom_left_last_loc', 'bottom_left_last_ratation', 'middle_left_last_loc',
                                                                             'middle_left_last_ratation', 'top_left_last_loc', 'top_left_last_ratation',
                                                                             'battery_left_location', 'battery_left_rotation'],
        'io_mesh_stl.create_mould.shell_eardrum.shell_canal': ['numberL', 'object_dicL', 'shellcanal_dataL'],
        'io_mesh_stl.create_mould.collision': ['cube1_locationL', 'cube2_locationL', 'cube3_locationL', 'receiver_locationL',
                                               'cube1_rotationL', 'cube2_rotationL', 'cube3_rotationL', 'receiver_rotationL'],
        'io_mesh_stl.create_mould.parameters_for_create_mould': ['left_hard_eardrum_adjust_border', 'left_soft_eardrum_adjust_border',
                                                                 'left_frame_style_eardrum_adjust_border', 'left_frame_style_hole_border',
                                                                 'left_shell_border', 'left_shell_plane_border'],
        'io_mesh_stl.create_mould.soft_eardrum.thickness_and_fill': ['left_last_loc', 'left_last_radius', 'left_last_ratation',
                                                                     'left_last_loc_upper', 'left_last_radius_upper', 'left_last_ratation_upper'],
        'io_mesh_stl.sound_canal': ['numberL', 'object_dicL', 'soundcanal_dataL', 'soundcanal_finishL', 'soundcanal_shapeL', 'soundcanal_hornpipe_offsetL',
                                    'is_on_rotateL', 'rotete_middle_disL', 'rotate_last_disL', 'rotate_offsetL'],
        'io_mesh_stl.vent_canal': ['numberL', 'object_dicL', 'ventcanal_dataL', 'ventcanal_finishL'],
        'io_mesh_stl.handle': ['is_on_rotateL', 'handle_info_saveL', 'handle_indexL'],
        'io_mesh_stl.label': ['default_plane_size_xL', 'default_plane_size_yL', 'label_info_saveL', 'label_indexL'],
        'io_mesh_stl.casting': ['prev_casting_thicknessL', 'is_casting_submitL'],
        'io_mesh_stl.support': ['is_add_supportL', 'is_on_rotateL', 'prev_location_xL', 'prev_location_yL', 'prev_location_zL',
                                'prev_rotation_xL', 'prev_rotation_yL', 'prev_rotation_zL', 'support_enumL', 'support_offsetL'],
        'io_mesh_stl.sprue': ['sprue_info_saveL', 'sprue_indexL', 'is_on_rotateL'],
    },
    'Shared': {
        'io_mesh_stl.public_operation': ['prev_properties_context', 'before_cut_mould',
                                         'left_context', 'left_var', 'right_context', 'right_var'],
        'io_mesh_stl.parameter': ['soft_modal_start', 'shell_modal_start'],
        'io_mesh_stl.ui': ['prev_context', 'show_prop'],
        'io_mesh_stl.create_tip.qiege': ['old_radius'],
        'io_mesh_stl.create_mould.shell_eardrum.shell_eardrum_bottom_fill': ['bottom_prev_radius', 'middle_prev_radius', 'top_prev_radius'],
        'io_mesh_stl.create_mould.soft_eardrum.thickness_and_fill': ['old_radius', 'old_radius_upper'],
        'io_mesh_stl.create_mould.create_mould': ['last_operate_type'],
        'io_mesh_stl.create_mould.hard_eardrum.hard_eardrum_cut': ['min_z_before_cut', 'max_z_before_cut'],
        'io_mesh_stl.create_tip.cut_mould': ['color_mode'],
    }
}


def _get_var_sources_for_side(side: str):
    """
    根据 side 返回一个迭代器，按优先级产生 (module_name, var_list) 对：
      1. side 特定的模块->列表
      2. Shared 模块->列表（合并已存在的模块名）
      3. 兼容旧的平面 GLOBAL_VARS_TO_SAVE（如果文件中仍然为旧格式）
    """
    # Detect legacy flat structure: values are lists (module->list)
    try:
        # If any value is a dict, treat as the new per-side structure
        is_per_side = any(isinstance(v, dict) for v in GLOBAL_VARS_TO_SAVE.values())
    except Exception:
        is_per_side = False

    if is_per_side:
        seen = set()
        # yield side-specific first
        for module_name, var_list in GLOBAL_VARS_TO_SAVE.get(side, {}).items():
            seen.add(module_name)
            yield module_name, var_list
        # then yield Shared, merging lists when module already seen
        for module_name, var_list in GLOBAL_VARS_TO_SAVE.get('Shared', {}).items():
            if module_name in seen:
                # merge deduplicated
                existing = GLOBAL_VARS_TO_SAVE.get(side, {}).get(module_name, [])
                merged = list(dict.fromkeys(list(existing) + list(var_list)))
                yield module_name, merged
            else:
                yield module_name, var_list
    else:
        # legacy flat dict
        for module_name, var_list in GLOBAL_VARS_TO_SAVE.items():
            yield module_name, var_list

# 需要保存的 Scene 属性集合（按侧划分）
# 结构建议：{ 'Left': set(...), 'Right': set(...), 'Shared': set(...) }
SCENE_PROPS_TO_SAVE = {
    'Right': {"laHouDUR","localLaHouDuR","maxLaHouDuR","minLaHouDuR","localThicking_offset","localThicking_borderWidth",
              "qiegesheRuPianYiR","neiBianJiXianR","waiBianYuanSheRuPianYiR","neiBianYuanSheRuPianYiR","zongHouDuR",
              "jiHuoBianYuanHouDuR","waiBuHouDuR","waiBuQuYuKuanDuR","zhongJianHouDuR","shiFouShiYongNeiBuR",
              "zhongJianQuYuKuanDuR","neiBuHouDuR","yingErMoSheRuPianYiR","mianBanPianYiR","xiaFangYangXianPianYiR",
              "shangSheRuYinZiR","xiaSheRuYinZiR","shiFouShangBuQieGeMianBanR","shangBuQieGeMianBanPianYiR",
              "useShellCanalR","shellCanalDiameterR","shellCanalThicknessR","shellCanalOffsetR","chuanShenGuanDaoZhiJing",
              "chuanShenKongOffset","soundcancalShapeEnum","tongQiGuanDaoZhiJing","erMoFuJianOffset","labelText","fontSize",
              "deep","styleEnum","ruanErMoHouDu","zhiChengOffset","zhiChengTypeEnum","paiQiKongOffset"},
    'Left': {"laHouDUL","localLaHouDuL","maxLaHouDuL","minLaHouDuL","localThicking_offset_L","localThicking_borderWidth_L",
             "qiegesheRuPianYiL","neiBianJiXianL","waiBianYuanSheRuPianYiL","neiBianYuanSheRuPianYiL","zongHouDuL",
             "jiHuoBianYuanHouDuL","waiBuHouDuL","waiBuQuYuKuanDuL","zhongJianHouDuL","shiFouShiYongNeiBuL",
             "zhongJianQuYuKuanDuL","neiBuHouDuL","yingErMoSheRuPianYiL","mianBanPianYiL","xiaFangYangXianPianYiL",
             "shangSheRuYinZiL","xiaSheRuYinZiL","shiFouShangBuQieGeMianBanL","shangBuQieGeMianBanPianYiL",
             "useShellCanalL","shellCanalDiameterL","shellCanalThicknessL","shellCanalOffsetL","chuanShenGuanDaoZhiJing_L",
             "chuanShenKongOffset_L","soundcancalShapeEnum_L","tongQiGuanDaoZhiJing_L","erMoFuJianOffsetL","labelTextL","fontSizeL",
             "deepL","styleEnumL","ruanErMoHouDuL","zhiChengOffsetL","zhiChengTypeEnumL","paiQiKongOffsetL"},
    'Shared': {"frame_preview_start","muJuTypeEnum","muJuNameEnum","mianBanTypeEnum"},
}


def add_scene_prop_to_watch(prop_name: str, side: str = 'Shared'):
    """将 scene 的属性名加入监视列表（保存时会记录）。

    side 可选 'Left'/'Right'/'Shared'。默认 Shared 以兼容之前行为。
    """
    if not isinstance(prop_name, str):
        raise TypeError("prop_name 必须是字符串")
    if isinstance(SCENE_PROPS_TO_SAVE, dict):
        if side not in SCENE_PROPS_TO_SAVE:
            SCENE_PROPS_TO_SAVE[side] = set()
        SCENE_PROPS_TO_SAVE[side].add(prop_name)
    else:
        # legacy fallback (if file still had flat set)
        SCENE_PROPS_TO_SAVE.add(prop_name)


def remove_scene_prop_from_watch(prop_name: str, side: str = 'Shared'):
    """从监视列表中移除属性名。"""
    if isinstance(SCENE_PROPS_TO_SAVE, dict):
        if side in SCENE_PROPS_TO_SAVE:
            SCENE_PROPS_TO_SAVE[side].discard(prop_name)
    else:
        SCENE_PROPS_TO_SAVE.discard(prop_name)


def get_scene_props_to_save(side: str = None):
    """返回监视的 scene 属性名的集合。

    如果提供 side（'Left' 或 'Right'），返回该侧与 Shared 的合并集合。
    如果不提供 side，返回所有侧的并集（用于全局检查）。
    """
    if isinstance(SCENE_PROPS_TO_SAVE, dict):
        if side in ('Left', 'Right'):
            res = set()
            res.update(SCENE_PROPS_TO_SAVE.get('Shared', set()))
            res.update(SCENE_PROPS_TO_SAVE.get(side, set()))
            return res
        else:
            # 返回所有侧的并集
            res = set()
            for s in SCENE_PROPS_TO_SAVE.values():
                res.update(s)
            return res
    else:
        # legacy flat set
        return set(SCENE_PROPS_TO_SAVE)

def get_is_processing_undo_redo():
    """返回当前是否正在处理撤回/前进操作的标志。"""
    return is_processing_undo_redo

def set_is_processing_undo_redo(val: bool):
    """设置当前是否正在处理撤回/前进操作的标志。"""
    global is_processing_undo_redo
    is_processing_undo_redo = val

# --- 辅助函数 ---
def _log_scene_objects(step_name="Current Scene State"):
    """打印当前场景中所有活跃对象和历史对象的列表，用于调试"""
    print(f"\n--- DEBUG: {step_name} ---")
    active_objects = []
    history_objects_map = {i: [] for i in range(1, MAX_HISTORY_SIZE + 1)}

    for obj in bpy.context.scene.objects:
        is_history = False
        for i in range(1, MAX_HISTORY_SIZE + 1):
            if obj.name.startswith(f"{i}{HISTORY_PREFIX_FORMAT}"):
                history_objects_map[i].append(obj.name)
                is_history = True
                break
        if not is_history:
            active_objects.append(obj.name)

    print(f"  活跃对象 ({len(active_objects)}): {active_objects if active_objects else '无'}")
    for i in range(1, MAX_HISTORY_SIZE + 1):
        if history_objects_map[i]:
            print(f"  历史状态 {i} 对象 ({len(history_objects_map[i])}): {history_objects_map[i]}")
    print(f"  全局变量历史: {_history_globals}")
    print(f"  全局状态: current_idx={_undo_current_state_idx}, max_idx={_undo_max_saved_idx}")
    print("----------------------------")


def _get_active_objects():
    """
    获取当前场景中所有“活跃”的对象（即名称没有历史前缀的对象）
    这些对象是用户当前正在操作的对象
    """
    # 保持原有逻辑以确定要排除的集合（另侧集合始终不应被删除）
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        need_not_delete_objects = bpy.data.collections["Left"].objects
    else:
        need_not_delete_objects = bpy.data.collections["Right"].objects
    active_objects = []
    for obj in bpy.context.scene.objects:
        if obj.name in need_not_delete_objects:
            continue
        # 判断是否为历史对象（任一侧的历史都算历史对象）
        is_history_object = False
        for side in ('Left', 'Right'):
            for i in range(1, MAX_HISTORY_SIZE + 1):
                if obj.name.startswith(f"{side}_{i}{HISTORY_PREFIX_FORMAT}"):
                    is_history_object = True
                    break
            if is_history_object:
                break
        if not is_history_object:
            active_objects.append(obj)
    # print(f"DEBUG: _get_active_objects 找到 {len(active_objects)} 个活跃对象: {[o.name for o in active_objects]}")
    return active_objects


def _get_history_objects(prefix_idx=None, side=None):
    """
    获取指定前缀的历史对象
    如果 prefix_idx 为 None，则返回所有历史对象
    """
    history_objects = []
    for obj in bpy.context.scene.objects:
        if prefix_idx is not None:
            # 查找指定侧的索引历史对象（若未指定 side，则查找任一侧）
            sides_to_check = (side,) if side else ('Left', 'Right')
            for s in sides_to_check:
                if obj.name.startswith(f"{s}_{prefix_idx}{HISTORY_PREFIX_FORMAT}"):
                    history_objects.append(obj)
                    break
        else:
            # 返回所有历史对象（包含左右）或若指定 side 则仅返回该侧
            sides_to_check = (side,) if side else ('Left', 'Right')
            for s in sides_to_check:
                for i in range(1, MAX_HISTORY_SIZE + 1):
                    if obj.name.startswith(f"{s}_{i}{HISTORY_PREFIX_FORMAT}"):
                        history_objects.append(obj)
                        break
                if obj in history_objects:
                    break
    # print(
    #     f"DEBUG: _get_history_objects(prefix_idx={prefix_idx}) 找到 {len(history_objects)} 个历史对象: {[o.name for o in history_objects]}")
    return history_objects


def _delete_objects(objects_to_delete, debug_msg=""):
    """
    删除 Blender 场景中的一组对象
    """
    if not objects_to_delete:
        # print(f"DEBUG: _delete_objects: 没有对象需要删除 {debug_msg}")
        return

    # print(
    #     f"DEBUG: _delete_objects: 准备删除 {len(objects_to_delete)} 个对象 {debug_msg}: {[o.name for o in objects_to_delete]}")

    # if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    #     bpy.ops.object.mode_set(mode='OBJECT')

    # bpy.ops.object.select_all(action='DESELECT')

    for obj in list(objects_to_delete):  # 迭代列表的副本，因为原列表会在循环中被修改
        if obj.name in bpy.data.objects:
            obj_name_to_print = obj.name  # 在删除前获取名称
            # 在删除对象之前，先将其从所有集合中取消链接，以避免潜在的引用问题
            for col in list(obj.users_collection):
                if obj.name in col.objects:
                    col.objects.unlink(obj)
                    # print(f"DEBUG:     从集合 {col.name} 取消链接 {obj_name_to_print} (删除前)")
            bpy.data.objects.remove(obj, do_unlink=True)
            # print(f"DEBUG:   已删除对象: {obj_name_to_print}")  # 使用保存的名称
        else:
            pass
            # print(f"DEBUG:   对象 {obj.name} 已不存在，跳过删除。")
    # print(f"DEBUG: _delete_objects: 完成删除 {debug_msg}")


def _rename_history_objects(old_prefix, new_prefix, side=None):
    """
    将场景中所有以 old_prefix_backup_ 开头的历史对象重命名为 new_prefix_backup_
    """
    # 旧逻辑为不带侧别的索引重命名。新逻辑按侧进行重命名。
    renamed_count = 0
    # 若 old_prefix/new_prefix 为数字索引（int或可转为str），按当前侧进行替换
    # 这里假定调用者会传入数字索引并在外部指定 side；为了兼容性，解析参数
    sides_to_process = (side,) if side else ('Left', 'Right')
    for s in sides_to_process:
        for obj in list(bpy.context.scene.objects):  # 迭代列表的副本，因为原列表会在循环中被修改
            if obj.name.startswith(f"{s}_{old_prefix}{HISTORY_PREFIX_FORMAT}"):
                old_prefix_len = len(s) + 1 + len(str(old_prefix)) + len(HISTORY_PREFIX_FORMAT)
                base_name = obj.name[old_prefix_len:]
                new_name = f"{s}_{new_prefix}{HISTORY_PREFIX_FORMAT}{base_name}"
                obj.name = new_name
                renamed_count += 1
    # print(f"DEBUG: _rename_history_objects: 完成重命名 {renamed_count} 个对象。")


def _restore_globals_from_saved(saved_globals):
    """
    从 saved_globals（由 record_state 存储的字典）恢复全局变量。
    支持两种键格式：
      - "module.name.var"：尝试将值写入模块属性（通过 importlib 导入或从 sys.modules 获取）
      - "var"：写回到当前模块的 globals()
    如果写入模块属性失败，会作为回退写入 globals()。
    """
    for key, value in saved_globals.items():
        try:
            if isinstance(key, str) and '.' in key:
                module_name, var_name = key.rsplit('.', 1)
                # 特殊处理 scene.<prop>
                if module_name == 'scene':
                    try:
                        scene = bpy.context.scene
                        # 优先尝试 setattr（用于 RNA 属性），否则回退为自定义属性赋值
                        try:
                            setattr(scene, var_name, value)
                        except Exception:
                            try:
                                scene[var_name] = value
                            except Exception as e:
                                print(f"WARNING: 无法将值写入 scene 属性 {var_name}: {e}")
                                traceback.print_exc()
                        continue
                    except Exception:
                        print(f"WARNING: 恢复 scene 属性 {var_name} 时无法获取 scene 对象")
                        traceback.print_exc()

                mod = sys.modules.get(module_name)
                if mod is None:
                    try:
                        mod = importlib.import_module(module_name)
                    except Exception as e:
                        mod = None
                if mod is not None:
                    try:
                        setattr(mod, var_name, value)
                        # print(f"DEBUG: 恢复 {module_name}.{var_name}")
                        continue
                    except Exception as e:
                        print(f"WARNING: 无法将值写入模块属性 {module_name}.{var_name}: {e}")
                        traceback.print_exc()
                        # 回退到 globals
                        globals()[var_name] = value
                else:
                    # 模块无法导入，回退到 globals
                    globals()[var_name] = value
            else:
                # 直接写入当前模块的全局命名空间
                globals()[key] = value
        except Exception as e:
            print(f"ERROR: 恢复全局变量 {key} 时发生异常: {e}")
            traceback.print_exc()


def restart_modal(module, var):
    processing_stage_dict = {
        "RENDER": "打磨",
        "OUTPUT": "局部加厚",
        "VIEW_LAYER": "切割",
        "SCENE": "创建模具",
        "WORLD": "传声孔",
        "COLLECTION": "通气孔",
        "OBJECT": "耳膜附件",
        "MODIFIER": "编号",
        "PARTICLES": "铸造法软耳模",
        "PHYSICS": "支撑",
        "CONSTRAINT": "排气孔",
        "DATA": "布局切换",
        "MATERIAL": "切割模具",
        "TEXTURE": "后期打磨"
    }
    process = processing_stage_dict[module]
    if not get_process_var_list[process]:
        bpy.context.scene.var = 0
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


def change_moudle(prev_moudle, prev_var):
    set_switch_flag(False)
    bpy.context.screen.areas[0].spaces.active.context = prev_moudle
    bpy.context.screen.areas[0].spaces.active.context = prev_moudle
    # 切换材质
    if (prev_moudle == 'RENDER' or prev_moudle == 'OUTPUT' or prev_moudle == 'TEXTURE'):
        change_mat_mould(1)
        name = bpy.context.scene.leftWindowObj
        if name == "右耳":
            collections = bpy.data.collections["Right"]
        else:
            collections = bpy.data.collections["Left"]
        for obj in collections.objects:
            if obj.type == 'MESH':
                me = obj.data
                bm = bmesh.new()
                bm.from_mesh(me)
                if len(bm.verts.layers.float_color) > 0:
                    color_lay = bm.verts.layers.float_color["Color"]
                    if prev_moudle == 'RENDER':
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 0
                            colvert.y = 0.25
                            colvert.z = 1
                    else:
                        for vert in bm.verts:
                            colvert = vert[color_lay]
                            colvert.x = 1
                            colvert.y = 0.319
                            colvert.z = 0.133

                bm.to_mesh(me)
                bm.free()
    else:
        change_mat_mould(0)
    
    if bpy.context.scene.leftWindowObj == '右耳':
        mat = bpy.data.materials.get("YellowR")
    else:
        mat = bpy.data.materials.get("YellowL")

    # 铸造法默认展示模式为透明
    if (prev_moudle == 'PARTICLES'):
        mat.blend_method = 'BLEND'
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
        elif bpy.context.scene.leftWindowObj == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
    # 排气孔默认展示模式为透明
    elif (prev_moudle == 'CONSTRAINT'):
        mat.blend_method = 'BLEND'
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
        elif bpy.context.scene.leftWindowObj == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
    # 软耳膜支撑显示为透明,硬耳膜支撑显示为非透明
    elif (prev_moudle == 'PHYSICS'):
        name = bpy.context.scene.leftWindowObj
        casting_name = name + "CastingCompare"
        casting_compare_obj = bpy.data.objects.get(casting_name)
        if(casting_compare_obj != None):
            mat.blend_method = 'BLEND'
            if bpy.context.scene.leftWindowObj == '右耳':
                bpy.context.scene.transparent3EnumR = 'OP3'
            elif bpy.context.scene.leftWindowObj == '左耳':
                bpy.context.scene.transparent3EnumL = 'OP3'
    # 切割模具模块（最后一个模块）显示为透明
    elif (prev_moudle == 'MATERIAL'):
        mat.blend_method = 'BLEND'
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP3'
        elif bpy.context.scene.leftWindowObj == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP3'
    # 打磨模块显示为非透明，并切换到第二种模型展示方式（打磨前）
    elif (prev_moudle == 'RENDER'):
        mat.blend_method = 'OPAQUE'
        mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.transparent2EnumR = 'OP1'
        elif bpy.context.scene.leftWindowObj == '左耳':
            bpy.context.scene.transparent2EnumL = 'OP1'
    # 其余模块的材质展示方式为不透明
    else:
        mat.blend_method = 'OPAQUE'
        mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 1
        if bpy.context.scene.leftWindowObj == '右耳':
            bpy.context.scene.transparent3EnumR = 'OP1'
        elif bpy.context.scene.leftWindowObj == '左耳':
            bpy.context.scene.transparent3EnumL = 'OP1'

    restart_modal(prev_moudle, prev_var)
    set_switch_flag(True)


def set_active_object():
    prev_mode = bpy.context.mode
    if prev_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        main_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)
        bpy.ops.object.mode_set(mode=prev_mode)
    else:
        main_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
        bpy.context.view_layer.objects.active = main_obj
        main_obj.select_set(True)


# --- 核心功能函数 ---
def record_state():
    """
    记录当前场景状态
    当模型发生修改时，调用此函数来保存当前场景的快照
    """
    global _undo_current_state_idx, _undo_max_saved_idx, MAX_HISTORY_SIZE, _history_globals, GLOBAL_VARS_TO_SAVE
    if not bpy.context.scene.needrecord:
        print("DEBUG: 记录状态被跳过，因为 needrecord 标志为 False。")
        return
    side = _get_side()
    state = _ensure_side_state(side)

    track_time("\n--- record_state start")
    print(f"record_state 开始 (side={side}) ---")
    print(f"初始全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")

    # 1. 仅清除当前侧的“未来”历史
    if state['current'] < state['max']:
        print(f"DEBUG: 检测到历史分支 (side={side})。清除从 {state['current'] + 1} 到 {state['max']} 的未来历史。")
        objects_to_delete = []
        for i in range(state['current'] + 1, state['max'] + 1):
            objects_to_delete.extend(_get_history_objects(i, side))
            hg = _get_history_globals_for_side(side)
            if i in hg:
                del hg[i]
        _delete_objects(objects_to_delete, f"清除未来历史 (side={side}, 从 {state['current'] + 1} 到 {state['max']})")
        _set_max_idx_for_side(side, state['current'])
        state['max'] = state['current']
        print(f"DEBUG: 未来历史已清除。新的 max_idx={state['max']}")

    # 2. 确定新状态的索引，并处理历史记录上限（按侧）
    new_state_idx = state['current'] + 1
    print(f"DEBUG: (side={side}) 尝试创建新状态索引: {new_state_idx}")

    if new_state_idx > MAX_HISTORY_SIZE:
        print(f"DEBUG: (side={side}) 历史记录已满 ({MAX_HISTORY_SIZE} 步)。正在滚动历史记录。")

        # 删除该侧最旧的状态 (前缀为 {side}_1_backup_)
        oldest_objects = _get_history_objects(1, side)
        _delete_objects(oldest_objects, f"删除最旧状态 (side={side}, 1_backup_)")
        hg = _get_history_globals_for_side(side)
        if 1 in hg:
            del hg[1]

        # 将该侧的其他历史状态的索引减一（2->1, 3->2 ...）
        print(f"DEBUG: (side={side}) 正在重命名历史状态 (2_backup_ -> 1_backup_, etc.)")
        for i in range(2, MAX_HISTORY_SIZE + 1):
            _rename_history_objects(i, i - 1, side)
            if i in hg:
                hg[i - 1] = hg.pop(i)

        # 新状态将占用 MAX_HISTORY_SIZE 的位置
        _set_current_idx_for_side(side, MAX_HISTORY_SIZE)
        _set_max_idx_for_side(side, MAX_HISTORY_SIZE)
        state['current'] = MAX_HISTORY_SIZE
        state['max'] = MAX_HISTORY_SIZE
        print(f"DEBUG: (side={side}) 历史记录已滚动。新的 current_idx={state['current']}, max_idx={state['max']}")
    else:
        # 历史记录未满，直接增加索引
        _set_current_idx_for_side(side, new_state_idx)
        _set_max_idx_for_side(side, new_state_idx)
        state['current'] = new_state_idx
        state['max'] = new_state_idx
        print(f"DEBUG: (side={side}) 历史记录未满。新的 current_idx={state['current']}, max_idx={state['max']}")

    # 3. 保存当前场景状态：复制当前侧的所有对象，并以侧别+索引作为前缀重命名
    active_objects = _get_active_objects()
    if not active_objects:
        print("警告: 当前场景中没有活跃对象可供保存。回滚索引。")
        # 如果没有活跃对象，我们不应该增加状态，回滚索引
        _set_current_idx_for_side(side, state['current'] - 1)
        _set_max_idx_for_side(side, state['max'] - 1)
        state['current'] -= 1
        state['max'] -= 1
        print(f"DEBUG: 回滚索引。最终状态: current_idx={state['current']}, max_idx={state['max']}")
        return

    # 4. 保存全局变量（保存到当前侧）
    print(f"DEBUG: 正在保存全局变量作为状态 {state['current']} (side={side})。")
    globals_to_save = {}
    globals_to_save["moudle"] = bpy.context.screen.areas[0].spaces.active.context
    globals_to_save["var"] = bpy.context.scene.var
    globals_to_save["finish"] = bpy.context.scene.pressfinish
    # 按模块读取需要保存的全局变量：按侧合并 side + Shared（支持旧的平面结构回退）
    for module_name, var_list in _get_var_sources_for_side(side):
        try:
            mod = sys.modules.get(module_name)
            if mod is None:
                # 尝试导入模块（如果尚未导入）
                mod = importlib.import_module(module_name)
        except Exception as e:
            print(f"WARNING: 无法导入模块 {module_name}: {e}")
            traceback.print_exc()
            continue

        for var_name in var_list:
            try:
                if hasattr(mod, var_name):
                    globals_to_save[f"{module_name}.{var_name}"] = getattr(mod, var_name)
                else:
                    # 未在模块中找到变量，跳过或按需处理
                    pass
            except Exception as e:
                print(f"WARNING: 读取 {module_name}.{var_name} 时出错: {e}")
                traceback.print_exc()
    # 5. 保存 Scene 属性（按侧合并 Side + Shared）
    try:
        scene = bpy.context.scene
        props_to_save = get_scene_props_to_save(side)
        for prop_name in props_to_save:
            try:
                # 优先使用 getattr（用于注册的 RNA 属性），否则尝试使用 item 访问（用于自定义属性）
                if hasattr(scene, prop_name):
                    val = getattr(scene, prop_name)
                else:
                    val = scene[prop_name] if prop_name in scene.keys() else None
                globals_to_save[f"scene.{prop_name}"] = val
            except Exception:
                # 若读取失败，仍然记录为 None 并打印异常以便调试
                globals_to_save[f"scene.{prop_name}"] = None
                print(f"WARNING: 读取 scene 属性 {prop_name} 时出错")
                traceback.print_exc()
    except Exception:
        print("WARNING: 无法获取 bpy.context.scene，跳过 Scene 属性保存。")
        traceback.print_exc()

    # 存入该侧的 history_globals
    _get_history_globals_for_side(side)[state['current']] = globals_to_save

    # 6. 复制当前侧的对象并以侧别+索引作为前缀保存为历史
    name = bpy.context.scene.leftWindowObj
    if name == "右耳":
        need_collect_objects = bpy.data.collections["Right"].objects
    else:
        need_collect_objects = bpy.data.collections["Left"].objects
    for obj in need_collect_objects:
        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()

        new_obj.name = f"{side}_{state['current']}{HISTORY_PREFIX_FORMAT}{obj.name}"

        for col in list(new_obj.users_collection):
            if new_obj.name in col.objects:
                col.objects.unlink(new_obj)

        if new_obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(new_obj)

        # 保存显示状态和集合信息
        new_obj['original_hide_viewport'] = obj.hide_get()
        new_obj['original_hide_render'] = obj.hide_render
        original_collections_names = [col.name for col in obj.users_collection]
        new_obj['original_collections'] = json.dumps(original_collections_names)

        new_obj.hide_set(True)
        new_obj.hide_render = True
        new_obj.select_set(False)

    print(f"--- record_state 结束 (side={side}) ---")
    print(f"最终全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")
    track_time("record_state end")
    reset_time_tracker()


def backup_state():
    """
    执行一步撤回操作：根据当前状态指针，恢复到上一个历史状态
    """
    global _undo_current_state_idx, _undo_max_saved_idx, MAX_HISTORY_SIZE, _history_globals, GLOBAL_VARS_TO_SAVE, is_processing_undo_redo

    side = _get_side()
    state = _ensure_side_state(side)

    track_time("\n--- backup start")
    print(f"backup 开始 (side={side}) ---")
    print(f"初始全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")
    is_processing_undo_redo = True

    # 1. 如果当前状态指针为 1，则无法再撤回
    if state['current'] == 1:
        print("DEBUG: 无法撤回，已是初始状态 (索引 1)。")
        return

    # 2. 确定要恢复的历史状态的索引（按侧）
    state_to_restore_prefix = state['current'] - 1
    print(f"DEBUG: (side={side}) 当前状态索引为 {state['current']}。目标恢复状态索引为 {state_to_restore_prefix}。")

    # 3. 删除当前场景中所有活跃的对象（没有前缀的对象）
    active_objects_to_delete = _get_active_objects()
    _delete_objects(active_objects_to_delete, "删除当前活跃对象")

    # 4. 恢复全局变量（从该侧的 history_globals）
    print(f"DEBUG: 正在从历史状态 {state_to_restore_prefix} 恢复全局变量 (side={side})。")
    saved_globals = _get_history_globals_for_side(side).get(state_to_restore_prefix, {})
    if saved_globals:
        _restore_globals_from_saved(saved_globals)
    else:
        print(f"警告: 未在 side={side} 的历史中找到状态 {state_to_restore_prefix} 的全局变量数据。")

    # 5. 恢复指定历史状态的对象（仅该侧）
    historical_objects_to_restore = []
    if state_to_restore_prefix > 0:
        historical_objects_to_restore = _get_history_objects(state_to_restore_prefix, side)

    if not historical_objects_to_restore and state_to_restore_prefix > 0:
        print(f"警告: 未找到 side={side} 状态 {state_to_restore_prefix} 的历史对象。场景可能为空。")

    for obj in historical_objects_to_restore:
        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()

        prefix = f"{side}_{state_to_restore_prefix}{HISTORY_PREFIX_FORMAT}"
        prefix_len_to_remove = len(prefix)
        new_obj.name = obj.name[prefix_len_to_remove:]

        # 恢复显示状态和集合信息
        original_hide_viewport = obj.get('original_hide_viewport', False)
        original_hide_render = obj.get('original_hide_render', False)

        original_collections_str = obj.get('original_collections', '[]')
        original_collections_names = []
        try:
            original_collections_names = json.loads(original_collections_str)
        except json.JSONDecodeError:
            try:
                original_collections_names = eval(original_collections_str)
                if not isinstance(original_collections_names, list):
                    original_collections_names = []
            except (SyntaxError, NameError):
                original_collections_names = []

        for col in list(new_obj.users_collection):
            if new_obj.name in col.objects:
                col.objects.unlink(new_obj)

        if original_collections_names:
            for col_name in original_collections_names:
                if col_name in bpy.data.collections:
                    target_collection = bpy.data.collections[col_name]
                    if new_obj.name not in target_collection.objects:
                        target_collection.objects.link(new_obj)
        else:
            if new_obj.name not in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.link(new_obj)

        new_obj.hide_set(original_hide_viewport)
        new_obj.hide_render = original_hide_render
        new_obj.select_set(False)

    # 6. 更新状态指针（仅该侧）
    _set_current_idx_for_side(side, state_to_restore_prefix)
    state['current'] = state_to_restore_prefix
    is_processing_undo_redo = False
    print(f"DEBUG: (side={side}) 状态指针已更新，当前为 {state['current']}。")

    set_active_object()
    current_module = bpy.context.screen.areas[0].spaces.active.context
    prev_moudle = saved_globals.get("moudle", None)
    prev_var = saved_globals.get("var", None)
    prev_finish = saved_globals.get("finish", None)
    if bpy.context.scene.pressfinish != prev_finish:
        if prev_finish:
            unregister_tools()
        if not prev_finish:
            register_tools()
            restart_modal(prev_moudle, prev_var)
    if current_module != prev_moudle:
        change_moudle(prev_moudle, prev_var)
   
    print(f"--- backup 结束 (side={side}) ---")
    print(f"最终全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")
    track_time("backup end")
    reset_time_tracker()


def forward_state():
    """
    执行一步前进（重做）操作：根据当前状态指针，恢复到下一个历史状态
    """
    global _undo_current_state_idx, _undo_max_saved_idx, MAX_HISTORY_SIZE, _history_globals, GLOBAL_VARS_TO_SAVE, is_processing_undo_redo

    side = _get_side()
    state = _ensure_side_state(side)

    track_time("\n--- forward start")
    print(f"forward 开始 (side={side}) ---")
    print(f"初始全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")

    is_processing_undo_redo = True
    # 如果没有可前进的状态
    if state['current'] >= state['max']:
        print("DEBUG: 无法前进，已是最新状态。")
        return

    # 目标恢复的历史索引（仅该侧）
    state_to_restore_prefix = state['current'] + 1
    print(f"DEBUG: (side={side}) 当前状态索引为 {state['current']}。目标前进到状态索引为 {state_to_restore_prefix}。")

    # 删除当前场景中所有活跃的对象（没有前缀的对象）
    active_objects_to_delete = _get_active_objects()
    _delete_objects(active_objects_to_delete, "删除当前活跃对象 (前进)")

    # 恢复全局变量（从该侧的 history_globals）
    print(f"DEBUG: 正在从历史状态 {state_to_restore_prefix} 恢复全局变量 (前进, side={side})。")
    saved_globals = _get_history_globals_for_side(side).get(state_to_restore_prefix, {})
    if saved_globals:
        _restore_globals_from_saved(saved_globals)
    else:
        print(f"警告: 未在 side={side} 的历史中找到状态 {state_to_restore_prefix} 的全局变量数据。")

    # 恢复指定历史状态的对象（仅该侧）
    historical_objects_to_restore = []
    if state_to_restore_prefix > 0:
        historical_objects_to_restore = _get_history_objects(state_to_restore_prefix, side)

    if not historical_objects_to_restore and state_to_restore_prefix > 0:
        print(f"警告: 未找到 side={side} 状态 {state_to_restore_prefix} 的历史对象。场景可能为空。")

    for obj in historical_objects_to_restore:
        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()

        prefix = f"{side}_{state_to_restore_prefix}{HISTORY_PREFIX_FORMAT}"
        prefix_len_to_remove = len(prefix)
        new_obj.name = obj.name[prefix_len_to_remove:]

        # 恢复对象显示状态与集合信息
        original_hide_viewport = obj.get('original_hide_viewport', False)
        original_hide_render = obj.get('original_hide_render', False)

        original_collections_str = obj.get('original_collections', '[]')
        original_collections_names = []
        try:
            original_collections_names = json.loads(original_collections_str)
        except json.JSONDecodeError:
            try:
                original_collections_names = eval(original_collections_str)
                if not isinstance(original_collections_names, list):
                    original_collections_names = []
            except (SyntaxError, NameError):
                original_collections_names = []

        for col in list(new_obj.users_collection):
            if new_obj.name in col.objects:
                col.objects.unlink(new_obj)

        if original_collections_names:
            for col_name in original_collections_names:
                if col_name in bpy.data.collections:
                    target_collection = bpy.data.collections[col_name]
                    if new_obj.name not in target_collection.objects:
                        target_collection.objects.link(new_obj)
        else:
            if new_obj.name not in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.link(new_obj)

        new_obj.hide_set(original_hide_viewport)
        new_obj.hide_render = original_hide_render
        new_obj.select_set(False)

    # 更新状态指针（仅该侧）
    _set_current_idx_for_side(side, state_to_restore_prefix)
    state['current'] = state_to_restore_prefix
    is_processing_undo_redo = False
    print(f"DEBUG: (side={side}) 状态指针已更新，当前为 {state['current']}。")

    set_active_object()
    current_module = bpy.context.screen.areas[0].spaces.active.context
    prev_moudle = saved_globals.get("moudle", None)
    prev_var = saved_globals.get("var", None)
    if bpy.context.scene.pressfinish:
        register_tools()
        bpy.context.scene.pressfinish = False
        restart_modal(prev_moudle, prev_var)
    if current_module != prev_moudle:
        change_moudle(prev_moudle, prev_var)

    print(f"--- forward 结束 (side={side}) ---")
    print(f"最终全局状态 (side={side}): current_idx={state['current']}, max_idx={state['max']}")
    track_time("forward end")
    reset_time_tracker()
