import bpy
from bpy.types import WorkSpaceTool
import bpy_extras
from .prop import *
from math import *
import mathutils
import bmesh
from bpy_extras import view3d_utils

var =0                                      #全局变量,切换不同按钮的model     加厚，打薄，光滑

prev_on_object=False                        #全局变量,保存之前的鼠标状态,用于判断鼠标状态是否改变(如从物体上移动到公共区域或从公共区域移动到物体上)









#获取区域和空间，鼠标行为切换相关
def get_region_and_space(context, area_type, region_type, space_type):
    region = None
    area = None
    space = None

    # 获取指定区域的信息
    for a in context.screen.areas:
        if a.type == area_type:
            area = a
            break
    else:
        return (None, None)
    # 获取指定区域的信息
    for r in area.regions:
        if r.type == region_type:
            region = r
            break
    # 获取指定区域的信息
    for s in area.spaces:
        if s.type == space_type:
            space = s
            break

    return (region, space)






#判断鼠标是否在物体上
def is_mouse_on_object(context, event):
    active_obj = context.active_object

                                     
    is_on_object = False  # 初始化变量

    if context.area:  
        context.area.tag_redraw()

    # 获取鼠标光标的区域坐标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(                                            
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    ray_dir = view3d_utils.region_2d_to_vector_3d(
        region,
        space.region_3d,
        mv
    )
    ray_orig = view3d_utils.region_2d_to_origin_3d(
        region,
        space.region_3d,
        mv
    )

    start = ray_orig
    end = ray_orig + ray_dir

    # 确定光线和对象的相交
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                is_on_object = True  # 如果发生交叉，将变量设为True
    return is_on_object




#判断鼠标状态是否发生改变
def is_changed(context, event):
    active_obj = context.active_object

                                     
    curr_on_object = False             # 当前鼠标是否在物体上,初始化为False
    global prev_on_object              #之前鼠标是否在物体上

    if context.area:  
        context.area.tag_redraw()

    # 获取鼠标光标的区域坐标
    mv = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

    # 获取信息和空间信息
    region, space = get_region_and_space(                                            
        context, 'VIEW_3D', 'WINDOW', 'VIEW_3D'
    )

    ray_dir = view3d_utils.region_2d_to_vector_3d(
        region,
        space.region_3d,
        mv
    )
    ray_orig = view3d_utils.region_2d_to_origin_3d(
        region,
        space.region_3d,
        mv
    )

    start = ray_orig
    end = ray_orig + ray_dir

    # 确定光线和对象的相交
    mwi = active_obj.matrix_world.inverted()
    mwi_start = mwi @ start
    mwi_end = mwi @ end
    mwi_dir = mwi_end - mwi_start

    if active_obj.type == 'MESH':
        if (active_obj.mode == 'OBJECT' or active_obj.mode == "SCULPT"):
            mesh = active_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm)

            _, _, fidx, _ = tree.ray_cast(mwi_start, mwi_dir, 2000.0)

            if fidx is not None:
                curr_on_object = True                     # 如果发生交叉，将变量设为True
    if(curr_on_object!=prev_on_object):
        prev_on_object=curr_on_object
        return True
    else:
        return False




#打磨功能模块左侧按钮的加厚操作
class Thickening(bpy.types.Operator):
    bl_idname="object.thickening"
    bl_label="加厚操作"
    bl_description="点击鼠标左键加厚模型，右键改变区域选取圆环的大小"
                                    #自定义的鼠标右键行为参数
    __right_mouse_down=False                    #按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x=None                          #鼠标移动时的位置
    __now_mouse_y=None                 
    __initial_mouse_x=None                      #点击鼠标右键的初始位置
    __initial_mouse_y=None
    global var

    # #打磨模块下左侧的三个按钮才起作用
    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'


    def invoke(self,context,event):    
        global var
        var=1
        op_cls = Thickening               
        print("thicking_invoke")   
        if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()               
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")   #调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction="ADD"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100      #将用于框选区域的圆环半径设置为500
        if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
            bpy.ops.sculpt.sculptmode_toggle()                
        bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
        op_cls.__right_mouse_down=False                               #初始化鼠标右键行为操作
        op_cls.__now_mouse_x=None                         
        op_cls.__now_mouse_y=None                  
        op_cls.__initial_mouse_x=None                     
        op_cls.__initial_mouse_y=None                                 #锁定圆环和模型的比例
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  
        context.window_manager.modal_handler_add(self)         #进入modal模式
        return {'RUNNING_MODAL'}       


    def modal(self,context,event):
        op_cls=Thickening
        global var 
        if(var==1):
            if (is_mouse_on_object(context,event)):
                if(is_changed(context,event)):
                    if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
                        bpy.ops.sculpt.sculptmode_toggle()               
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")   #调用加厚笔刷
                    bpy.data.brushes["SculptDraw"].direction="ADD"
                if event.type=='RIGHTMOUSE':       #点击鼠标右键，改变区域选取圆环的大小
                    if event.value=='PRESS':                   #按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x=event.mouse_region_x
                        op_cls.__initial_mouse_y=event.mouse_region_y
                        op_cls.__right_mouse_down=True
                    elif event.value=='RELEASE':               
                        op_cls.__right_mouse_down=False         #松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小     
                    return {'RUNNING_MODAL'}
                elif event.type=='MOUSEMOVE':
                    if op_cls.__right_mouse_down:               #鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y=event.mouse_region_y
                        op_cls.__now_mouse_x=event.mouse_region_x
                        dis=int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)+fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size=dis    
            elif((not is_mouse_on_object(context,event)) and is_changed(context,event)):
                if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
                    bpy.ops.sculpt.sculptmode_toggle()                
                bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
            return{'PASS_THROUGH'}
        else:
            return {'FINISHED'}    
            








#打磨功能模块左侧按钮的减薄操作
class Thinning(bpy.types.Operator):
    bl_idname="object.thinning"
    bl_label="减薄操作"
    bl_description="点击鼠标左键减薄模型，右键改变区域选取圆环的大小"
                                    #自定义的鼠标右键行为参数
    __right_mouse_down=False                    #按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x=None                          #鼠标移动时的位置
    __now_mouse_y=None                 
    __initial_mouse_x=None                      #点击鼠标右键的初始位置
    __initial_mouse_y=None

    # @classmethod
    # def poll(cls,context):
    #     return context.space_data.type == 'VIEW_3D' and context.space_data.shading.type == 'RENDERED'

        
    def invoke(self,context,event):   
        global var
        var=2                  
        op_cls = Thinning
        print("thinning_invoke")
        if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()               
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")   #调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction="ADD"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100      #将用于框选区域的圆环半径设置为500
        if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
            bpy.ops.sculpt.sculptmode_toggle()                
        bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
        __right_mouse_down=False                               #初始化鼠标右键行为操作
        __now_mouse_x=None                         
        __now_mouse_y=None                 
        __initial_mouse_x=None                     
        __initial_mouse_y=None                                 #锁定圆环和模型的比例
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  
        context.window_manager.modal_handler_add(self)         #进入modal模式
        return {'RUNNING_MODAL'}      


    def modal(self,context,event):
        op_cls=Thinning
        global var
        if(var==2):
            if (is_mouse_on_object(context,event)):
                if(is_changed(context,event)):
                    if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
                        bpy.ops.sculpt.sculptmode_toggle()               
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")   #调用减薄笔刷
                    bpy.data.brushes["SculptDraw"].direction="SUBTRACT"  
                if event.type=='RIGHTMOUSE':       #点击鼠标右键，改变区域选取圆环的大小
                    if event.value=='PRESS':                   #按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x=event.mouse_region_x
                        op_cls.__initial_mouse_y=event.mouse_region_y
                        op_cls.__right_mouse_down=True
                    elif event.value=='RELEASE':               
                        op_cls.__right_mouse_down=False         #松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小     
                    return {'RUNNING_MODAL'}
                elif event.type=='MOUSEMOVE':
                    if op_cls.__right_mouse_down:               #鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y=event.mouse_region_y
                        op_cls.__now_mouse_x=event.mouse_region_x
                        dis=int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)+fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size=dis    
            elif((not is_mouse_on_object(context,event)) and is_changed(context,event)):
                if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
                    bpy.ops.sculpt.sculptmode_toggle()                
                bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
            return{'PASS_THROUGH'}
        else:
            return {'FINISHED'}    



#打磨功能模块左侧按钮的光滑操作
class Smooth(bpy.types.Operator):
    bl_idname="object.smooth"
    bl_label="光滑操作"
    bl_description="点击鼠标左键光滑模型，右键改变区域选取圆环的大小"
                                    #自定义的鼠标右键行为参数
    __right_mouse_down=False                    #按下右键未松开时，移动鼠标改变圆环大小
    __now_mouse_x=None                          #鼠标移动时的位置
    __now_mouse_y=None                 
    __initial_mouse_x=None                      #点击鼠标右键的初始位置
    __initial_mouse_y=None


    # @classmethod
    # def poll(context):
    #     if(context.space_data.context == 'RENDER'):
    #         return True
    #     else:
    #         return False

    def invoke(self,context,event):                         
        op_cls = Smooth
        global var
        var=3
        print("smooth_invoke")
        if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
            bpy.ops.sculpt.sculptmode_toggle()               
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")   #调用加厚笔刷
        bpy.data.brushes["SculptDraw"].direction="ADD"
        bpy.context.scene.tool_settings.unified_paint_settings.size = 100      #将用于框选区域的圆环半径设置为500
        if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
            bpy.ops.sculpt.sculptmode_toggle()                
        bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
        __right_mouse_down=False                               #初始化鼠标右键行为操作
        __now_mouse_x=None                         
        __now_mouse_y=None                 
        __initial_mouse_x=None                     
        __initial_mouse_y=None                                 #锁定圆环和模型的比例
        bpy.context.scene.tool_settings.unified_paint_settings.use_locked_size = 'SCENE'  
        context.window_manager.modal_handler_add(self)         #进入modal模式
        return {'RUNNING_MODAL'}   


    def modal(self,context,event):
        op_cls=Smooth
        global var
        if(var==3):
            if (is_mouse_on_object(context,event)):
                if(is_changed(context,event)):
                    if bpy.context.mode == "OBJECT":                       #将默认的物体模式切换到雕刻模式
                        bpy.ops.sculpt.sculptmode_toggle()               
                    bpy.context.space_data.shading.type = 'MATERIAL'       #调用光滑笔刷
                    bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
                if event.type=='RIGHTMOUSE':       #点击鼠标右键，改变区域选取圆环的大小
                    if event.value=='PRESS':                   #按下鼠标右键，保存鼠标点击初始位置，标记鼠标右键已按下，移动鼠标改变圆环大小
                        op_cls.__initial_mouse_x=event.mouse_region_x
                        op_cls.__initial_mouse_y=event.mouse_region_y
                        op_cls.__right_mouse_down=True
                    elif event.value=='RELEASE':               
                        op_cls.__right_mouse_down=False         #松开鼠标右键，标记鼠标右键未按下，移动鼠标不再改变圆环大小，结束该事件，确定圆环的大小     
                    return {'RUNNING_MODAL'}
                elif event.type=='MOUSEMOVE':
                    if op_cls.__right_mouse_down:               #鼠标右键按下时，鼠标移动改变圆环大小
                        op_cls.__now_mouse_y=event.mouse_region_y
                        op_cls.__now_mouse_x=event.mouse_region_x
                        dis=int(sqrt(fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)*fabs(op_cls.__now_mouse_y-op_cls.__initial_mouse_y)+fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)*fabs(op_cls.__now_mouse_x-op_cls.__initial_mouse_x)))
                        bpy.data.scenes["Scene"].tool_settings.unified_paint_settings.size=dis    
            elif((not is_mouse_on_object(context,event)) and is_changed(context,event)):
                if bpy.context.mode == "SCULPT":                       #将默认的雕刻模式切换到物体模式
                    bpy.ops.sculpt.sculptmode_toggle()                
                bpy.ops.wm.tool_set_by_id(name="builtin.select")           #切换到选择模式
            return{'PASS_THROUGH'}
        else:
            return{'FINISHED'}







class MyTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thickening"
    bl_label = "加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        ("object.thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
                        {"properties": [("wait_for_input", False)]}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool2(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thickening2"
    bl_label = "加厚"
    bl_description = (
        "使用鼠标拖动加厚耳模"
    )
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        ("object.thickening", {"type": 'MOUSEMOVE', "value": 'ANY'},
                        {"properties": [("wait_for_input", False)]}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool3(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thinning"
    bl_label = "磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.mesh.spin"
    bl_widget = None
    bl_keymap = (
        ("object.thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
                        {"properties": [("wait_for_input", False)]}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool4(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.thinning2"
    bl_label = "磨小"
    bl_description = (
        "使用鼠标拖动磨小耳模"
    )
    bl_icon = "ops.mesh.spin"
    bl_widget = None
    bl_keymap = (
        ("object.thinning", {"type": 'MOUSEMOVE', "value": 'ANY'},
                        {"properties": [("wait_for_input", False)]}),
    )

    def draw_settings(context, layout, tool):
        pass

class MyTool5(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'SCULPT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smooth"
    bl_label = "圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.mesh.extrude_region_move"
    bl_widget = None
    bl_keymap = (
        ("object.smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
                            {"properties": [("wait_for_input", False)]}),
    )
    def draw_settings(context, layout, tool):
        pass

class MyTool6(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    # The prefix of the idname should be your add-on name.
    bl_idname = "my_tool.smooth2"
    bl_label = "圆滑"
    bl_description = (
        "使用鼠标拖动圆滑耳模"
    )
    bl_icon = "ops.mesh.extrude_region_move"
    bl_widget = None
    bl_keymap = (
        ("object.smooth", {"type": 'MOUSEMOVE', "value": 'ANY'},
                            {"properties": [("wait_for_input", False)]}),
    )
    def draw_settings(context, layout, tool):
        pass


#注册类
_classes  = [

    Thickening,
    Thinning,
    Smooth,
    ]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.utils.register_tool(MyTool,separator=True, group=False)
    bpy.utils.register_tool(MyTool3,separator=True, group=False,after={MyTool.bl_idname})
    bpy.utils.register_tool(MyTool5,separator=True, group=False,after={MyTool3.bl_idname})

    bpy.utils.register_tool(MyTool2,separator=True, group=False)
    bpy.utils.register_tool(MyTool4,separator=True, group=False,after={MyTool2.bl_idname})
    bpy.utils.register_tool(MyTool6,separator=True, group=False,after={MyTool4.bl_idname})


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_tool(MyTool)
    bpy.utils.unregister_tool(MyTool3)
    bpy.utils.unregister_tool(MyTool5)

    bpy.utils.unregister_tool(MyTool2)
    bpy.utils.unregister_tool(MyTool4)
    bpy.utils.unregister_tool(MyTool6)