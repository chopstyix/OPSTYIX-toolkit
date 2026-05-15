import bpy, math
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty, StringProperty


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _crop_factor(camera):
    fullframe_diagonal = 43.27
    if camera.sensor_height > camera.sensor_width:
        ratio = 2 / 3
    else:
        ratio = 3 / 2
    camera_diagonal = math.sqrt(
        math.pow(camera.sensor_width, 2) +
        math.pow(camera.sensor_width / ratio, 2)
    )
    cf = round(fullframe_diagonal / camera_diagonal, 2)
    equivalent = round(camera.lens * cf)
    return f"Crop Factor: {cf}, {equivalent} mm equivalent."


def _sensor_size(camera):
    """Return the effective sensor size respecting AUTO fit mode."""
    fit = camera.sensor_fit
    if fit == 'VERTICAL':
        return camera.sensor_height
    if fit == 'AUTO':
        scene = bpy.context.scene
        render = scene.render
        aspect = (render.resolution_x * render.pixel_aspect_x) / \
                 (render.resolution_y * render.pixel_aspect_y)
        return camera.sensor_height if aspect < 1.0 else camera.sensor_width
    return camera.sensor_width


def _focal_ratio(camera):
    """Return camera.lens / sensor_size, guarded against zero."""
    sensor = _sensor_size(camera)
    if sensor == 0 or camera.lens == 0:
        return None
    return camera.lens / sensor


# ─── Property getters / setters ───────────────────────────────────────────────

def _get_lens_shift_y(self):
    return self.id_data.shift_y


def _set_lens_shift_y(self, value):
    camera = self.id_data
    ratio = _focal_ratio(camera)
    if ratio is None:
        return

    if self.lens_shift_compensated:
        objs = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is camera]
        if objs:
            obj = objs[0]
            old_atan = math.atan(self.lens_shift / ratio)
            rot = obj.rotation_euler.to_matrix().to_euler('XYZ')
            rot.x += old_atan
            self['lens_shift'] = value
            camera.shift_y = value
            rot.x -= math.atan(value / ratio)
            obj.rotation_euler = rot.to_matrix().to_euler(obj.rotation_mode)
            return

    self['lens_shift'] = value
    camera.shift_y = value


def _get_lens_shift_x(self):
    return self.id_data.shift_x


def _set_lens_shift_x(self, value):
    camera = self.id_data
    ratio = _focal_ratio(camera)
    if ratio is None:
        return

    if self.lens_shift_compensated:
        objs = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is camera]
        if objs:
            obj = objs[0]
            old_atan = math.atan(self.lens_shift_x / ratio)
            rot = obj.rotation_euler.to_matrix().to_euler('YZX')
            rot.y -= old_atan
            self['lens_shift_x'] = value
            camera.shift_x = value
            rot.y += math.atan(value / ratio)
            obj.rotation_euler = rot.to_matrix().to_euler(obj.rotation_mode)
            return

    self['lens_shift_x'] = value
    camera.shift_x = value


def _update_ls_compensated(self, context):
    camera = self.id_data
    ratio = _focal_ratio(camera)
    if ratio is None:
        return

    objs = [o for o in bpy.data.objects
            if o.type == 'CAMERA' and o.data.original is camera.original]
    if not objs:
        return
    obj = objs[0]

    atan_v = math.atan(self.lens_shift   / ratio)
    atan_h = math.atan(self.lens_shift_x / ratio)

    # Apply vertical correction first, then re-read euler for horizontal
    # to avoid gimbal drift from sequential same-base rotations.
    rot_v = obj.rotation_euler.to_matrix().to_euler('XYZ')
    rot_v.x += atan_v if not self.lens_shift_compensated else -atan_v
    obj.rotation_euler = rot_v.to_matrix().to_euler(obj.rotation_mode)

    rot_h = obj.rotation_euler.to_matrix().to_euler('YZX')
    rot_h.y += -atan_h if not self.lens_shift_compensated else atan_h
    obj.rotation_euler = rot_h.to_matrix().to_euler(obj.rotation_mode)


# ─── Property group ───────────────────────────────────────────────────────────

class OPSTYIXLensShiftSettings(bpy.types.PropertyGroup):
    lens_shift: FloatProperty(
        name="Vertical Shift",
        description="Vertically shifts the lens while keeping the shot framed",
        default=0.0,
        soft_min=-2.0, soft_max=2.0,
        precision=3,
        options={'HIDDEN'},
        get=_get_lens_shift_y,
        set=_set_lens_shift_y,
    )
    lens_shift_x: FloatProperty(
        name="Horizontal Shift",
        description="Horizontally shifts the lens while keeping the shot framed",
        default=0.0,
        soft_min=-2.0, soft_max=2.0,
        precision=3,
        options={'HIDDEN'},
        get=_get_lens_shift_x,
        set=_set_lens_shift_x,
    )
    lens_shift_compensated: BoolProperty(
        name="Maintain Framing",
        description=(
            "Automatically rotates the camera to keep the shot framed when "
            "shifting. Disabling reverts to default Blender behavior"
        ),
        default=True,
        options={'HIDDEN'},
        update=_update_ls_compensated,
    )


# ─── Operators ────────────────────────────────────────────────────────────────

class OPSTYIX_OT_AutoLensShift(Operator):
    bl_idname      = "opstyix.auto_lens_shift"
    bl_label       = "Auto-calculate from Camera Tilt"
    bl_description = (
        "Calculates the Lens Shift needed from the current camera tilt "
        "to make vertical lines parallel"
    )
    bl_options = {'REGISTER', 'UNDO'}

    camera: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.camera)
        if obj is None or obj.type != 'CAMERA':
            return {'CANCELLED'}

        camera = obj.data
        settings = camera.opstyix_lens_shift
        ratio = _focal_ratio(camera)
        if ratio is None:
            self.report({'ERROR'}, "Invalid camera lens or sensor size.")
            return {'CANCELLED'}

        old_atan = math.atan(settings.lens_shift / ratio)
        rot = obj.rotation_euler.x + old_atan

        if rot == 0:
            self.report({'ERROR'},
                "Cannot calculate Lens Shift — camera has no vertical rotation.")
            return {'CANCELLED'}

        shift = -ratio / math.tan(rot)
        if shift > 20 or shift < -20:
            self.report({'ERROR'},
                "Camera vertical rotation is too extreme — reduce angle and try again.")
            return {'CANCELLED'}

        settings.lens_shift = shift
        obj.rotation_euler.x = math.radians(-90 if rot < 0 else 90)

        if 359.2 > round(math.degrees(obj.rotation_euler.y) % 360) > 0.2:
            self.report({'WARNING'},
                "Camera has Y rotation — vertical lines will be parallel but not straight.")

        return {'FINISHED'}


class OPSTYIX_OT_ResetLensShift(Operator):
    bl_idname      = "opstyix.reset_lens_shift"
    bl_label       = "Reset Shift"
    bl_description = "Reset both Vertical and Horizontal Shift to zero and reverse any rotation compensation"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        camera = context.camera
        if camera is None:
            return {'CANCELLED'}
        settings = camera.opstyix_lens_shift
        settings.lens_shift   = 0.0
        settings.lens_shift_x = 0.0
        return {'FINISHED'}


# ─── Camera Properties UI injection ───────────────────────────────────────────

def _lens_shift_ui(self, context):
    if context.camera is None:
        return
    camera = context.camera
    settings = camera.opstyix_lens_shift
    cam_name = getattr(context.view_layer.objects.active, 'name', '')

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    split = layout.split(factor=0.4)
    split.separator()
    row = split.row(align=True)
    row.operator('opstyix.auto_lens_shift',  icon='EVENT_A').camera = cam_name
    row.operator('opstyix.reset_lens_shift', icon='LOOP_BACK', text='Reset')

    layout.prop(settings, 'lens_shift_compensated')

    row = layout.row()
    row.alignment = 'RIGHT'
    row.label(text=_crop_factor(camera))


# ─── Register / Unregister ────────────────────────────────────────────────────

_classes = [
    OPSTYIXLensShiftSettings,
    OPSTYIX_OT_AutoLensShift,
    OPSTYIX_OT_ResetLensShift,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Camera.opstyix_lens_shift = bpy.props.PointerProperty(
        type=OPSTYIXLensShiftSettings
    )
    bpy.types.DATA_PT_lens.append(_lens_shift_ui)


def unregister():
    bpy.types.DATA_PT_lens.remove(_lens_shift_ui)
    del bpy.types.Camera.opstyix_lens_shift
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
