import bpy
from .damo import *
from .qiege import *


flag = True


def My_Properties():

    # 打磨操作属性      蜡厚度，局部蜡厚度限制，最大蜡厚度，最小蜡厚度
    bpy.types.Scene.laHouDU = bpy.props.FloatProperty(
        name="laHouDU", min=-2.0, max=2.0, step=1,
        description="调整蜡厚度的大小", update=Houdu)
    bpy.types.Scene.localLaHouDu = bpy.props.BoolProperty(
        name="localLaHouDu", default=False)
    bpy.types.Scene.maxLaHouDu = bpy.props.FloatProperty(
        name="maxLaHouDu", min=-1.0, max=1.0, step=1, description="最大蜡厚度的值")
    bpy.types.Scene.minLaHouDu = bpy.props.FloatProperty(
        name="minLaHouDu", min=-1.0, max=1.0, step=1, description="最小蜡厚度的值")

    # bpyabcdefghijklmnopqrstuvwxyzuvwuvwuvwxyz

    # 局部或整体加厚    偏移值，边框宽度
    bpy.types.Scene.pianYiZhi = bpy.props.FloatProperty(
        name="pianYiZhi", update=localOrGlobalJiaHou)
    bpy.types.Scene.bianKuangKuanDu = bpy.props.FloatProperty(
        name="bianKuangKuanDu", min=-1.0, max=1.0)

    # 点面切割属性
    bpy.types.Scene.qieGeTypeEnum = bpy.props.EnumProperty(
        name="qieGeTypeEnum",
        description='this is option',
        items=[
            ('OP1', '平面切割', ''),
            ('OP2', '阶梯状切割', '')],
        update=qiegeenum
    )
    bpy.types.Scene.sheRuPianYi = bpy.props.FloatProperty(
        name="sheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.waiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.neiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYi", min=-1.0, max=1.0)

    # 创建模具属性
    bpy.types.Scene.muJuTypeEnum = bpy.props.EnumProperty(
        name="muJuTypeEnum",
        description='this is option',
        items=[
            ('OP1', '软耳模', ''),
            ('OP2', '硬耳膜', ''),
            ('OP3', '外壳', ''),
            ('OP4', '框架式耳膜', '')]
    )
    bpy.types.Scene.neiBianJiXian = bpy.props.BoolProperty(
        name="neiBianJiXian")
    bpy.types.Scene.waiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.neiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYi", min=-1.0, max=1.0)

    bpy.types.Scene.zongHouDu = bpy.props.FloatProperty(
        name="zongHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.jiHuoBianYuanHouDu = bpy.props.BoolProperty(
        name="jiHuoBianYuanHouDu")
    bpy.types.Scene.waiBuHouDu = bpy.props.FloatProperty(
        name="waiBuHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.waiBuQuYuKuanDu = bpy.props.FloatProperty(
        name="waiBuQuYuKuanDu", min=-1.0, max=1.0)
    bpy.types.Scene.zhongJianHouDu = bpy.props.FloatProperty(
        name="zhongJianHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouShiYongNeiBu = bpy.props.BoolProperty(
        name="shiFouShiYongNeiBu")
    bpy.types.Scene.zhongJianQuYuKuanDu = bpy.props.FloatProperty(
        name="zhongJianQuYuKuanDu", min=-1.0, max=1.0)
    bpy.types.Scene.neiBuHouDu = bpy.props.FloatProperty(
        name="neiBuHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.mianBanTypeEnum = bpy.props.EnumProperty(
        name="mianBanTypeEnum",
        description='this is option',
        items=[
            ('OP1', '312空面板', '')]
    )
    bpy.types.Scene.jieShouQiTypeEnum = bpy.props.EnumProperty(
        name="jieShouQiTypeEnum",
        description='this is option',
        items=[
            ('OP1', 'REC31570', '')]
    )
    bpy.types.Scene.jieShouQiKaiGuanTypeEnum = bpy.props.EnumProperty(
        name="jieShouQiKaiGuanTypeEnum",
        description='this is option',
        items=[
            ('OP1', '外置套管', '')]
    )
    bpy.types.Scene.buJianBTypeEenu = bpy.props.EnumProperty(
        name="buJianBTypeEenu",
        description='this is option',
        items=[
            ('OP1', 'E7111', '')]
    )
    bpy.types.Scene.mianBanPianYi = bpy.props.FloatProperty(
        name="mianBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.xiaFangYangXianPianYi = bpy.props.FloatProperty(
        name="xiaFangYangXianPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shangSheRuYinZi = bpy.props.FloatProperty(
        name="shangSheRuYinZi", min=-1.0, max=1.0)
    bpy.types.Scene.xiaSheRuYinZi = bpy.props.FloatProperty(
        name="xiaSheRuYinZi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouShangBuQieGeMianBan = bpy.props.BoolProperty(
        name="shiFouShangBuQieGeMianBan")
    bpy.types.Scene.shangBuQieGeMianBanPianYi = bpy.props.FloatProperty(
        name="shangBuQieGeMianBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouKongQiangMianBan = bpy.props.BoolProperty(
        name="shiFouKongQiangMianBan")
    bpy.types.Scene.KongQiangMianBanSheRuPianYi = bpy.props.FloatProperty(
        name="KongQiangMianBanSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.ShangBuQieGeBanPianYi = bpy.props.FloatProperty(
        name="ShangBuQieGeBanPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.gongXingMianBan = bpy.props.FloatProperty(
        name="gongXingMianBan", min=-1.0, max=1.0)
    bpy.types.Scene.gongKuan = bpy.props.FloatProperty(
        name="gongKuan", min=-1.0, max=1.0)
    bpy.types.Scene.gongGao = bpy.props.FloatProperty(
        name="gongGao", min=-1.0, max=1.0)
    bpy.types.Scene.yingErMoSheRuPianYi = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouTongFengGuan = bpy.props.BoolProperty(
        name="shiFouTongFengGuan")
    bpy.types.Scene.tongFengGuanZhiJing = bpy.props.FloatProperty(
        name="tongFengGuanZhiJing", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanHouDu = bpy.props.FloatProperty(
        name="tongFengGuanHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanWaiBuHouDu = bpy.props.FloatProperty(
        name="tongFengGuanWaiBuHouDu", min=-1.0, max=1.0)

    # 传声孔      管道平滑      传声管道直径         激活   管道形状  偏移
    bpy.types.Scene.gaunDaoPinHua = bpy.props.BoolProperty(
        name="gaunDaoPinHua")
    bpy.types.Scene.chuanShenGuanDaoZhiJing = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing", min=-1.0, max=1.0)
    bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset = bpy.props.FloatProperty(
        name="chuanShenKongOffset", min=-1.0, max=1.0)
    bpy.types.Scene.shapeEnum = bpy.props.EnumProperty(
        name="shapeEnum",
        description='传声孔的形状',
        items=[
            ('OP1', '号角管1', ''),
            ('OP2', '号角管2', ''),
            ('OP3', '传声管1', ''),
            ('OP4', '传声管2', ''),
            ('OP5', '铜扣', ''),
            ('OP6', 'S喇叭', ''),
            ('OP7', 'M喇叭', ''),
            ('OP8', 'P喇叭', ''),
            ('OP9', 'SP喇叭', ''),
            ('OP10', 'RIC启敏喇叭', ''),
            ('OP11', 'HP喇叭', ''),
            ('OP12', '听诊器耳塞', '')]
    )

    # 通气孔     通气管道直径
    bpy.types.Scene.tongQiGuanDaoZhiJing = bpy.props.FloatProperty(
        name="tongQiGuanDaoZhiJing", min=-1.0, max=1.0)

    # 耳膜附件      耳膜附件类型    偏移
    bpy.types.Scene.erMoFuJianOffset = bpy.props.FloatProperty(
        name="erMoFuJianOffset", min=-1.0, max=1.0)
    bpy.types.Scene.erMoFuJianTypeEnum = bpy.props.EnumProperty(
        name="erMoFuJianTypeEnum",
        description='handle耳膜附件的类型',
        items=[
            ('OP1', '耳膜附件', ''),
        ]
    )

    # 编号
    bpy.types.Scene.fontSize = bpy.props.FloatProperty(
        name="fontSize", min=-1.0, max=1.0)
    bpy.types.Scene.deep = bpy.props.FloatProperty(
        name="deep", min=-1.0, max=1.0)
    bpy.types.Scene.styleEnum = bpy.props.EnumProperty(
        name="styleEnum",
        description='编号的风格',
        items=[
            ('OP1', '内嵌', ''),
            ('OP2', '外凸', ''),]
    )

    # 软耳模厚度       厚度类型    软耳模厚度
    bpy.types.Scene.ruanErMoHouDu = bpy.props.FloatProperty(
        name="ruanErMoHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.ruanErMoTypeEnum = bpy.props.EnumProperty(
        name="ruanErMoTypeEnum",
        description='',
        items=[
            ('OP1', '偏移曲面', ''),
            ('OP2', '无', ''),]
    )

    # 支撑        支撑类型     偏移
    bpy.types.Scene.zhiChengOffset = bpy.props.FloatProperty(
        name="zhiChengOffset", min=-1.0, max=1.0)
    bpy.types.Scene.zhiChengTypeEnum = bpy.props.EnumProperty(
        name="zhiChengTypeEnum",
        description='',
        items=[
            ('OP1', '软耳模支撑', ''),
            ('OP2', '硬耳膜支撑', ''),]
    )

    # 排气孔        排气孔类型     偏移
    bpy.types.Scene.paiQiKongOffset = bpy.props.FloatProperty(
        name="paiQiKongOffset", min=-1.0, max=1.0)
    bpy.types.Scene.paiQiKongTypeEnum = bpy.props.EnumProperty(
        name="paiQiKongTypeEnum",
        description='',
        items=[
            ('OP1', '排气孔', ''),]
    )


# 添加厚度修改器
def modify(self, context, thinckness):
    global flag
    context1 = bpy.context.space_data.context
    if flag == True and context1 == 'RENDER':
        flag = False
        obj = bpy.context.active_object
        md = obj.modifiers.new("jiahou", "SOLIDIFY")
        md.use_rim_only = True
        md.use_quality_normals = True
        md.offset = 1
        md.thickness = context.scene.laHouDU
        # context.window_manager.modal_handler_add(self)
        # MyHandleClass.add_handler(draw_callback_px,(None,context.scene.laHouDU))
        return {'RUNNING_MODAL'}
    else:
        if thinckness < 0:
            name = bpy.context.active_object.name
            md = bpy.data.objects[name].modifiers["jiahou"]
            md.use_flip_normals = True

        else:
            name = bpy.context.active_object.name
            md = bpy.data.objects[name].modifiers["jiahou"]
            md.use_flip_normals = False
        # MyHandleClass.remove_handler()
        return {'FINISHED'}


def Houdu(self, context):
    bl_description = "初始耳模的厚度"
    thickness = context.scene.laHouDU
    modify(self, context, thickness)
    active_object = bpy.context.active_object
    name = active_object.name
    bpy.data.objects[name].modifiers["jiahou"].thickness = thickness
    # MyHandleClass.remove_handler()
    # MyHandleClass.add_handler(draw_callback_px, (None, thickness))


def qiegeenum(self, context):
    bl_description = "选择切割方式"
    enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        quitStepCut()
        initCircle()
    if enum == "OP2":
        quitCut()
        initPlane()


# 回调函数，根据绑定的属性值更改选中区域的厚度


def localOrGlobalJiaHou(self, context):
    bl_description = "所选区域增加的厚度"
    thickness = context.scene.pianYiZhi
    bpy.data.objects["Mesh"].modifiers["geometry_extract_solidify"].thickness = thickness


def register():
    My_Properties()

# def unregister():
