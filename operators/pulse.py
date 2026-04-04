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
from contextlib import contextmanager
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import (IntProperty, FloatProperty,
                        EnumProperty, BoolVectorProperty, BoolProperty)

MAX_BAR_LENGTH = 8


# ─── Helpers ──────────────────────────────────────────────────────────────────

def scene_fps(context):
    r = context.scene.render
    return r.fps / r.fps_base

def beat_to_frame(beat_index_0, bpm, fps, snap=True):
    val = beat_index_0 * fps * 60.0 / bpm
    return round(val) if snap else val

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

def _iter_actions(context):
    """Yield every action reachable from the current context — mirrors what
    the Graph Editor can display."""
    seen = set()

    def _emit(anim_data):
        if anim_data is not None and anim_data.action is not None:
            act = anim_data.action
            if id(act) not in seen:
                seen.add(id(act))
                yield act

    obj = context.active_object
    if obj is not None:
        yield from _emit(obj.animation_data)

        if obj.data is not None:
            yield from _emit(obj.data.animation_data)
            shape_keys = getattr(obj.data, "shape_keys", None)
            if shape_keys is not None:
                yield from _emit(shape_keys.animation_data)

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            yield from _emit(mat.animation_data)
            if mat.node_tree is not None:
                yield from _emit(mat.node_tree.animation_data)

        for ps in getattr(obj, "particle_systems", []):
            if ps.settings is not None:
                yield from _emit(ps.settings.animation_data)

    scene = context.scene
    yield from _emit(scene.animation_data)
    world = getattr(scene, "world", None)
    if world is not None:
        yield from _emit(world.animation_data)
        if world.node_tree is not None:
            yield from _emit(world.node_tree.animation_data)


def _get_active_fcurve(context):
    fc = getattr(context, "active_editable_fcurve", None)
    if fc is not None:
        return fc
    for action in _iter_actions(context):
        for curve in _get_all_fcurves(action):
            if curve.select:
                return curve
    return None

def _get_selected_fcurves(context):
    result = []
    for action in _iter_actions(context):
        result.extend(fc for fc in _get_all_fcurves(action) if fc.select)
    return result



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
    ('LINEAR', 'Linear', 'Constant rate of change', 'IPO_LINEAR', 0),
    ('SINE',   'Sine',   'Sinusoidal easing',        'IPO_SINE',   1),
    ('QUAD',   'Quad',   'Quadratic easing',         'IPO_QUAD',   2),
    ('CUBIC',  'Cubic',  'Cubic easing',             'IPO_CUBIC',  3),
    ('QUART',  'Quart',  'Quartic easing',           'IPO_QUART',  4),
    ('QUINT',  'Quint',  'Quintic easing',           'IPO_QUINT',  5),
    ('EXPO',   'Expo',   'Exponential easing',       'IPO_EXPO',   6),
    ('CIRC',   'Circ',   'Circular easing',          'IPO_CIRC',   7),
]

EASING_ITEMS = [
    ('AUTO',        'Auto',     'Automatic easing',              'IPO_EASE_IN_OUT', 0),
    ('EASE_IN',     'In',       'Accelerate into the keyframe',  'IPO_EASE_IN',     1),
    ('EASE_OUT',    'Out',      'Decelerate out of the keyframe','IPO_EASE_OUT',     2),
    ('EASE_IN_OUT', 'In / Out', 'Accelerate in, decelerate out', 'IPO_EASE_IN_OUT', 3),
]

def apply_kp(kp, interp, easing):
    kp.interpolation = interp
    if interp in EASING_AWARE:
        kp.easing = easing


# ─── Property Group ───────────────────────────────────────────────────────────

class PulseKeyframeProperties(PropertyGroup):

    bpm: IntProperty(
        name="BPM",
        description="Tempo in beats per minute (used when the Beat Marker module is disabled)",
        default=128, min=1, max=999,
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
        default=(True,) * MAX_BAR_LENGTH,
    )
    num_bars: IntProperty(
        name="Bars",
        description="How many bars to repeat the pattern across",
        default=4, min=1, soft_max=64,
    )

    fill_gaps: BoolProperty(
        name="Fill Gaps",
        description="Insert a keyframe at base value (0 or Min) on unselected beats",
        default=False,
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
    use_peak_range: BoolProperty(
        name="Use Range",
        description="Clamp the inserted peak value between a minimum and maximum",
        default=False,
    )
    peak_min: FloatProperty(
        name="Min",
        description="Minimum allowed peak value",
        default=0.0,
        soft_min=-10.0, soft_max=10.0,
        precision=3,
    )
    peak_max: FloatProperty(
        name="Max",
        description="Maximum allowed peak value",
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
        default=0, min=0, soft_max=500, subtype='TIME',
    )

    # ── Curves ────────────────────────────────────────────────────────────────
    interp_advanced: BoolProperty(
        name="Advanced",
        description="Expose lead/fade frame counts and lead interpolation settings",
        default=False,
    )
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
    # ── Randomization ─────────────────────────────────────────────────────────
    use_random: BoolProperty(
        name="Randomize",
        description="Apply a random variation to the peak value of each event",
        default=False,
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
    # ── Frequency ─────────────────────────────────────────────────────────────
    beat_multiplier: EnumProperty(
        name="Frequency",
        description="Beat frequency multiplier — 1x fires once per beat, 2x every half-beat, etc.",
        items=[
            ('1', '1x', 'One pulse per beat'),
            ('2', '2x', 'Two pulses per beat (doubles)'),
            ('3', '3x', 'Three pulses per beat (triples)'),
            ('4', '4x', 'Four pulses per beat'),
            ('5', '5x', 'Five pulses per beat'),
            ('6', '6x', 'Six pulses per beat'),
            ('7', '7x', 'Seven pulses per beat'),
            ('8', '8x', 'Eight pulses per beat'),
        ],
        default='1',
    )
    # ── Snapping ──────────────────────────────────────────────────────────────
    snap_keyframes: BoolProperty(
        name="Snap to Frames",
        description=(
            "When enabled, keyframe positions are rounded to the nearest integer frame.\n"
            "When disabled, positions are exact floating-point values — useful when the "
            "beat grid does not divide evenly into whole frames."
        ),
        default=True,
    )
    # ── Beat Randomization ────────────────────────────────────────────────────
    rand_beats: BoolProperty(
        name="Randomize Beats",
        description=(
            "Randomly determine which beats fire each bar, "
            "overriding the manual beat pattern selection"
        ),
        default=False,
    )
    beat_probability: FloatProperty(
        name="Probability",
        description="Probability (0–1) that any given beat fires when randomizing",
        default=0.5,
        min=0.0, max=1.0,
        precision=2,
        subtype='FACTOR',
    )
    beat_rand_seed: IntProperty(
        name="Seed",
        description=(
            "Seed for beat randomization — same seed always produces "
            "the same beat pattern. Change to get a different result."
        ),
        default=0,
        min=0, max=99999,
    )


# ─── BPM helper ───────────────────────────────────────────────────────────────

def get_bpm(context):
    """Return BPM from Beat Marker if available, otherwise fall back to Pulse's own property."""
    marker_props = getattr(context.scene, "OPSTYIX_MarkerProperties", None)
    if marker_props is not None:
        return marker_props.input_bpm
    return context.scene.pulse_keyframe_props.bpm


# ─── Snap guard ───────────────────────────────────────────────────────────────

@contextmanager
def _snap_guard(context, props):
    """Temporarily disable animation snapping if props.snap_keyframes is False."""
    ts       = context.scene.tool_settings
    original = ts.use_snap_anim
    if not props.snap_keyframes:
        ts.use_snap_anim = False
    try:
        yield
    finally:
        if not props.snap_keyframes:
            ts.use_snap_anim = original


# ─── Shared logic ─────────────────────────────────────────────────────────────

def get_active_beat_indices(props):
    return [i for i in range(props.bar_length) if props.beat_pattern[i]]


def get_pulse_events(props, fps, bpm, rng=None, is_angle=False, frame_offset=None,
                     num_bars_override=None):
    """
    Return a list of dicts, one per pulse event, containing:
      peak_frame, lead_frame, end_frame,
      lead_value, peak_value, end_value
    rng: optional random.Random instance for reproducible randomization.
    is_angle: when True, peak_value and rand range are treated as degrees and
              converted to radians before inserting.
    num_bars_override: if set, overrides props.num_bars (used for doubles mode).
    """
    active           = get_active_beat_indices(props)
    bpm              = float(bpm)
    pv               = (props.peak_value * math.pi / 180.0 if is_angle else props.peak_value)
    events           = []
    pulse_index      = 0
    last_active_peak = 0.0

    num_bars = num_bars_override if num_bars_override is not None else props.num_bars
    for bar in range(num_bars):
        bar_start = bar * props.bar_length

        # Determine which beats are active this bar
        if props.rand_beats:
            bar_rng     = random.Random(props.beat_rand_seed + bar)
            bar_active  = [i for i in range(props.bar_length)
                           if bar_rng.random() < props.beat_probability]
        else:
            bar_active  = active
        bar_active_set = set(bar_active)

        beat_range = (range(props.bar_length)
                      if (props.fill_gaps and not props.additive)
                      else bar_active)

        for beat_offset in beat_range:
            global_beat = bar_start + beat_offset
            offset      = frame_offset if frame_offset is not None else props.frame_offset
            peak_frame  = beat_to_frame(global_beat, bpm, fps, snap=props.snap_keyframes) + offset

            # ── Resolve base value ────────────────────────────────────────────
            if props.use_peak_range:
                p_min    = (props.peak_min * math.pi / 180.0 if is_angle else props.peak_min)
                p_max    = (props.peak_max * math.pi / 180.0 if is_angle else props.peak_max)
                base_pv  = p_max
                base_val = p_min
            else:
                base_pv  = pv
                base_val = 0.0

            if beat_offset not in bar_active_set:
                fill_val = last_active_peak if props.additive else base_val
                events.append({
                    "peak_frame": peak_frame,
                    "peak_value": fill_val,
                    "active":     False,
                })
                continue

            if rng is not None and props.use_random:
                r_val = rng.uniform(props.rand_min, props.rand_max)
                if is_angle:
                    r_val = r_val * math.pi / 180.0
                event_pv = base_pv + r_val
                if props.rand_allow_negative:
                    event_pv = abs(event_pv) * (-1 if rng.random() < 0.5 else 1)
                if props.use_peak_range:
                    event_pv = max(p_min, min(p_max, event_pv))
            else:
                event_pv = base_pv

            if props.additive:
                peak_val         = pulse_index * pv
                lead_val         = peak_val
                end_val          = peak_val
                last_active_peak = peak_val
            else:
                lead_val = base_val
                peak_val = event_pv
                end_val  = base_val

            events.append({
                "peak_frame": peak_frame,
                "lead_frame": peak_frame - props.lead_frames,
                "end_frame":  peak_frame + props.event_frames,
                "lead_value": lead_val,
                "peak_value": peak_val,
                "end_value":  end_val,
                "bar":        bar + 1,
                "beat":       beat_offset + 1,
                "active":     True,
            })
            pulse_index += 1

    return events


def clear_fcurve_keyframes(fc):
    kps = fc.keyframe_points
    for i in range(len(kps) - 1, -1, -1):
        kps.remove(kps[i])


def do_insert(fc, props, fps, bpm, seed=None, frame_offset=None, num_bars_override=None):
    rng             = random.Random(seed if seed is not None else props.rand_seed) if props.use_random else None
    is_angle        = _fcurve_is_angle(fc)
    total           = 0
    last_frame      = None
    last_peak_value = None
    events          = get_pulse_events(props, fps, bpm, rng=rng, is_angle=is_angle,
                                       frame_offset=frame_offset,
                                       num_bars_override=num_bars_override)
    for ev in events:
        last_frame = ev["peak_frame"]
        if not ev.get("active", True):
            kp = fc.keyframe_points.insert(
                ev["peak_frame"], ev["peak_value"], options={'FAST'})
            apply_kp(kp, props.fade_interp, props.fade_easing)
            total += 1
            continue

        if props.additive:
            last_peak_value = ev["peak_value"]
            kp = fc.keyframe_points.insert(
                ev["peak_frame"], ev["peak_value"], options={'FAST'})
            apply_kp(kp, props.lead_interp, props.lead_easing)
            total += 1
        else:
            if props.interp_advanced:
                lead_frames  = props.lead_frames
                lead_interp  = props.lead_interp
                lead_easing  = props.lead_easing
                event_frames = props.event_frames
            else:
                lead_frames  = 1
                lead_interp  = 'LINEAR'
                lead_easing  = 'AUTO'
                event_frames = 0

            if lead_frames > 0:
                kp = fc.keyframe_points.insert(
                    ev["peak_frame"] - lead_frames, ev["lead_value"], options={'FAST'})
                apply_kp(kp, lead_interp, lead_easing)
                total += 1

            kp = fc.keyframe_points.insert(
                ev["peak_frame"], ev["peak_value"], options={'FAST'})
            apply_kp(kp, props.fade_interp, props.fade_easing)
            total += 1

            if event_frames > 0:
                kp = fc.keyframe_points.insert(
                    ev["peak_frame"] + event_frames, ev["end_value"], options={'FAST'})
                apply_kp(kp, props.fade_interp, props.fade_easing)
                total += 1

    if last_frame is not None:
        fpb         = fps * 60.0 / float(bpm)
        extra_frame = round(last_frame + fpb) if props.snap_keyframes else (last_frame + fpb)
        if props.additive and last_peak_value is not None:
            trail_val = last_peak_value
        else:
            trail_val = (props.peak_min if props.use_peak_range else 0.0)
        kp = fc.keyframe_points.insert(extra_frame, trail_val, options={'FAST'})
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
    if not props.rand_beats and not get_active_beat_indices(props):
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
        props        = context.scene.pulse_keyframe_props
        curves       = _get_selected_fcurves(context)
        if not common_validate(self, props, _get_active_fcurve(context)):
            return {'CANCELLED'}
        mult         = int(props.beat_multiplier)
        fps          = scene_fps(context)
        bpm          = get_bpm(context) * mult
        frame_offset = context.scene.frame_current
        num_bars     = props.num_bars * mult if mult > 1 else None
        total        = 0
        with _snap_guard(context, props):
            for i, fc in enumerate(curves):
                seed = (props.rand_seed + i) if (props.use_random and props.rand_per_channel) else None
                total += do_insert(fc, props, fps, bpm, seed=seed,
                                   frame_offset=frame_offset, num_bars_override=num_bars)
        self.report({'INFO'}, f"Inserted {total} keyframes across {len(curves)} channel(s).")
        return {'FINISHED'}


class GRAPH_OT_overwrite_pulse_keyframes(Operator):
    bl_idname      = "graph.overwrite_pulse_keyframes"
    bl_label       = "Apply"
    bl_description = "Clear ALL existing keyframes then insert the pulse pattern fresh"
    bl_options     = {'REGISTER', 'UNDO'}
    poll           = classmethod(common_poll)

    def execute(self, context):
        props    = context.scene.pulse_keyframe_props
        curves   = _get_selected_fcurves(context)
        if not common_validate(self, props, _get_active_fcurve(context)):
            return {'CANCELLED'}
        mult     = int(props.beat_multiplier)
        fps      = scene_fps(context)
        bpm      = get_bpm(context) * mult
        num_bars = props.num_bars * mult if mult > 1 else None
        cleared  = 0
        total    = 0
        if props.use_random:
            props.rand_seed = random.randint(0, 99999)
        if props.rand_beats:
            props.beat_rand_seed = random.randint(0, 99999)
        with _snap_guard(context, props):
            for i, fc in enumerate(curves):
                cleared += len(fc.keyframe_points)
                clear_fcurve_keyframes(fc)
                seed = (props.rand_seed + i) if props.rand_per_channel else None
                total += do_insert(fc, props, fps, bpm, seed=seed, num_bars_override=num_bars)
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
        layout       = self.layout
        props        = context.scene.pulse_keyframe_props
        marker_props = getattr(context.scene, "OPSTYIX_MarkerProperties", None)
        fps          = scene_fps(context)
        bpm          = float(get_bpm(context))
        fpb          = fps * 60.0 / bpm
        active       = get_active_beat_indices(props)


        # ── TEMPO & PATTERN ───────────────────────────────────────────────────
        header, body = layout.panel("pulse_tempo", default_closed=False)
        header.label(text="Tempo", icon='TIME')
        if body:
            row = body.row(align=True)
            if marker_props is not None:
                row.prop(marker_props, "input_bpm", text="BPM")
            else:
                row.prop(props, "bpm", text="BPM")
            row.prop(props, "frame_offset")
            info = body.row()
            info.enabled = False
            info.label(
                text=f"1 beat = {fpb:.2f} fr",
                icon='INFO',
            )

            body.separator(factor=0.5)

            col = body.column(align=True)
            row = col.row(align=True)
            row.prop(props, "bar_length")
            row.prop(props, "num_bars")

            n    = props.bar_length
            cols = min(n, 8)
            beat_col = col.column(align=True)
            beat_col.enabled = not props.rand_beats
            grid = beat_col.grid_flow(
                row_major=True, columns=cols,
                even_columns=True, even_rows=True, align=True,
            )
            for i in range(n):
                grid.prop(props, "beat_pattern", index=i,
                          text=str(i + 1), toggle=True)

            col.separator(factor=0.5)

            rand_row = col.row(align=True)
            rand_row.prop(props, "rand_beats", text="Randomize", toggle=True,
                          icon='FORCE_TURBULENCE')
            if props.rand_beats:
                sub = col.column(align=True)
                sub.prop(props, "beat_probability", text="Probability", slider=True)
                sub.prop(props, "beat_rand_seed", text="Seed")

            row = col.row()
            row.enabled = not props.additive
            row.prop(props, "fill_gaps")

        # ── PEAK ──────────────────────────────────────────────────────────────
        # Mode, peak value, and degrees — all about what value gets written
        header, body = layout.panel("pulse_peak", default_closed=False)
        header.label(text="Peak", icon='KEYFRAME_HLT')
        if body:
            col = body.column(align=True)
            col.prop(props, "additive", toggle=True,
                     text="Additive" if props.additive else "Standard",
                     icon='PLUS' if props.additive else 'KEYFRAME')

            row = col.row(align=True)
            if props.additive:
                row.prop(props, "peak_value", text="Step")
            else:
                row.prop(props, "use_peak_range", text="Range", toggle=True)
                sub = row.row(align=True)
                sub.enabled = props.use_peak_range
                sub.prop(props, "peak_min", text="Min")
                if props.use_peak_range:
                    row.prop(props, "peak_max", text="Max")
                else:
                    row.prop(props, "peak_value", text="Max")

            col.separator()

            # ── Randomize ─────────────────────────────────────────────────────
            rand_row = col.row(align=True)
            rand_row.prop(props, "use_random", text="Randomize", toggle=True,
                          icon='FORCE_TURBULENCE')
            rrow = col.row(align=True)
            rrow.enabled = props.use_random
            rrow.prop(props, "rand_min", text="Min")
            rrow.prop(props, "rand_max", text="Max")
            if props.use_random:
                if props.rand_min > props.rand_max:
                    w = col.row()
                    w.alert = True
                    w.label(text="Min must be ≤ Max!", icon='ERROR')
                col.prop(props, "rand_seed")
                col.prop(props, "rand_per_channel")
                col.prop(props, "rand_allow_negative")

        # ── INTERPOLATION ─────────────────────────────────────────────────────
        header, body = layout.panel("pulse_envelope", default_closed=False)
        header.label(text="Interpolation", icon='IPO_EASE_IN_OUT')
        if body:
            col = body.column(align=True)
            if props.additive:
                col.prop(props, "lead_interp", text="")
                col.prop(props, "lead_easing", text="")
            else:
                col.prop(props, "interp_advanced", text="Advanced", toggle=True)
                col.separator(factor=0.5)

                if props.interp_advanced:
                    col.label(text="Lead", icon='TRIA_UP')
                    row = col.row(align=True)
                    row.prop(props, "lead_frames", text="Frames")
                    row.prop(props, "lead_interp", text="")
                    hint = col.row(align=True)
                    sub = hint.row()
                    sub.enabled = False
                    sub.label(text=f"{frames_to_beats(props.lead_frames, bpm, fps):.3f} b")
                    hint.prop(props, "lead_easing", text="")

                    col.separator()

                    col.label(text="Fade", icon='TRIA_DOWN')
                    row2 = col.row(align=True)
                    row2.prop(props, "event_frames", text="Frames")
                    row2.prop(props, "fade_interp", text="")
                    hint2 = col.row(align=True)
                    sub2 = hint2.row()
                    sub2.enabled = False
                    sub2.label(text=f"{frames_to_beats(props.event_frames, bpm, fps):.3f} b")
                    hint2.prop(props, "fade_easing", text="")
                else:
                    row = col.row(align=True)
                    row.prop(props, "fade_interp", text="")
                    row.prop(props, "fade_easing", text="")



        # ── WARNINGS ──────────────────────────────────────────────────────────
        if not _get_selected_fcurves(context):
            row = layout.row()
            row.alert = True
            row.label(text="No channel selected. Select an F-Curve to continue.", icon='INFO')
        if not props.additive:
            total_dur = props.lead_frames + props.event_frames
            if total_dur > fpb:
                row = layout.row()
                row.alert = True
                row.label(
                    text=f"Lead + Event ({total_dur} fr) exceeds 1 beat ({fpb:.1f} fr)",
                    icon='ERROR',
                )
        if not active and not props.rand_beats:
            row = layout.row()
            row.alert = True
            row.label(text="No beats active in pattern!", icon='ERROR')

        # ── EXECUTE ───────────────────────────────────────────────────────────
        header, body = layout.panel("pulse_execute", default_closed=False)
        header.label(text="Execute", icon='PLAY')
        if body:
            body.prop(props, "snap_keyframes")
            row = body.row(align=True)
            row.scale_y = 1.4
            row.prop(props, "beat_multiplier", text="")
            row.operator("graph.overwrite_pulse_keyframes", text="Apply", icon='FILE_REFRESH')


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
    print("Graph Editor → N-panel → 'OPSTYIX' tab.\n")