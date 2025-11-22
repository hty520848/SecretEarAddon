import bpy
import bmesh
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from math import sqrt   

class BooleanCleanup(bpy.types.Operator):
    bl_idname = "huier.boolean_cleanup"
    bl_label = "HUIER: Boolean Cleanup"
    bl_description = "Merge verts on cyclic selections resulting from Boolean operations"
    bl_options = {'REGISTER', 'UNDO'}

    side_selection_items = [("A", "A", ""),
                            ("B", "B", "")]

    sideselection: EnumProperty(name="Side", items=side_selection_items, default="A")
    flip: BoolProperty(name="Flip Red to Green", default=False)
    threshold: FloatProperty(name="Threshold", default=0, min=0, step=0.1)
    triangulate: BoolProperty(name="Triangulate", default=False)
    allowmodalthreashold: BoolProperty(default=True)
    sharp: BoolProperty(default=False)
    debuginit: BoolProperty(default=True)
    passthrough: BoolProperty(default=False)

    
    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(self, "sideselection", expand=True)

        column.prop(self, "threshold")

        row = column.row(align=True)

        row.prop(self, "triangulate", toggle=True)

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            mode = tuple(context.tool_settings.mesh_select_mode)

            if mode == (True, False, False) or mode == (False, True, False):
                return len([v for v in bm.verts if v.select]) >= 1

    def execute(self, context):
        active = context.active_object

        try:
            self.main(active)
        except Exception as e:
            output_traceback(self, e)

        return {'FINISHED'}

    def main(self, active, modal=False):
        debug = False

        mesh = active.data

        bpy.ops.object.mode_set(mode='OBJECT')

        if modal:
            self.initbm.to_mesh(active.data)

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        verts = [v for v in bm.verts if v.select]
        edges = [e for e in bm.edges if e.select]

        if any([not e.smooth for e in edges]):
            self.sharp = True

        sideA, sideB, cyclic, err = get_sides(bm, verts, edges, debug=debug)

        if sideA and sideB:
            self.tag_fixed_verts(sideA, sideB)

            if not cyclic:
                sideA[0]["vert"].tag = True
                sideA[-1]["vert"].tag = True

            mg = build_edge_graph(verts, edges, debug=debug)

            self.fixed_verts, self.unmoved_verts = self.move_merts(bm, mg, cyclic, debug=debug)

            if self.triangulate:
                self.triangulate_side(bm, sideA, sideB)

            bmesh.ops.remove_doubles(bm, verts=verts, dist=0.00001)

            if self.triangulate and self.sharp:
                for e in bm.edges:
                    if e.select:
                        e.smooth = False

            bm.to_mesh(mesh)
            bpy.ops.object.mode_set(mode='EDIT')

            return True

        else:
            popup_message(err[0], title=err[1])
            bpy.ops.object.mode_set(mode='EDIT')

            return False

    def triangulate_side(self, bm, sideA, sideB):
        faces = []
        if self.sideselection == "A":
            for sB in sideB:
                for f in sB["faces"]:
                    if f not in faces:
                        faces.append(f)
        else:
            for sA in sideA:
                for f in sA["faces"]:
                    if f not in faces:
                        faces.append(f)

        bmesh.ops.triangulate(bm, faces=faces)

    def move_merts(self, bm, mg, cyclic, debug=False):
        fixed_vert_coords = []
        unmoved_vert_coords = []

        if debug:
            print("cylclic selection:", cyclic)

        for eidx, vidx in enumerate(mg):
            if debug:
                print("vert:", vidx)

            fixed = mg[vidx]["fixed"]
            if debug:
                print(" • fixed:", fixed)

            if fixed:
                fixed_vert_coords.append(bm.verts[vidx].co.copy())
                continue

            else:
                A = mg[vidx]["connected"][0]
                B = mg[vidx]["connected"][1]

                Aidx, Afixed, Adist = A
                Bidx, Bfixed, Bdist = B

                lsort = [A, B]
                lsort = sorted(lsort, key=lambda l: l[2])
                closest = lsort[0]
                furthest = lsort[1]

                if closest[2] <= self.threshold:
                    closestidx = closest[0]
                    closestdist = closest[2]

                    furthestidx = furthest[0]

                    bm.verts[vidx].co = bm.verts[closestidx].co
                    if debug:
                        print(" • moved to vert %d - distance: %f" % (closestidx, closestdist))

                    for childidx in mg[vidx]["children"]:
                        bm.verts[childidx].co = bm.verts[closestidx].co
                        if debug:
                            print("  • moved the child vert %d as well" % (childidx))

                    mg[closestidx]["children"].append(vidx)
                    if debug:
                        print(" • updated %d's mg 'children' entry with vert %d" % (closestidx, vidx))

                    for childidx in mg[vidx]["children"]:
                        mg[closestidx]["children"].append(childidx)

                        if debug:
                            print("  • updated %d's mg 'children' entry with vert %d" % (closestidx, childidx))

                    closest_conected = mg[closestidx]["connected"]
                    furthest_connected = mg[furthestidx]["connected"]

                    newdist = get_distance_between_verts(bm.verts[closestidx], bm.verts[furthestidx])

                    for i, con in enumerate(closest_conected):
                        if con[0] == vidx:
                            mg[closestidx]["connected"][i] = (furthestidx, furthest[1], newdist)

                    if debug:
                        print(" • updated %d's mg 'connected' entry with vert %d replacing vert %d" % (closestidx, furthestidx, vidx))

                    for i, con in enumerate(furthest_connected):
                        if con[0] == vidx:
                            mg[furthestidx]["connected"][i] = (closestidx, closest[1], newdist)

                    if debug:
                        print(" • updated %d's mg 'connected' entry with vert %d replacing vert %d" % (furthestidx, closestidx, vidx))

                else:
                    unmoved_vert_coords.append(bm.verts[vidx].co.copy())

        return fixed_vert_coords, unmoved_vert_coords

    def tag_fixed_verts(self, sideA, sideB):
        if self.sideselection == "A":
            for sA in sideA:
                if sA["edges"]:

                    sA["vert"].tag = True
        else:
            for sB in sideB:
                if sB["edges"]:

                    sB["vert"].tag = True

def output_traceback(self, e):
    import traceback
    print()
    traceback.print_exc()
    self.report({'ERROR'}, str(e))

def get_sides(bm, verts, edges, debug=False):
    if any([not e.is_manifold for e in edges]):
        errmsg = "Non-manifold edges are part of the selection. Failed to determine sides of the selection."
        errtitle = "Non-Manifold Geometry"
        return None, None, None, (errmsg, errtitle)

    bm.select_flush(True)
    flushedges = [e for e in bm.edges if e.select and e not in edges]

    for e in flushedges:
        e.select = False

    bm.select_flush(False)

    ends = []
    for v in verts:
        if sum([e.select for e in v.link_edges]) == 1:
            ends.append(v)

    endslen = len(ends)

    cyclic = False

    if endslen == 0:
        if debug:
            print("Cyclic edge loop selection")

        cyclic = True

        loops = [l for l in verts[0].link_loops if l.edge in edges]

        sideA = get_side(verts, edges, verts[0], loops[0], flushedges=flushedges, debug=debug)
        sideB = get_side(verts, edges, verts[0], loops[1], flushedges=flushedges, reverse=True, offset=1, debug=debug)

        if sideA and sideB:
            return sideA, sideB, cyclic, None
        else:
            errmsg = "There's a non-manifold edge closeby, failed to determine sides of the selection."
            errtitle = "Non-Manifold Geometry"

            return None, None, None, (errmsg, errtitle)

    elif endslen == 2:
        if debug:
            print("Non-Cyclic edge loop selection")

        loops = [l for v in ends for l in v.link_loops if l.edge in edges]

        sideA = get_side(verts, edges, ends[0], loops[0], endvert=ends[1], flushedges=flushedges, debug=debug)
        sideB = get_side(verts, edges, ends[1], loops[1], endvert=ends[0], flushedges=flushedges, reverse=True, debug=debug)

        if sideA and sideB:
            return sideA, sideB, cyclic, None
        else:
            errmsg = "There's a non-manifold edge closeby, failed to determine sides of the selection."
            errtitle = "Non-Manifold Geometry"

            return None, None, None, (errmsg, errtitle)

    else:
        if debug:
            print("Invalid selection.")

        errmsg = "Only single-island cyclic or non-cyclic edge loop selections are supproted."
        errtitle = "Illegal Selection"

        return None, None, None, (errmsg, errtitle)
    
def get_side(verts, edges, startvert, startloop, endvert=None, flushedges=[], reverse=False, offset=None, debug=False):
    vert = startvert
    loop = startloop

    edges_travelled = [loop.edge]

    startedge = []
    if endvert:
        if startloop.link_loop_prev.edge not in edges:
            startedge.append(startloop.link_loop_prev.edge)

    d = {"vert": vert, "seledge": loop.edge, "edges": startedge, "faces": [loop.face]}
    side = [d]

    while True:
        if vert == endvert:
            d["seledge"] = edges_travelled[-1]
            break

        loop = loop.link_loop_next

        vert = loop.vert
        edge = loop.edge
        face = loop.face

        if not edge.is_manifold:
            return

        if edge in edges_travelled:
            break

        if vert in verts:
            if vert in [s["vert"] for s in side]:
                append = False
                d = [s for s in side if s["vert"] == vert][0]

            else:
                append = True
                d = {}
                d["vert"] = vert
                d["edges"] = []
                d["faces"] = []

            if edge in edges:
                edges_travelled.append(edge)
                d["seledge"] = edge
            else:
                d["edges"].append(edge)

            d["faces"].append(face)

            if append:
                side.append(d)

            if edge in flushedges:
                loop = loop.link_loop_radial_next

        else:
            loop = loop.link_loop_prev.link_loop_radial_next

    if reverse:
        side.reverse()

    if offset:
        side = side[-offset:] + side[:-offset]

    if debug:
        print()
        for d in side:
            print("vert:", d["vert"].index)
            print(" • seledge", d["seledge"].index)
            print(" • edges:", [e.index for e in d["edges"]])
            print(" • faces:", [f.index for f in d["faces"]])

    return side

def build_edge_graph(verts, edges, debug=False):
    mg = {}
    for v in verts:
        mg[v.index] = {"fixed": v.tag,
                       "connected": [],
                       "children": []}

    for e in edges:
        v1 = e.verts[0]
        v2 = e.verts[1]

        mg[v1.index]["connected"].append((v2.index, v2.tag, e.calc_length()))
        mg[v2.index]["connected"].append((v1.index, v1.tag, e.calc_length()))

    if debug:
        for idx in mg:
            print(idx, mg[idx])

    return mg

def popup_message(message, title="Info", icon="INFO", terminal=True):
    def draw_message(self, context):
        if isinstance(message, list):
            for m in message:
                self.layout.label(text=m)
        else:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw_message, title=title, icon=icon)

    if terminal:
        if icon == "FILE_TICK":
            icon = "ENABLE"
        elif icon == "CANCEL":
            icon = "DISABLE"
        print(icon, title)
        print(" • ", message)

def get_distance_between_verts(vert1, vert2, getvectorlength=True):
    if getvectorlength:
        vector = vert1.co - vert2.co
        return vector.length
    else:
        return get_distance_between_points(vert1.co, vert2.co)
    
def get_distance_between_points(point1, point2):
    return sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2 + (point1[2] - point2[2]) ** 2)

def register():
    bpy.utils.register_class(BooleanCleanup)

def unregister():
    bpy.utils.unregister_class(BooleanCleanup)
