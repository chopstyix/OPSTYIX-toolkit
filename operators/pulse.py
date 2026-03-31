"""
Blender Script: Pulse Keyframe Tool — Graph Editor Panel
=========================================================
Beat-driven pulse keyframes with a per-beat pattern grid.

PULSE MODES
  Standard  — each event is a self-contained 0 → peak → 0 shape.
  Additive  — each event adds peak_value on top of the previous one.
              The curve steps upward like a staircase:
                event 1:  0 → 1
                event 2:  1 → 2
                event 3:  2 → 3  …and so on.
              The Lead and Event durations control the ramp up and
              the fall back to the new accumulated base respectively.
              e.g. with a fall: 0→1 (hold briefly) →0, then 1→2→1, then 2→3→2

HOW TO USE:
  1. Scripting workspace → Run Script.
  2. Graph Editor → select an F-Curve channel.
  3. N-panel → "Pulse" tab → adjust → Insert or Overwrite.
"""

import os
import bpy
import bpy.utils.previews
import math
import random
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (IntProperty, FloatProperty,
                        EnumProperty, BoolVectorProperty, BoolProperty)

MAX_BAR_LENGTH = 8


# ─── Helpers ──────────────────────────────────────────────────────────────────

def scene_fps(context):
    r = context.scene.render
    return r.fps / r.fps_base

def beat_to_frame(beat_index_0, bpm, fps):
    return round(beat_index_0 * fps * 60.0 / bpm)

def frames_to_beats(frames, bpm, fps):
    if bpm <= 0 or fps <= 0:
        return 0.0
    return frames / (fps * 60.0 / bpm)

def _get_all_fcurves(action):
    if hasattr(action, "fcurves"):
        try:
            yield from action.fcurves
            return
        except Exception:
            pass
    if hasattr(action, "layers"):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for cb in strip.channelbags:
                        if hasattr(cb, "fcurves"):
                            yield from cb.fcurves

def _get_active_fcurve(context):
    fc = getattr(context, "active_editable_fcurve", None)
    if fc is not None:
        return fc
    obj = context.active_object
    if obj is None or obj.animation_data is None:
        return None
    action = obj.animation_data.action
    if action is None:
        return None
    for curve in _get_all_fcurves(action):
        if curve.select:
            return curve
    return None

def _get_selected_fcurves(context):
    obj = context.active_object
    if obj is None or obj.animation_data is None:
        return []
    action = obj.animation_data.action
    if action is None:
        return []
    return [fc for fc in _get_all_fcurves(action) if fc.select]



# Known data_path fragments that store values in radians
_ANGLE_PATH_HINTS = (
    "rotation_euler", "rotation_axis_angle", "rotation_quaternion",
    "angle", "twist_start", "twist_end", "bevel_factor",
)

def _fcurve_is_angle(fc):
    """Return True if the F-Curve likely stores values in radians."""
    dp = fc.data_path.lower()
    return any(hint in dp for hint in _ANGLE_PATH_HINTS)


EASING_AWARE = {'SINE', 'QUAD', 'CUBIC', 'QUART', 'QUINT',
                'EXPO', 'CIRC', 'BACK', 'BOUNCE', 'ELASTIC'}

INTERP_ITEMS = [
    ('LINEAR',   'Linear',   'Constant rate of change'),
    ('BEZIER',   'Bezier',   'Smooth with Bezier handles'),
    ('CONSTANT', 'Constant', 'Instant step — no interpolation'),
    ('SINE',     'Sine',     'Sinusoidal easing'),
    ('QUAD',     'Quad',     'Quadratic easing'),
    ('CUBIC',    'Cubic',    'Cubic easing'),
    ('QUART',    'Quart',    'Quartic easing'),
    ('QUINT',    'Quint',    'Quintic easing'),
    ('EXPO',     'Expo',     'Exponential easing'),
    ('CIRC',     'Circ',     'Circular easing'),
    ('BACK',     'Back',     'Overshoot past the target'),
    ('BOUNCE',   'Bounce',   'Bounce at the target'),
    ('ELASTIC',  'Elastic',  'Elastic spring effect'),
]

EASING_ITEMS = [
    ('AUTO',        'Auto',     'Automatic easing'),
    ('EASE_IN',     'In',       'Accelerate into the keyframe'),
    ('EASE_OUT',    'Out',      'Decelerate out of the keyframe'),
    ('EASE_IN_OUT', 'In / Out', 'Accelerate in, decelerate out'),
]

def apply_kp(kp, interp, easing):
    kp.interpolation = interp
    if interp in EASING_AWARE:
        kp.easing = easing


# ─── Property Group ───────────────────────────────────────────────────────────

class PulseKeyframeProperties(PropertyGroup):

    bpm: FloatProperty(
        name="BPM", description="Beats per minute of your track",
        default=120.0, min=1.0, max=999.0, precision=0,
    )
    frame_offset: IntProperty(
        name="Frame Offset",
        description="Offset all pulse keyframes by this many frames",
        default=0, min=0, soft_max=99999, subtype='TIME',
    )
    bar_length: IntProperty(
        name="Bar Length",
        description="Number of beats per bar / pattern cycle",
        default=4, min=1, max=MAX_BAR_LENGTH,
    )
    beat_pattern: BoolVectorProperty(
        name="Beat Pattern",
        description="Toggle which beats within the bar fire a pulse",
        size=MAX_BAR_LENGTH,
        default=(True,) + (False,) * (MAX_BAR_LENGTH - 1),  # 8 slots
    )
    num_bars: IntProperty(
        name="Bars",
        description="How many bars to repeat the pattern across",
        default=4, min=1, soft_max=64,
    )

    # ── Mode ──────────────────────────────────────────────────────────────────
    additive: BoolProperty(
        name="Additive",
        description=(
            "Additive mode: each event adds the peak value on top of the "
            "previous one, creating a rising staircase.\n\n"
            "Standard:  0 → peak → 0  (every event resets)\n"
            "Additive:  0 → V  →  V → 2V  →  2V → 3V  …"
        ),
        default=False,
    )

    # ── Shape ─────────────────────────────────────────────────────────────────
    peak_value: FloatProperty(
        name="Peak Value",
        description=(
            "Standard: the value the curve reaches at the peak of each pulse.\n"
            "Additive: the amount added to the accumulated base per event."
        ),
        default=1.0,
        soft_min=-10.0, soft_max=10.0,
        precision=3,
    )
    lead_frames: IntProperty(
        name="Lead",
        description="Frames for the ramp up to the peak (0 = no lead-in keyframe)",
        default=1, min=0, soft_max=500, subtype='TIME',
    )
    event_frames: IntProperty(
        name="Event",
        description=(
            "Standard: frames for the fall back to 0 after the peak.\n"
            "Additive: frames for the fall back to the accumulated base "
            "after the peak (set to 0 to skip the fall entirely)."
        ),
        default=12, min=0, soft_max=500, subtype='TIME',
    )

    # ── Curves ────────────────────────────────────────────────────────────────
    lead_interp: EnumProperty(
        name="Type",
        description="Interpolation for the lead-in ramp",
        items=INTERP_ITEMS, default='LINEAR',
    )
    lead_easing: EnumProperty(
        name="Easing",
        description="Easing direction for the lead-in",
        items=EASING_ITEMS, default='EASE_IN',
    )
    fade_interp: EnumProperty(
        name="Type",
        description="Interpolation for the fade-out",
        items=INTERP_ITEMS, default='LINEAR',
    )
    fade_easing: EnumProperty(
        name="Easing",
        description="Easing direction for the fade-out",
        items=EASING_ITEMS, default='EASE_OUT',
    )
    use_degrees: BoolProperty(
        name="Input in Degrees",
        description=(
            "Treat Peak Value as degrees and convert to radians before "
            "inserting. Enable this when animating a rotation or any "
            "property whose F-Curve stores values in radians."
        ),
        default=False,
    )

    # ── Randomization ─────────────────────────────────────────────────────────
    use_random: BoolProperty(
        name="Randomize",
        description="Apply a random variation to the peak value of each event",
        default=False,
    )
    rand_mode: EnumProperty(
        name="Mode",
        description=(
            "Offset: adds a random amount within [Min, Max] on top of Peak Value.\n"
            "Replace: ignores Peak Value and picks a random value within [Min, Max]."
        ),
        items=[
            ('OFFSET',  'Offset',  'Peak Value ± random amount within [Min, Max]'),
            ('REPLACE', 'Replace', 'Peak value replaced by a random value within [Min, Max]'),
        ],
        default='OFFSET',
    )
    rand_min: FloatProperty(
        name="Min",
        description="Lower bound of the random range",
        default=-0.2,
        soft_min=-10.0, soft_max=10.0,
        precision=3,
    )
    rand_max: FloatProperty(
        name="Max",
        description="Upper bound of the random range",
        default=0.2,
        soft_min=-10.0, soft_max=10.0,
        precision=3,
    )
    rand_seed: IntProperty(
        name="Seed",
        description=(
            "Random seed — same seed always produces the same variation pattern. "
            "Change this to get a different random result."
        ),
        default=0,
        min=0,
        max=99999,
    )
    rand_allow_negative: BoolProperty(
        name="Allow Negative Peak",
        description=(
            "Randomly flip the sign of each peak value. Each event has a 50/50 "
            "chance of being positive or negative. Works alongside Offset and "
            "Replace modes, and respects the Input in Degrees conversion."
        ),
        default=False,
    )
    rand_per_channel: BoolProperty(
        name="Unique Per Channel",
        description=(
            "Give each selected channel its own random variation. "
            "Disable to apply the same random pattern to every channel."
        ),
        default=True,
    )


# ─── Shared logic ─────────────────────────────────────────────────────────────

def get_active_beat_indices(props):
    return [i for i in range(props.bar_length) if props.beat_pattern[i]]


def get_pulse_events(props, fps, rng=None):
    """
    Return a list of dicts, one per pulse event, containing:
      peak_frame, lead_frame, end_frame,
      lead_value, peak_value, end_value
    rng: optional random.Random instance for reproducible randomization.
    """
    active = get_active_beat_indices(props)
    bpm    = props.bpm
    pv     = (props.peak_value * math.pi / 180.0
              if props.use_degrees else props.peak_value)
    events = []
    pulse_index = 0

    for bar in range(props.num_bars):
        bar_start = bar * props.bar_length
        for beat_offset in active:
            global_beat = bar_start + beat_offset
            peak_frame  = beat_to_frame(global_beat, bpm, fps) + props.frame_offset

            # ── Resolve peak value (with optional randomization) ──────────────
            if rng is not None and props.use_random:
                # Step 1: compute base value from mode
                r_val = rng.uniform(props.rand_min, props.rand_max)
                # rand_min/max are in degrees when use_degrees is on;
                # convert to radians so r_val matches pv's unit
                if props.use_degrees:
                    r_val = r_val * math.pi / 180.0
                if props.rand_mode == 'OFFSET':
                    event_pv = pv + r_val
                else:  # REPLACE — r_val IS the peak, already unit-correct
                    event_pv = r_val
                # Step 2: randomly flip sign (50/50) if allowed
                if props.rand_allow_negative:
                    event_pv = abs(event_pv) * (-1 if rng.random() < 0.5 else 1)
            else:
                event_pv = pv

            if props.additive:
                base        = pulse_index * pv   # base always uses unrandomised step
                peak_val    = base + event_pv
                lead_val    = base
                end_val     = base
            else:
                lead_val    = 0.0
                peak_val    = event_pv
                end_val     = 0.0

            events.append({
                "peak_frame":  peak_frame,
                "lead_frame":  peak_frame - props.lead_frames,
                "end_frame":   peak_frame + props.event_frames,
                "lead_value":  lead_val,
                "peak_value":  peak_val,
                "end_value":   end_val,
                "bar":         bar + 1,
                "beat":        beat_offset + 1,
            })
            pulse_index += 1

    return events


def clear_fcurve_keyframes(fc):
    kps = fc.keyframe_points
    for i in range(len(kps) - 1, -1, -1):
        kps.remove(kps[i])


def do_insert(fc, props, fps, seed=None):
    rng   = random.Random(seed if seed is not None else props.rand_seed) if props.use_random else None
    total = 0
    for ev in get_pulse_events(props, fps, rng=rng):
        if props.additive:
            # Additive: single peak keyframe only.
            # Lead interp/easing drives the curve shape into this keyframe.
            kp = fc.keyframe_points.insert(
                ev["peak_frame"], ev["peak_value"], options={'FAST'})
            apply_kp(kp, props.lead_interp, props.lead_easing)
            total += 1
        else:
            if props.lead_frames > 0:
                kp = fc.keyframe_points.insert(
                    ev["lead_frame"], ev["lead_value"], options={'FAST'})
                apply_kp(kp, props.lead_interp, props.lead_easing)
                total += 1

            kp = fc.keyframe_points.insert(
                ev["peak_frame"], ev["peak_value"], options={'FAST'})
            apply_kp(kp, props.fade_interp, props.fade_easing)
            total += 1

            if props.event_frames > 0:
                kp = fc.keyframe_points.insert(
                    ev["end_frame"], ev["end_value"], options={'FAST'})
                apply_kp(kp, props.fade_interp, props.fade_easing)
                total += 1

    fc.keyframe_points.sort()
    fc.update()
    return total


def common_poll(cls, context):
    return (
        context.space_data is not None
        and context.space_data.type == 'GRAPH_EDITOR'
        and _get_active_fcurve(context) is not None
    )

def common_validate(operator, props, fc):
    if fc is None:
        operator.report({'ERROR'}, "No active F-Curve. Select a channel first.")
        return False
    if not get_active_beat_indices(props):
        operator.report({'ERROR'}, "No beats active in the pattern.")
        return False
    return True


# ─── Operators ────────────────────────────────────────────────────────────────

class GRAPH_OT_insert_pulse_keyframes(Operator):
    bl_idname      = "graph.insert_pulse_keyframes"
    bl_label       = "Insert"
    bl_description = "Add pulse keyframes on top of any existing keyframes"
    bl_options     = {'REGISTER', 'UNDO'}
    poll           = classmethod(common_poll)

    def execute(self, context):
        props   = context.scene.pulse_keyframe_props
        curves  = _get_selected_fcurves(context)
        if not common_validate(self, props, _get_active_fcurve(context)):
            return {'CANCELLED'}
        fps     = scene_fps(context)
        total   = 0
        for i, fc in enumerate(curves):
            seed = (props.rand_seed + i) if (props.use_random and props.rand_per_channel) else None
            total += do_insert(fc, props, fps, seed=seed)
        self.report({'INFO'}, f"Inserted {total} keyframes across {len(curves)} channel(s).")
        return {'FINISHED'}


class GRAPH_OT_overwrite_pulse_keyframes(Operator):
    bl_idname      = "graph.overwrite_pulse_keyframes"
    bl_label       = "Overwrite"
    bl_description = "Clear ALL existing keyframes then insert the pulse pattern fresh"
    bl_options     = {'REGISTER', 'UNDO'}
    poll           = classmethod(common_poll)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        props   = context.scene.pulse_keyframe_props
        curves  = _get_selected_fcurves(context)
        if not common_validate(self, props, _get_active_fcurve(context)):
            return {'CANCELLED'}
        fps     = scene_fps(context)
        cleared = 0
        total   = 0
        if props.use_random:
            props.rand_seed = random.randint(0, 99999)
        for i, fc in enumerate(curves):
            cleared += len(fc.keyframe_points)
            clear_fcurve_keyframes(fc)
            seed = (props.rand_seed + i) if props.rand_per_channel else None
            total += do_insert(fc, props, fps, seed=seed)
        self.report({'INFO'},
            f"Cleared {cleared}, inserted {total} keyframes across {len(curves)} channel(s).")
        return {'FINISHED'}



# ─── Panel ────────────────────────────────────────────────────────────────────

class GRAPH_PT_pulse_keyframes(Panel):
    bl_label       = "OPSTYIX Pulse"
    bl_space_type  = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category    = "OPSTYIX"

    def draw_header(self, context):
        self.layout.label(icon_value=custom_icons["opstyix_icon"].icon_id)

    def draw(self, context):
        layout = self.layout
        props  = context.scene.pulse_keyframe_props
        fc     = _get_active_fcurve(context)
        fps    = scene_fps(context)
        bpm    = props.bpm
        fpb    = fps * 60.0 / bpm
        active = get_active_beat_indices(props)


        # ── TEMPO ─────────────────────────────────────────────────────────────
        header, body = layout.panel("pulse_tempo", default_closed=False)
        header.label(text="Tempo", icon='TIME')
        if body:
            row = body.row(align=True)
            row.prop(props, "bpm")
            row.prop(props, "frame_offset")
            info = body.row()
            info.enabled = False
            info.label(
                text=f"1 beat = {fpb:.2f} fr  ·  bar 1 beat 1 → frame {props.frame_offset}",
                icon='INFO',
            )

        # ── PATTERN ───────────────────────────────────────────────────────────
        header, body = layout.panel("pulse_pattern", default_closed=False)
        header.label(text="Pattern", icon='SEQ_SEQUENCER')
        if body:
            row = body.row(align=True)
            row.prop(props, "bar_length")
            row.prop(props, "num_bars")
            body.separator(factor=0.5)

            n    = props.bar_length
            cols = min(n, 8)
            grid = body.grid_flow(
                row_major=True, columns=cols,
                even_columns=True, even_rows=True, align=True,
            )
            for i in range(n):
                grid.prop(props, "beat_pattern", index=i,
                          text=str(i + 1), toggle=True)

            body.separator(factor=0.5)
            info = body.row()
            info.enabled = False
            info.label(
                text=f"{len(active)} beat(s) × {props.num_bars} bar(s) "
                     f"= {len(active) * props.num_bars} pulse(s)"
            )

        # ── PEAK ──────────────────────────────────────────────────────────────
        # Mode, peak value, and degrees — all about what value gets written
        header, body = layout.panel("pulse_peak", default_closed=False)
        header.label(text="Peak", icon='KEYFRAME_HLT')
        if body:
            # Standard / Additive toggle
            body.prop(props, "additive", toggle=True,
                      text="Additive" if props.additive else "Standard",
                      icon='PLUS' if props.additive else 'KEYFRAME')

            if props.additive:
                hint = body.row()
                hint.enabled = False
                pv = props.peak_value
                hint.label(
                    text=f"0→{pv:.3g}  {pv:.3g}→{pv*2:.3g}  {pv*2:.3g}→{pv*3:.3g} …",
                    icon='INFO',
                )

            body.separator(factor=0.5)

            # Peak value + degrees toggle inline on the same row
            peak_row = body.row(align=True)
            peak_row.prop(props, "peak_value",
                          text="Step" if props.additive else "Peak")
            peak_row.prop(props, "use_degrees", text="°", toggle=True,
                          icon='DRIVER_ROTATIONAL_DIFFERENCE')

            if props.use_degrees:
                conv = body.row()
                conv.enabled = False
                conv.label(
                    text=f"{props.peak_value:.4g}° = {props.peak_value * math.pi / 180.0:.6f} rad",
                    icon='INFO',
                )
            elif fc is not None and _fcurve_is_angle(fc):
                warn = body.row()
                warn.alert = True
                warn.label(text="Rotation curve detected — enable °?", icon='ERROR')

        # ── ENVELOPE ─────────────────────────────────────────────────────────
        # In standard mode: Lead and Fade each show their duration AND
        # curve shape side-by-side so related controls stay together.
        # In additive mode: only the single peak keyframe curve is shown.
        header, body = layout.panel("pulse_envelope", default_closed=False)
        header.label(
            text="Curve" if props.additive else "Envelope",
            icon='SMOOTHCURVE' if props.additive else 'IPO_EASE_IN_OUT',
        )
        if body:
            if props.additive:
                # Single curve setting for the staircase peak keyframes
                body.prop(props, "lead_interp", text="")
                erow = body.row(align=True)
                erow.prop(props, "lead_easing", expand=True)
                erow.enabled = props.lead_interp in EASING_AWARE
            else:
                # Lead row: duration left, interp+easing right
                body.label(text="Lead  (0 → peak)", icon='TRIA_UP')
                row = body.row(align=True)
                self._dur_col(row, props, "lead_frames",
                              props.lead_frames, bpm, fps)
                row.separator(factor=1.5)
                rc = row.column(align=True)
                rc.prop(props, "lead_interp", text="")
                er = rc.row(align=True)
                er.prop(props, "lead_easing", expand=True)
                er.enabled = props.lead_interp in EASING_AWARE

                body.separator(factor=1.0)

                # Fade row: duration left, interp+easing right
                body.label(text="Fade  (peak → 0)", icon='TRIA_DOWN')
                row2 = body.row(align=True)
                self._dur_col(row2, props, "event_frames",
                              props.event_frames, bpm, fps)
                row2.separator(factor=1.5)
                rc2 = row2.column(align=True)
                rc2.prop(props, "fade_interp", text="")
                er2 = rc2.row(align=True)
                er2.prop(props, "fade_easing", expand=True)
                er2.enabled = props.fade_interp in EASING_AWARE

        # ── RANDOMIZE ─────────────────────────────────────────────────────────
        header, body = layout.panel("pulse_random", default_closed=True)
        header.prop(props, "use_random", text="")
        header.label(text="Randomize", icon='FORCE_TURBULENCE')
        if body and props.use_random:

            # Mode: how the random value is applied
            body.prop(props, "rand_mode", expand=True)
            body.separator(factor=0.5)

            # Range + sign — all about what values get generated
            range_box = body.box()
            range_box.label(text="Range:", icon='ARROW_LEFTRIGHT')
            rrow = range_box.row(align=True)
            rrow.prop(props, "rand_min", text="Min")
            rrow.prop(props, "rand_max", text="Max")
            if props.rand_min > props.rand_max:
                w = range_box.row()
                w.alert = True
                w.label(text="Min must be ≤ Max!", icon='ERROR')
            range_box.prop(props, "rand_allow_negative", toggle=True,
                           icon='ARROW_LEFTRIGHT')
            if props.use_degrees:
                dh = range_box.row()
                dh.enabled = False
                dh.label(text="Range values treated as degrees", icon='INFO')

            body.separator(factor=0.5)

            # Seed — reproducibility
            seed_box = body.box()
            seed_box.prop(props, "rand_seed")
            seed_box.prop(props, "rand_per_channel", toggle=True,
                          icon='RENDERLAYERS')
            sr = seed_box.row()
            sr.enabled = False
            sr.label(text="Auto-changes on Overwrite", icon='FILE_REFRESH')


        # ── WARNINGS ──────────────────────────────────────────────────────────
        if not props.additive:
            total_dur = props.lead_frames + props.event_frames
            if total_dur > fpb:
                row = layout.row()
                row.alert = True
                row.label(
                    text=f"Lead + Event ({total_dur} fr) exceeds 1 beat ({fpb:.1f} fr)",
                    icon='ERROR',
                )
        if not active:
            row = layout.row()
            row.alert = True
            row.label(text="No beats active in pattern!", icon='ERROR')

        # ── EXECUTE ───────────────────────────────────────────────────────────
        layout.separator(factor=0.5)
        row = layout.row(align=True)
        row.scale_y = 1.4
        row.operator("graph.insert_pulse_keyframes",    text="Insert",    icon='KEYFRAME_HLT')
        row.operator("graph.overwrite_pulse_keyframes", text="Overwrite", icon='FILE_REFRESH')

    @staticmethod
    def _dur_col(row, props, attr, frame_val, bpm, fps):
        """Duration field stacked above its beat-equivalent label."""
        col = row.column(align=True)
        col.prop(props, attr, text="fr")
        sub = col.row()
        sub.enabled = False
        sub.label(text=f"{frames_to_beats(frame_val, bpm, fps):.3f} b")
        return col


# ─── Global Variable ──────────────────────────────────────────────────────────
custom_icons = None

# ─── Registration ─────────────────────────────────────────────────────────────

CLASSES = [
    PulseKeyframeProperties,
    GRAPH_OT_insert_pulse_keyframes,
    GRAPH_OT_overwrite_pulse_keyframes,
    GRAPH_PT_pulse_keyframes,
]

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, "..", "icons")
    custom_icons.load(
        "opstyix_icon", os.path.join(icons_dir, "opstyix_icon.png"), "IMAGE"
    )
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pulse_keyframe_props = bpy.props.PointerProperty(
        type=PulseKeyframeProperties
    )

def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.pulse_keyframe_props

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("\nPulse Keyframe Tool registered.")
    print("Graph Editor → N-panel → 'Pulse' tab.\n")