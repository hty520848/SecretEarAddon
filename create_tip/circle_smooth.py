import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty
import bmesh
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
from math import degrees, radians, sin, cos, pi
from ..tool import delete_vert_group
import mathutils
import math


class Circle_Smooth(bpy.types.Operator):
    bl_idname = "circle.smooth"
    bl_label = "Circle: Smooth"
    bl_description = "description"
    bl_options = {'REGISTER', 'UNDO'}

    boolean_solver_items = [("FAST", "Fast", ""),
                            ("EXACT", "Exact", "")]

    width: FloatProperty(name="Width", default=0.1, min=0, step=10)
    resample: BoolProperty(name="Resample", default=True)
    factor: FloatProperty(name="Factor", default=1, min=0.5)
    smooth: BoolProperty(name="Smooth", default=False)
    iterations: IntProperty(name="Iterations", default=1, min=1)
    optimize: BoolProperty(name="Optimize", default=True)
    angle: FloatProperty(name="Angle", default=180, min=0, max=180)
    extend: FloatProperty(name="Extend", default=0.2, min=0)
    override: BoolProperty(name="Spread", default=False)
    rails: IntProperty(name="Precision", default=18, min=7)
    tilt: FloatProperty(name="Wiggle", default=1)
    shift: BoolProperty(name="Shift", default=True)
    solver: EnumProperty(name="Solver", items=boolean_solver_items)
    center_border_group_name: bpy.props.StringProperty(name="CenterBorderGroupName", default="CenterBorder")
    max_smooth_width: FloatProperty(name="max_width", default=0)

    shade_smooth: BoolProperty(default=False)
    mark_sharp: BoolProperty(default=False)
    all_cyclic: BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        column.prop(self, "width")

        if not self.all_cyclic:
            split = column.split(factor=0.7, align=True)
            split.prop(self, "extend")
            split.prop(self, "override", toggle=True)

        column.separator()

        row = column.row(align=True)

        row.prop(self, "resample", toggle=True)
        r = row.split(align=True)
        r.active = self.resample
        r.prop(self, "factor")

        row = column.row(align=True)
        row.prop(self, "smooth", toggle=True)
        r = row.split(align=True)
        r.active = self.smooth
        r.prop(self, "iterations")

        row = column.row(align=True)
        row.prop(self, "optimize", toggle=True)
        r = row.split(align=True)
        r.active = self.optimize
        r.prop(self, "angle")

        row = column.row(align=True)
        row.prop(self, "solver", expand=True)

        column.separator()

        row = column.row(align=True)
        row.prop(self, "rails")
        row.prop(self, "tilt")
        row.prop(self, "shift", toggle=True)

    def execute(self, context):
        active = context.active_object
        mxw = active.matrix_world

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        edge_layer, face_layer = self.get_data_layers(bm, force_new=True)

        verts = [v for v in bm.verts if v.select]

        sequences = get_selected_vert_sequences(verts, debug=False)

        edge = bm.edges.get((sequences[0][0][0], sequences[0][0][1]))
        face = edge.link_faces[0]
        self.mark_sharp = not edge.smooth
        self.shade_smooth = face.smooth
        self.all_cyclic = all(cyclic for _, cyclic in sequences)

        circle_coords, circle_normals = create_circle_coords(self.width, self.rails, self.tilt, calc_normals=True,
                                                             debug=False)

        pipes = []
        all_pipe_faces = []
        face_maps = []

        for idx, (seq, cyclic) in enumerate(sequences):
            coords = create_pipe_coords(seq, cyclic, self.resample, self.factor, self.smooth, self.iterations,
                                        self.optimize, self.angle, mxw, debug=False)

            ext_coords = self.extend_coords(coords, cyclic, self.extend)

            ring_coords = create_pipe_ring_coords(ext_coords, cyclic, circle_coords, circle_normals, mx=mxw,
                                                  debug=False)

            vert_rings = self.create_pipe_verts(bm, ring_coords, cyclic, mx=mxw, debug=False)

            pipe_faces = self.create_pipe_faces(bm, vert_rings, cyclic, edge_layer, face_layer, idx, self.shift,
                                                self.shade_smooth)
            all_pipe_faces.extend(pipe_faces)

            pipes.append((coords, cyclic))

        bmesh.ops.recalc_face_normals(bm, faces=all_pipe_faces)
        bmesh.update_edit_mesh(active.data)

        for idx in range(len(pipes)):
            self.boolean_pipe(bm, face_layer, idx)

        pipe_cut()

        # return {'FINISHED'}

        bpy.ops.mesh.select_all(action='DESELECT')

        active = context.active_object
        bm = bmesh.from_edit_mesh(active.data)
        edge_layer = bm.edges.layers.string.get('OffsetCutEdges')
        face_layer = bm.faces.layers.int.get('OffsetCutFaces')
        vert_layer = bm.verts.layers.int.new('OffsetCutVerts')

        # merge_verts = []
        # junk_edges = []
        # edges = []

        for pipe_idx, (coords, cyclic) in enumerate(pipes):
            faces = [f for f in bm.faces if f[face_layer] == pipe_idx + 1]
            edges = {e for f in faces for e in f.edges}
            verts = {v for f in faces for v in f.verts}

            geom = bmesh.ops.region_extend(bm, geom=faces, use_faces=True)
            border_faces = geom['geom']
            border_edges = {e for f in border_faces for e in f.edges}
            border_verts = {v for f in border_faces for v in f.verts}

            select_vert(edges, edge_layer, pipe_idx, coords, border_verts, vert_layer)

            # sweeps, non_sweep_edges, has_caps = self.get_sorted_sweep_edges(len(coords), edges, edge_layer, pipe_idx)

            # end_rail_edges = self.set_end_sweeps(sweeps, border_verts, border_edges) if not cyclic and len(
            #     sweeps) > 2 else set()

            # junk = self.collect_junk_edges(non_sweep_edges, border_edges, border_verts, end_rail_edges)
            # junk_edges.extend(junk)

            # merge = self.recreate_hard_edges(sweeps, cyclic, coords, border_verts, self.override, vert_layer)
            # merge_verts.extend(merge)

            # self.mark_end_sweep_edges_sharp(self.mark_sharp, cyclic, has_caps, border_edges, merge_verts)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='10', regular=True)
        bpy.ops.mesh.select_all(action='DESELECT')

        get_outer_and_inner_vert_group()
        delete_inner_part()

        # resample_outer_border(len(coords))

        # 添加每个环的圆心
        active = context.active_object
        bm = bmesh.from_edit_mesh(active.data)
        vert_layer = bm.verts.layers.int.get('OffsetCutVerts')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(active.data)

        new_verts = list()
        for idx, coord in enumerate(coords):
            new_vert = bm.verts.new(coord)
            # 标记顶点
            new_vert[vert_layer] = idx + 1
            new_verts.append(new_vert)
        bm.verts.index_update()  # 更新顶点索引
        # 连接顶点生成边
        for i in range(len(new_verts)):
            v1 = new_verts[i]
            v2 = new_verts[(i + 1) % len(new_verts)]  # 确保形成闭环
            bm.edges.new([v1, v2])
        bmesh.update_edit_mesh(active.data)
        bpy.ops.mesh.select_all(action='DESELECT')
        for v in new_verts:
            v.select = True
        bpy.ops.object.vertex_group_set_active(group=self.center_border_group_name)
        bpy.ops.object.vertex_group_assign()

        vert_layer = bm.verts.layers.int.get('OffsetCutVerts')
        scale_factor = 0.1 + (self.max_smooth_width - self.width) / self.max_smooth_width * 0.8
        scale_border(scale_factor, self.center_border_group_name, vert_layer)

        bridge_border(self.width, self.center_border_group_name)

        fill_inner_part()

        bm = bmesh.new()
        bm.from_mesh(active.data)

        # bmesh.ops.dissolve_edges(bm, edges=junk_edges, use_verts=True)
        # bmesh.ops.remove_doubles(bm, verts=[v for v in merge_verts if v.is_valid], dist=0.00001)

        bm.select_flush(True)

        # self.mark_selected_sharp(bm, self.mark_sharp)
        # bmesh.update_edit_mesh(active.data)

        edge_layer = bm.edges.layers.string.get('OffsetCutEdges')
        face_layer = bm.faces.layers.int.get('OffsetCutFaces')
        vert_layer = bm.verts.layers.int.get('OffsetCutVerts')

        bm.edges.layers.string.remove(edge_layer)
        bm.faces.layers.int.remove(face_layer)
        bm.verts.layers.int.remove(vert_layer)

        bm.to_mesh(active.data)
        bm.free()

        # 删除顶点组
        delete_vert_group("CircleCutOuter")
        delete_vert_group(self.center_border_group_name)
        delete_vert_group("CircleCutInner")

        bpy.ops.object.shade_smooth()

        return {'FINISHED'}

    def get_data_layers(self, bm, force_new=False):
        edge_layer = bm.edges.layers.string.get('OffsetCutEdges')
        face_layer = bm.faces.layers.int.get('OffsetCutFaces')

        if force_new:
            if edge_layer:
                bm.edges.layers.string.remove(edge_layer)

            if face_layer:
                bm.faces.layers.int.remove(face_layer)

        edge_layer = bm.edges.layers.string.new('OffsetCutEdges')
        face_layer = bm.faces.layers.int.new('OffsetCutFaces')

        return edge_layer, face_layer

    def extend_coords(self, coords, cyclic, extend):
        if not cyclic and extend:
            ext_coords = coords.copy()

            start_dir = (coords[0] - coords[1]).normalized()
            ext_coords[0] = coords[0] + start_dir * extend

            end_dir = (coords[-1] - coords[-2]).normalized()
            ext_coords[-1] = coords[-1] + end_dir * extend

        else:
            ext_coords = coords

        return ext_coords

    def create_pipe_verts(self, bm, ring_coords, cyclic, mx=None, debug=False):
        vert_rings = []

        for ridx, ring in enumerate(ring_coords):
            if ridx == len(ring_coords) - 1:
                if cyclic:
                    next_ring = ring_coords[0]
                else:
                    verts = []
                    for co, _ in ring:
                        v = bm.verts.new(co)
                        verts.append(v)

                    vert_rings.append((verts, 0))
                    continue
            else:
                next_ring = ring_coords[ridx + 1]

            first_co, first_nrm = ring[0]

            dots = [(idx, co, first_nrm.dot(nrm)) for idx, (co, nrm) in enumerate(next_ring)]
            maxdot = max(dots, key=lambda x: x[2])

            shift_amount = maxdot[0]

            if debug and mx:
                draw_line([first_co, maxdot[1]], mx=mx, color=(1, 1, 0), alpha=0.5, modal=False)

            verts = []
            for co, _ in ring:
                v = bm.verts.new(co)
                verts.append(v)

            vert_rings.append((verts, shift_amount))

        return vert_rings

    def create_pipe_faces(self, bm, vert_rings, cyclic, edge_layer, face_layer, pipe_idx, shift, smooth):
        pipe_faces = []

        for ridx, ring in enumerate(vert_rings):
            if cyclic:
                if ridx == len(vert_rings) - 1:
                    next_verts = vert_rings[0][0]

                else:
                    next_verts = vert_rings[ridx + 1][0]

            else:
                if ridx in [0, len(vert_rings) - 1]:
                    f = bm.faces.new(ring[0])

                    f[face_layer] = pipe_idx + 1
                    pipe_faces.append(f)

                    for e in f.edges:
                        d = {pipe_idx: ridx}
                        e[edge_layer] = str(d).encode()

                    if ridx == len(vert_rings) - 1:
                        continue

                next_verts = vert_rings[ridx + 1][0]

            verts, shift_amount = ring

            if shift and shift_amount:
                next_verts = next_verts.copy()
                rotate_list(next_verts, shift_amount)

            for vidx, (v, vn) in enumerate(zip(verts, next_verts)):

                if vidx < self.rails - 1:
                    f = bm.faces.new([v, verts[vidx + 1], next_verts[vidx + 1], vn])

                else:
                    f = bm.faces.new([v, verts[0], next_verts[0], vn])

                f.smooth = smooth

                if cyclic or ridx > 0:
                    e = f.edges[0]
                    d = {pipe_idx: ridx}
                    e[edge_layer] = str(d).encode()

                f[face_layer] = pipe_idx + 1

                pipe_faces.append(f)

        return pipe_faces

    def boolean_pipe(self, bm, face_layer, pipe_idx):

        bpy.ops.mesh.select_all(action='DESELECT')

        for f in bm.faces:
            if f[face_layer] == pipe_idx + 1:
                f.select_set(True)

        # bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE', solver=self.solver)

    def mark_selected_sharp(self, bm, mark_sharp):
        if mark_sharp:
            for e in bm.edges:
                if e.select:
                    e.smooth = False

    def mark_end_sweep_edges_sharp(self, mark_sharp, cyclic, has_caps, border_edges, merge_verts):
        if cyclic or has_caps or not mark_sharp:
            return

        else:
            for e in [e for e in border_edges if any([v in merge_verts for v in e.verts])]:
                e.smooth = False

    def collect_junk_edges(self, non_sweep_edges, border_edges, border_verts, end_rail_edges):
        junk = set()

        for e in non_sweep_edges - border_edges - end_rail_edges:
            if any(v in border_verts for v in e.verts):
                junk.add(e)

        return list(junk)

    def recreate_hard_edges(self, sweeps, cyclic, coords, border_verts, override, vert_layer):
        merge = set()

        for idx, (sweep, co) in enumerate(zip(sweeps, coords)):
            if sweep:
                sweep_verts = {v for e in sweep for v in e.verts}

                for v in sweep_verts:
                    if v in border_verts:
                        v[vert_layer] = idx + 1

                # if cyclic or 0 < idx < len(sweeps) - 1 or override:
                #     sweep_verts -= border_verts

                # for v in sweep_verts:
                #     v.co = co

                #     merge.add(v)

                #     v.select_set(True)

        return merge

    def set_end_sweeps(self, sweeps, border_verts, border_edges):
        end_rails = set()

        if sweeps[1]:
            for e in sweeps[1]:
                if not any([v in border_verts for v in e.verts]):
                    sweep = []

                    for loop in e.link_loops:
                        start_loop = loop

                        while True:
                            loop = loop.link_loop_next

                            if loop.edge in border_edges:
                                sweep.append(loop.edge)

                            else:
                                end_rails.add(loop.edge)

                            if loop == start_loop:
                                break

                    if sweeps[0] is None:
                        sweeps[0] = sweep

                    else:
                        sweeps[0].extend(sweep)

        if sweeps[-2]:
            for e in sweeps[-2]:
                if not any([v in border_verts for v in e.verts]):
                    sweep = []

                    for loop in e.link_loops:
                        start_loop = loop

                        while True:
                            loop = loop.link_loop_next

                            if loop.edge in border_edges:
                                sweep.append(loop.edge)

                            else:
                                end_rails.add(loop.edge)

                            if loop == start_loop:
                                break

                            if sweeps[-1] is None:
                                sweeps[-1] = sweep

                            else:
                                sweeps[-1].extend(sweep)

        return end_rails

    def get_sorted_sweep_edges(self, sweep_count, edges, layer, pipe_idx):
        sweeps = [None] * sweep_count
        non_sweep_edges = set()

        for e in edges:
            edge_string = e[layer].decode()

            if edge_string:
                edge_dict = eval(edge_string)

                sweep_idx = edge_dict.get(pipe_idx)

                sweep = sweeps[sweep_idx]

                if sweep:
                    sweeps[sweep_idx].append(e)

                else:
                    sweeps[sweep_idx] = [e]

            else:
                non_sweep_edges.add(e)

        return sweeps, non_sweep_edges, True if sweeps[0] and sweeps[-1] else False


def get_selected_vert_sequences(verts, debug=False):
    sequences = []

    noncyclicstartverts = [v for v in verts if len([e for e in v.link_edges if e.select]) == 1]

    if noncyclicstartverts:
        v = noncyclicstartverts[0]

    else:
        v = verts[0]

    seq = []

    while verts:
        seq.append(v)

        verts.remove(v)
        if v in noncyclicstartverts:
            noncyclicstartverts.remove(v)

        nextv = [e.other_vert(v) for e in v.link_edges if e.select and e.other_vert(v) not in seq]

        if nextv:
            v = nextv[0]

        else:
            cyclic = True if len([e for e in v.link_edges if e.select]) == 2 else False

            sequences.append((seq, cyclic))

            if verts:
                if noncyclicstartverts:
                    v = noncyclicstartverts[0]
                else:
                    v = verts[0]

                seq = []

    if debug:
        for seq, cyclic in sequences:
            print(cyclic, [v.index for v in seq])

    return sequences


def create_circle_coords(radius, count, tilt, calc_normals=False, debug=False):
    coords = []

    rotmx = Matrix.Rotation(radians(tilt), 4, 'Z')

    for idx in range(count):
        vert_angle = idx * (2.0 * pi / count)

        x = sin(vert_angle) * radius
        y = cos(vert_angle) * radius
        coords.append(rotmx @ Vector((x, y, 0)))

        if debug:
            draw_points(coords, alpha=0.5, modal=False)

    if calc_normals:
        normals = [(co - Vector()).normalized() * 0.05 for co in coords]

        if debug:
            draw_vectors(normals, origins=coords, color=(1, 0, 0), modal=False)

        return coords, normals

    return coords


def create_rotation_matrix_from_vector(vec):
    vec.normalize()

    if vec == Vector((0, 0, 1)):
        tangent = Vector((1, 0, 0))
        binormal = Vector((0, 1, 0))

    elif vec == Vector((0, 0, -1)):
        tangent = Vector((-1, 0, 0))
        binormal = Vector((0, 1, 0))

    else:
        tangent = Vector((0, 0, 1)).cross(vec).normalized()
        binormal = tangent.cross(-vec).normalized()

    rotmx = Matrix()
    rotmx[0].xyz = tangent
    rotmx[1].xyz = binormal
    rotmx[2].xyz = vec

    return rotmx.transposed()


def get_builtin_shader_name(name, prefix='3D'):
    if bpy.app.version >= (4, 0, 0):
        return name
    else:
        return f"{prefix}_{name}"


def draw_line(coords, indices=None, mx=Matrix(), color=(1, 1, 1), alpha=1, width=1, xray=True, modal=True,
              screen=False):
    def draw():
        nonlocal indices

        if indices is None:
            indices = [(i, i + 1) for i in range(0, len(coords)) if i < len(coords) - 1]

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_points(coords, indices=None, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True,
                screen=False):
    def draw():
        shader = gpu.shader.from_builtin(get_builtin_shader_name('UNIFORM_COLOR'))
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        if indices:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]}, indices=indices)
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords}, indices=indices)

        else:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]})
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords})

        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True, screen=False):
    def draw():
        shader = gpu.shader.from_builtin(get_builtin_shader_name('UNIFORM_COLOR'))
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co]})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_vectors(vectors, origins, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, fade=False, normal=False, xray=True,
                 modal=True, screen=False):
    def draw():
        coords = []
        colors = []

        for v, o in zip(vectors, origins):
            coords.append(mx @ o)

            if normal:
                coords.append(mx @ o + get_world_space_normal(v, mx))
            else:
                coords.append(mx @ o + mx.to_3x3() @ v)

            colors.extend([(*color, alpha), (*color, alpha / 10 if fade else alpha)])

        indices = [(i, i + 1) for i in range(0, len(coords), 2)]

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": colors})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def draw_vector(vector, origin=Vector((0, 0, 0)), mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, fade=False,
                normal=False, xray=True, modal=True, screen=False):
    def draw():
        if normal:
            coords = [mx @ origin, mx @ origin + get_world_space_normal(vector, mx)]
        else:
            coords = [mx @ origin, mx @ origin + mx.to_3x3() @ vector]

        colors = ((*color, alpha), (*color, alpha / 10 if fade else alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": colors})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')


def rotate_list(list, amount):
    for i in range(abs(amount)):
        if amount > 0:
            list.append(list.pop(0))
        else:
            list.insert(0, list.pop(-1))

    return list


def average_locations(locationslist):
    avg = Vector()

    for n in locationslist:
        avg += n

    return avg / len(locationslist)


def get_loc_matrix(location):
    return Matrix.Translation(location)


def create_pipe_coords(seq, cyclic, resample, factor, smooth, iterations, optimize, angle, mx, debug=False):
    def smooth_coords(coords, cyclic, iterations, mx, debug=False):
        while iterations:
            iterations -= 1

            smoothed = []

            for idx, co in enumerate(coords):
                if idx in [0, len(coords) - 1]:
                    if cyclic:
                        if idx == 0:
                            smoothed.append(average_locations([coords[-1], coords[1]]))

                        elif idx == len(coords) - 1:
                            smoothed.append(average_locations([coords[-2], coords[0]]))
                    else:
                        smoothed.append(co)
                else:
                    co_prev = coords[idx - 1]
                    co_next = coords[idx + 1]

                    smoothed.append(average_locations([co_prev, co_next]))

            coords = smoothed

        if debug:
            red = (1, 0.25, 0.25)
            draw_points(coords, mx=mx, color=red, xray=True, modal=False)

        return coords

    def optimize_straights(coords, cyclic, angle, mx, debug=False):
        optimized = []
        removed = []

        for idx, co in enumerate(coords):
            if idx in [0, len(coords) - 1]:
                if cyclic:
                    if idx == 0:
                        co_prev = coords[-1]
                        co_next = coords[1]

                    elif idx == len(coords) - 1:
                        co_prev = coords[-2]
                        co_next = coords[0]
                else:
                    optimized.append(co)
                    continue
            else:
                co_prev = coords[idx - 1]
                co_next = coords[idx + 1]

            vec1 = co_prev - co
            vec2 = co_next - co
            a = round(degrees(vec1.angle(vec2)), 3)

            if a >= angle:
                removed.append(co)

            else:
                optimized.append(co)

        if debug:
            black = (0, 0, 0)
            draw_points(removed, mx=mx, color=black, modal=False)

        return optimized

    coords = [v.co.copy() for v in seq]

    if resample:
        coords = resample_coords(coords, cyclic, segments=int(len(coords) * factor), mx=mx, debug=False)

    if smooth:
        coords = smooth_coords(coords, cyclic, iterations, mx, debug=False)

    if optimize:
        coords = optimize_straights(coords, cyclic, angle, mx, debug=False)

    if debug:
        white = (1, 1, 1)
        draw_points(coords, mx=mx, color=white, xray=True, modal=False)

    return coords


def create_pipe_ring_coords(coords, cyclic, circle_coords, circle_normals=None, mx=None, debug=False):
    ring_coords = []

    for idx, co in enumerate(coords):
        ring = []

        prevco = coords[-1] if idx == 0 else coords[idx - 1]
        nextco = coords[0] if idx == len(coords) - 1 else coords[idx + 1]

        if cyclic or idx not in [0, len(coords) - 1]:
            vec_next = (nextco - co).normalized()
            vec_prev = (co - prevco).normalized()

            direction = vec_prev + vec_next

        else:
            if idx == 0:
                direction = (nextco - co).normalized()

            elif idx == len(coords) - 1:
                direction = (co - prevco).normalized()

        if debug and mx:
            draw_vector(direction * 0.05, origin=co, mx=mx, color=(1, 1, 1), modal=False)

        rotmx = create_rotation_matrix_from_vector(direction)

        locmx = get_loc_matrix(co)

        for cidx, cco in enumerate(circle_coords):
            if circle_normals:
                normal = circle_normals[cidx]
                ring.append((locmx @ rotmx @ cco, rotmx @ normal))

            else:
                ring.append(locmx @ rotmx @ cco)

        if debug and mx:
            if circle_normals:
                dcoords = [co for co, _ in ring]
                draw_points(dcoords[1:], mx=mx, color=(1, 1, 1), size=4, alpha=0.5, modal=False)
                draw_point(dcoords[0], mx=mx, color=(1, 0, 0), size=4, alpha=1, modal=False)

                normals = [nrm for _, nrm in ring]
                draw_vectors(normals, dcoords, mx=mx, color=(1, 0, 0), alpha=0.5, modal=False)

            else:
                draw_points(ring[1:], mx=mx, color=(1, 1, 1), size=4, alpha=0.5, modal=False)
                draw_point(ring[0], mx=mx, color=(1, 0, 0), size=4, alpha=1, modal=False)

        ring_coords.append(ring)

    return ring_coords


def resample_coords(coords, cyclic, segments=None, shift=0, mx=None, debug=False):
    if not segments:
        segments = len(coords) - 1

    if len(coords) < 2:
        return coords

    if not cyclic and shift != 0:  # not PEP but it shows that we want shift = 0
        print('Not shifting because this is not a cyclic vert chain')
        shift = 0

    arch_len = 0
    cumulative_lengths = [0]  # TODO: make this the right size and dont append

    for i in range(0, len(coords) - 1):
        v0 = coords[i]
        v1 = coords[i + 1]
        V = v1 - v0
        arch_len += V.length
        cumulative_lengths.append(arch_len)

    if cyclic:
        v0 = coords[-1]
        v1 = coords[0]
        V = v1 - v0
        arch_len += V.length
        cumulative_lengths.append(arch_len)
        segments += 1

    if cyclic:
        new_coords = [[None]] * segments
    else:
        new_coords = [[None]] * (segments + 1)
        new_coords[0] = coords[0]
        new_coords[-1] = coords[-1]

    n = 0

    for i in range(0, segments - 1 + cyclic * 1):
        desired_length_raw = (i + 1 + cyclic * -1) / segments * arch_len + shift * arch_len / segments
        if desired_length_raw > arch_len:
            desired_length = desired_length_raw - arch_len
        elif desired_length_raw < 0:
            desired_length = arch_len + desired_length_raw  # this is the end, + a negative number
        else:
            desired_length = desired_length_raw

        for j in range(n, len(coords) + 1):

            if cumulative_lengths[j] > desired_length:
                break

        extra = desired_length - cumulative_lengths[j - 1]

        if j == len(coords):
            new_coords[i + 1 + cyclic * -1] = coords[j - 1] + extra * (coords[0] - coords[j - 1]).normalized()
        else:
            new_coords[i + 1 + cyclic * -1] = coords[j - 1] + extra * (coords[j] - coords[j - 1]).normalized()

    if debug:
        print(len(coords), len(new_coords))
        print(cumulative_lengths)
        print(arch_len)

        if mx:
            green = (0.25, 1, 0.25)
            yellow = (1, 0.9, 0.2)
            draw_points(new_coords, mx=mx, color=green if cyclic else yellow, xray=True, modal=False)

    return new_coords


def select_vert(edges, layer, pipe_idx, coords, border_verts, vert_layer):
    sweeps = [None] * len(coords)

    for e in edges:
        edge_string = e[layer].decode()

        if edge_string:
            edge_dict = eval(edge_string)

            sweep_idx = edge_dict.get(pipe_idx)

            sweep = sweeps[sweep_idx]

            if sweep:
                sweeps[sweep_idx].append(e)

            else:
                sweeps[sweep_idx] = [e]

    for idx, (sweep, co) in enumerate(zip(sweeps, coords)):
        if sweep:
            sweep_verts = {v for e in sweep for v in e.verts}

            for v in sweep_verts:
                if v in border_verts:
                    v[vert_layer] = idx + 1


def pipe_cut():
    # 分离出管道
    bpy.ops.mesh.separate(type='SELECTED')

    active_obj = bpy.context.active_object

    for obj in bpy.data.objects:
        if obj.select_get() and obj != active_obj:
            pipe_obj = obj
            break

    # 清理自相交网格
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    pipe_obj.select_set(True)
    bpy.context.view_layer.objects.active = pipe_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)  # 让物体法线向内

    # 切割
    bpy.ops.object.mode_set(mode='OBJECT')
    pipe_obj.select_set(True)
    active_obj.select_set(True)
    bpy.context.view_layer.objects.active = active_obj

    # 使用布尔插件
    bpy.ops.object.booltool_auto_difference()
    bpy.ops.object.mode_set(mode='EDIT')
    active_obj.vertex_groups.new(name="CircleCutOuter")
    bpy.ops.object.vertex_group_assign()


def get_outer_and_inner_vert_group():
    main_obj = bpy.context.active_object
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()

    bm = bmesh.from_edit_mesh(main_obj.data)
    bm.verts.ensure_lookup_table()
    all_border_vert_index = [v.index for v in bm.verts if v.select]
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.verts[all_border_vert_index[0]].select = True

    bpy.ops.mesh.select_linked(delimit=set())
    part_1_index = [v.index for v in bm.verts if v.select]
    part_2_index = [v.index for v in bm.verts if not v.select]
    if len(part_1_index) > len(part_2_index):
        inner_part_set = set(part_2_index)
        outer_part_set = set(part_1_index)
    else:
        inner_part_set = set(part_1_index)
        outer_part_set = set(part_2_index)
    bpy.ops.mesh.select_all(action='DESELECT')

    for v in bm.verts:
        if v.is_boundary and v.index in inner_part_set:
            v.select_set(True)

    main_obj.vertex_groups.new(name="CircleCutInner")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_remove_from()


def delete_inner_part():
    main_obj = bpy.context.active_object
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.vertex_group_remove()


def scale_border(scale_factor, center_border_group_name, vert_layer):
    active = bpy.context.active_object
    bpy.ops.object.vertex_group_select()
    bm = bmesh.from_edit_mesh(active.data)
    outer_border = [v for v in bm.verts if v.select]
    outer_edges = set()
    extrude_direction = {}

    center = mathutils.Vector((0, 0, 0))
    for v in outer_border:
        center += v.co
    center /= len(outer_border)

    # 遍历选中的顶点
    for vert in outer_border:
        key = (vert.co[0], vert.co[1], vert.co[2])
        extrude_direction[key] = vert[vert_layer]
        for edge in vert.link_edges:
            # 检查边的两个顶点是否都在选中的顶点中
            if edge.verts[0] in outer_border and edge.verts[1] in outer_border:
                outer_edges.add(edge)
                edge.select_set(True)

    # 复制选中的顶点并沿着中心方向缩放
    bpy.ops.mesh.duplicate()

    # 获取所有选中的顶点
    inside_border_vert = [v for v in bm.verts if v.select]

    for i, vert in enumerate(inside_border_vert):
        key = (vert.co[0], vert.co[1], vert.co[2])
        vert[vert_layer] = extrude_direction[key]
        vert.co += (center - vert.co) * (1 - scale_factor)  # 沿中心方向缩放

    active.vertex_groups.new(name="CircleCutInner")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group=center_border_group_name)
    bpy.ops.object.vertex_group_remove_from()
    bpy.ops.mesh.select_all(action='DESELECT')


def bridge_ring_by_ring(v_index_layer_value_dict, border_index_set, center_border_index_set):
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()

    border_route_dict = dict()
    center_route_dict = dict()

    for layer_value_key in range(1, len(v_index_layer_value_dict)):
        # for layer_value_key in range(1,2):
        now_v_index_group = v_index_layer_value_dict.get(layer_value_key)
        next_v_index_group = v_index_layer_value_dict.get(layer_value_key + 1)

        for now_index in now_v_index_group:
            if now_index in border_index_set:
                now_up_index = now_index
            elif now_index in center_border_index_set:
                now_center_index = now_index

        for next_index in next_v_index_group:
            if next_index in border_index_set:
                next_up_index = next_index
            elif next_index in center_border_index_set:
                next_center_index = next_index

        border_route_dict[layer_value_key] = get_route_index(now_up_index, next_up_index, bm)
        center_route_dict[layer_value_key] = get_route_index(now_center_index, next_center_index, bm)

    # 处理最后一组头尾相连的面
    now_v_index_group = v_index_layer_value_dict.get(1)
    next_v_index_group = v_index_layer_value_dict.get(len(v_index_layer_value_dict))

    for now_index in now_v_index_group:
        if now_index in border_index_set:
            now_up_index = now_index
        elif now_index in center_border_index_set:
            now_center_index = now_index

    for next_index in next_v_index_group:
        if next_index in border_index_set:
            next_up_index = next_index
        elif next_index in center_border_index_set:
            next_center_index = next_index
    border_route_dict[len(v_index_layer_value_dict)] = get_route_index(now_up_index, next_up_index, bm)
    center_route_dict[len(v_index_layer_value_dict)] = get_route_index(now_center_index, next_center_index, bm)

    for layer_value_key in range(1, len(v_index_layer_value_dict) + 1):
        # for layer_value_key in range(1,2):
        bpy.ops.mesh.select_all(action='DESELECT')
        border_route = border_route_dict[layer_value_key]
        center_route = center_route_dict[layer_value_key]
        for index in border_route:
            bm.verts[index].select = True
            for e in bm.verts[index].link_edges:
                if e.other_vert(bm.verts[index]).select:
                    e.select = True
        for index in center_route:
            bm.verts[index].select = True
            for e in bm.verts[index].link_edges:
                if e.other_vert(bm.verts[index]).select:
                    e.select = True
        bpy.ops.mesh.edge_face_add()

    # 桥接完成后重新计算法线
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action='DESELECT')


def bridge_border(width, center_border_group_name):
    main_obj = bpy.context.active_object

    # 分离出桥接边
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CircleCutInner')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group=center_border_group_name)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != main_obj.name:
                bridge_border_obj = obj
    bridge_border_obj.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    bridge_border_obj.select_set(True)
    bridge_border_obj.name = main_obj.name + "BridgeBorder"
    bpy.context.view_layer.objects.active = bridge_border_obj

    # 对需要作为桥接点的顶点进行分组
    v_index_layer_value_dict = dict()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    mesh = bridge_border_obj.data
    bm = bmesh.from_edit_mesh(mesh)
    vert_layer = bm.verts.layers.int.get('OffsetCutVerts')
    for v in bm.verts:
        v_layer_value = v[vert_layer]
        if v_layer_value != 0:
            v_layer_value_set = v_index_layer_value_dict.get(v_layer_value)
            if v_layer_value_set == None:
                v_layer_value_set = set()
            v_layer_value_set.add(v.index)
            v_index_layer_value_dict[v_layer_value] = v_layer_value_set

    # 区分上下边界index
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()
    outer_border_index_set = set([v.index for v in bm.verts if v.select])
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutInner')
    bpy.ops.object.vertex_group_select()
    inner_border_index_set = set([v.index for v in bm.verts if v.select])
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=center_border_group_name)
    bpy.ops.object.vertex_group_select()
    center_border_index_set = set([v.index for v in bm.verts if v.select])
    bpy.ops.mesh.select_all(action='DESELECT')

    filter_error_data(v_index_layer_value_dict, outer_border_index_set, center_border_index_set)
    bridge_ring_by_ring(v_index_layer_value_dict, outer_border_index_set, center_border_index_set)
    bridge_ring_by_ring(v_index_layer_value_dict, inner_border_index_set, center_border_index_set)

    # 将边界合并回原物体
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    main_obj.select_set(True)
    bridge_border_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group=center_border_group_name)
    bpy.ops.object.vertex_group_select()
    # 进行倒角
    bpy.ops.mesh.bevel(offset_type='PERCENT', offset_pct=80, segments=int(width / 0.1), profile=0.4,
                       release_confirm=True)


def filter_error_data(v_index_layer_value_dict, outer_border_index_set, center_border_index_set):
    for key in range(1, len(v_index_layer_value_dict) + 1):
        layer_value_set = v_index_layer_value_dict[key]
        if len(layer_value_set) != 3:
            for item in layer_value_set:
                if item in center_border_index_set:
                    center_border_index = item
                    up_border_index = get_closest_index(center_border_index, outer_border_index_set)
                    # down_border_index = get_closest_index(center_border_index, inner_border_index_set)
                    # layer_value_set = set([up_border_index, center_border_index, down_border_index])
                    temp_set = set(layer_value_set)
                    temp_set.add(up_border_index)
                    v_index_layer_value_dict[key] = temp_set


def get_closest_index(v_index, v_index_set):
    obj = bpy.context.active_object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()

    min_distance = math.inf
    min_index = None
    for index in v_index_set:
        distance = (bm.verts[v_index].co - bm.verts[index].co).length
        if distance < min_distance:
            min_distance = distance
            min_index = index
    return min_index


def get_route_index(now_index, next_index, bm):
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.verts[now_index].select = True
    bm.verts[next_index].select = True
    # 判断是否需要选择最短路径
    short_route_flag = True
    for e in bm.verts[now_index].link_edges:
        if e.other_vert(bm.verts[now_index]).select:
            short_route_flag = False
            break
    if short_route_flag:
        bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
    return [v.index for v in bm.verts if v.select]


def resample_outer_border(resample_num):
    main_obj = bpy.context.active_object
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')

    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.select_get():
            if obj.name != main_obj.name:
                outer_border_obj = obj
    outer_border_obj.select_set(False)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_more()
    main_obj.vertex_groups.new(name="CircleCutOuterBridge")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    resample_mesh(outer_border_obj, resample_num)
    # 重新设置顶点组
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    outer_border_obj.vertex_groups.new(name="CircleCutOuter")
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.mode_set(mode='OBJECT')

    main_obj.select_set(True)
    outer_border_obj.select_set(True)
    bpy.context.view_layer.objects.active = main_obj
    bpy.ops.object.join()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuterBridge')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='CircleCutOuter')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.bridge_edge_loops()
    delete_vert_group("CircleCutOuterBridge")


def resample_mesh(obj, resample_num):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='CURVE')
    # 添加几何节点修改器
    modifier = obj.modifiers.new(name="Resample", type='NODES')
    bpy.ops.node.new_geometry_node_group_assign()

    node_tree = bpy.data.node_groups[0]
    node_links = node_tree.links

    input_node = node_tree.nodes[0]
    output_node = node_tree.nodes[1]

    resample_node = node_tree.nodes.new("GeometryNodeResampleCurve")
    resample_node.inputs[2].default_value = resample_num

    node_links.new(input_node.outputs[0], resample_node.inputs[0])
    node_links.new(resample_node.outputs[0], output_node.inputs[0])

    bpy.ops.object.convert(target='MESH')

    bpy.data.node_groups.remove(node_tree)


def fill_inner_part():
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_multi_face=False, use_non_contiguous=False,
                                     use_verts=False)
    bpy.ops.mesh.fill()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def register():
    bpy.utils.register_class(Circle_Smooth)


def unregister():
    bpy.utils.unregister_class(Circle_Smooth)
