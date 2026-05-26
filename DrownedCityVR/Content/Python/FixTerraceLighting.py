"""
FixTerraceLighting.py
=====================
For the Terrace level:
1. Positions the RuinedCrypt_01_P Level Instance relative to PlayerStart
2. Sets lighting to match RuinedCrypt's cool atmospheric tone
3. Disables shadow casting on excess movable lights (fixes overlap warning)

How to run:
  File -> Execute Python Script -> select this file
  Terrace.umap must be open (tab should show "Terrace")
"""

import unreal

USE_OPEN_LEVEL = True   # Run against the currently open map

# How many units BELOW PlayerStart to place the RuinedCrypt ground
# (keeps terrain hidden beneath the tower platform)
RUIN_Z_OFFSET = -350.0

# RuinedCrypt scale — 0.7 = 70% of original size
RUIN_SCALE = 0.7

# Atmospheric light color: cool blue-green to match RuinedCrypt's soft tone
SUN_COLOR   = unreal.LinearColor(0.65, 0.80, 0.90, 1.0)   # cool / blue-white
SUN_LUX     = 8000.0      # low intensity for dusk/evening mood

SKY_INTENSITY = 1.2

FOG_DENSITY   = 0.04      # subtle atmospheric fog
FOG_FALLOFF   = 0.25


# ------------------------------------------------------------------ helpers --

def _log(msg):
    unreal.log(f"[FixTerrace] {msg}")

def _warn(msg):
    unreal.log_warning(f"[FixTerrace] {msg}")

def _actors():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return list(sub.get_all_level_actors())

def _of_class(cls):
    return [a for a in _actors() if a.get_class() == cls]


# --------------------------------------------------------------- functions ---

def fix_ruinedcrypt_position():
    """Aligns the RuinedCrypt Level Instance to the PlayerStart location."""
    all_actors = _actors()

    # Find PlayerStart
    ps = next((a for a in all_actors if a.get_class() == unreal.PlayerStart), None)
    if ps is None:
        _warn("PlayerStart not found — skipping RuinedCrypt positioning.")
        return

    ps_loc = ps.get_actor_location()
    _log(f"PlayerStart location: X={ps_loc.x:.0f} Y={ps_loc.y:.0f} Z={ps_loc.z:.0f}")

    # Find RuinedCrypt Level Instance by label or class name
    ruin = None
    for a in all_actors:
        label = a.get_actor_label().lower()
        cls   = a.get_class().get_name().lower()
        if "ruinedcrypt" in label or "ruined_crypt" in label or \
           ("levelinstance" in cls and "ruined" in label):
            ruin = a
            break

    if ruin is None:
        _warn("RuinedCrypt_01_P Level Instance not found. "
              "Check the actor label in the Outliner.")
        return

    # New position: same X/Y as PlayerStart, Z offset downward
    new_loc = unreal.Vector(ps_loc.x, ps_loc.y, ps_loc.z + RUIN_Z_OFFSET)
    ruin.set_actor_location(new_loc, sweep=False, teleport=True)
    ruin.set_actor_scale3d(unreal.Vector(RUIN_SCALE, RUIN_SCALE, RUIN_SCALE))
    ruin.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), teleport_physics=True)

    _log(f"RuinedCrypt positioned at Z={new_loc.z:.0f}  Scale={RUIN_SCALE}")


def fix_directional_light():
    """Sets the DirectionalLight to a cool atmospheric color."""
    lights = _of_class(unreal.DirectionalLight)
    if not lights:
        _warn("DirectionalLight not found.")
        return

    # Keep only the first one, remove duplicates
    keep = lights[0]
    for extra in lights[1:]:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(extra)
    _log(f"Removed {len(lights)-1} duplicate DirectionalLight(s).")

    comp = keep.get_component_by_class(unreal.DirectionalLightComponent)
    if comp:
        comp.set_intensity(SUN_LUX)
        comp.set_light_color(SUN_COLOR)
        comp.set_atmosphere_sun_light(True)
        comp.set_cast_shadows(True)
        comp.set_mobility(unreal.ComponentMobility.STATIONARY)
    _log("DirectionalLight updated.")


def fix_sky_light():
    """Sets SkyLight intensity and removes duplicates."""
    skies = _of_class(unreal.SkyLight)
    if not skies:
        return
    keep = skies[0]
    for extra in skies[1:]:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(extra)

    comp = keep.get_component_by_class(unreal.SkyLightComponent)
    if comp:
        comp.set_intensity(SKY_INTENSITY)
        comp.set_mobility(unreal.ComponentMobility.STATIONARY)
    _log("SkyLight updated.")


def fix_fog():
    """Configures subtle atmospheric height fog."""
    fogs = _of_class(unreal.ExponentialHeightFog)
    if not fogs:
        _warn("ExponentialHeightFog not found — skipping fog setup.")
        return
    comp = fogs[0].get_component_by_class(unreal.ExponentialHeightFogComponent)
    if comp:
        comp.set_fog_density(FOG_DENSITY)
        comp.set_fog_height_falloff(FOG_FALLOFF)
        comp.set_volumetric_fog(False)
    _log("Fog updated.")


def disable_excess_movable_shadows():
    """Disables shadow casting on movable PointLights and SpotLights
    to fix the TOO MANY OVERLAPPING SHADOWED MOVABLE LIGHTS warning."""
    all_actors = _actors()
    fixed = 0
    for a in all_actors:
        cls = a.get_class()
        if cls not in (unreal.PointLight, unreal.SpotLight):
            continue
        for comp_cls in (unreal.PointLightComponent, unreal.SpotLightComponent):
            comp = a.get_component_by_class(comp_cls)
            if comp and comp.get_mobility() == unreal.ComponentMobility.MOVABLE:
                comp.set_cast_shadows(False)
                fixed += 1
    if fixed:
        _log(f"Disabled shadow casting on {fixed} movable PointLight/SpotLight(s).")


def save():
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    if world:
        try:
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages_with_confirmation(False)
            _log("Saved.")
        except Exception as e:
            _warn(f"Save error: {e}")


# -------------------------------------------------------------------  main  --

def run():
    _log("Starting...")
    fix_ruinedcrypt_position()
    fix_directional_light()
    fix_sky_light()
    fix_fog()
    disable_excess_movable_shadows()
    save()
    _log("Done. Move the camera in the Viewport to see the changes.")


if __name__ == "__main__":
    run()
