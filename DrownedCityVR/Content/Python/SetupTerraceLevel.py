"""Editor script for /Game/VRTemplate/Maps/Terrace.

Builds baseline lighting, fog, floor, and PlayerStart. Also dedupes conflicting
lights (common after map duplicates) and clamps exposure for forward-shaded VR.

File -> Execute Python Script, or run from the Output Log Cmd line.
"""

import unreal

TERRACE_MAP = "/Game/VRTemplate/Maps/Terrace"
USE_OPEN_LEVEL = False

FLOOR_MESH = "/Game/LevelPrototyping/Meshes/SM_Cube"
FLOOR_MAT = "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray"
FLOOR_SCALE = unreal.Vector(25.0, 25.0, 0.3)
FLOOR_POS = unreal.Vector(0.0, 0.0, 15.0)

PLAYER_START_POS = unreal.Vector(0.0, -400.0, 50.0)
SUN_ROT = unreal.Rotator(-42.0, 135.0, 0.0)
SUN_LUX = 40000.0

SKIP_DUPLICATES = True
FIX_LIGHTING = True
PREFERRED_SUN_LABEL = "Terrace_Sun"


def _log(message):
    unreal.log(f"[TerraceSetup] {message}")


def _warn(message):
    unreal.log_warning(f"[TerraceSetup] {message}")


def _editor_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return list(subsystem.get_all_level_actors())


def _actors_of_class(actor_class):
    return [a for a in _editor_actors() if a.get_class() == actor_class]


def _any_of_class(actor_class):
    return len(_actors_of_class(actor_class)) > 0


def _any_with_label(fragment):
    needle = fragment.lower()
    return any(needle in actor.get_actor_label().lower() for actor in _editor_actors())


def _destroy(actor):
    if actor is None:
        return
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    subsystem.destroy_actor(actor)


def _pick_preferred(actors, preferred_label):
    preferred_label = preferred_label.lower()
    for actor in actors:
        if actor.get_actor_label().lower() == preferred_label:
            return actor
    return actors[0] if actors else None


def _dedupe(actor_class, preferred_label):
    actors = _actors_of_class(actor_class)
    if len(actors) <= 1:
        return _pick_preferred(actors, preferred_label)

    keep = _pick_preferred(actors, preferred_label)
    removed = 0
    for actor in actors:
        if actor != keep:
            _destroy(actor)
            removed += 1

    class_name = actor_class.get_name()
    _log(f"Removed {removed} extra {class_name} actor(s), kept {keep.get_actor_label()}")
    return keep


def _configure_sun(actor):
    if actor is None:
        return

    component = actor.get_component_by_class(unreal.DirectionalLightComponent)
    if component is None:
        return

    component.set_mobility(unreal.ComponentMobility.STATIONARY)
    component.set_intensity(SUN_LUX)
    component.set_light_color(unreal.LinearColor(1.0, 0.92, 0.82, 1.0))
    component.set_atmosphere_sun_light(True)
    component.set_cast_shadows(True)

    actor.set_actor_label(PREFERRED_SUN_LABEL)
    _log("Configured primary DirectionalLight (Stationary)")


def _configure_sky_light(actor):
    if actor is None:
        return
    component = actor.get_component_by_class(unreal.SkyLightComponent)
    if component:
        component.set_mobility(unreal.ComponentMobility.STATIONARY)
        component.set_real_time_capture(True)
    actor.set_actor_label("Terrace_SkyLight")


def _configure_fog(actor):
    if actor is None:
        return
    component = actor.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if component:
        component.set_fog_density(0.02)
        component.set_fog_height_falloff(0.3)
        component.set_volumetric_fog(False)
    actor.set_actor_label("Terrace_Fog")


def _fix_post_process_volumes():
    volumes = _actors_of_class(unreal.PostProcessVolume)
    if not volumes:
        return

    for actor in volumes:
        settings = actor.get_editor_property("settings")

        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property(
            "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL
        )
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_bias", 0.0)
        settings.set_editor_property("override_auto_exposure_min_brightness", True)
        settings.set_editor_property("auto_exposure_min_brightness", 0.5)
        settings.set_editor_property("override_auto_exposure_max_brightness", True)
        settings.set_editor_property("auto_exposure_max_brightness", 2.0)

        actor.set_editor_property("settings", settings)

        for prop in ("unbound", "b_unbound", "bUnbound"):
            try:
                actor.set_editor_property(prop, True)
                break
            except Exception:
                pass

        if actor.get_actor_label().startswith("PostProcessVolume"):
            actor.set_actor_label("Terrace_PostProcess")

    _log(f"Tuned exposure on {len(volumes)} PostProcessVolume(s)")


def _fix_lighting_conflicts():
    sun = _dedupe(unreal.DirectionalLight, PREFERRED_SUN_LABEL)
    _configure_sun(sun)

    sky = _dedupe(unreal.SkyLight, "Terrace_SkyLight")
    _configure_sky_light(sky)

    _dedupe(unreal.SkyAtmosphere, "Terrace_SkyAtmosphere")
    fog = _dedupe(unreal.ExponentialHeightFog, "Terrace_Fog")
    _configure_fog(fog)

    clouds = _actors_of_class(unreal.VolumetricCloud)
    if len(clouds) > 1:
        keep = _pick_preferred(clouds, "Terrace_Clouds")
        for actor in clouds:
            if actor != keep:
                _destroy(actor)
        _log("Removed duplicate VolumetricCloud actors")

    _fix_post_process_volumes()


def _spawn_class(actor_class, location, rotation=None, label=None):
    rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(actor_class, location, rotation)
    if actor and label:
        actor.set_actor_label(label)
    return actor


def _spawn_mesh(mesh_path, location, scale, label):
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        _warn(f"Missing mesh: {mesh_path}")
        return None

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_object(
        mesh, location, unreal.Rotator(0.0, 0.0, 0.0)
    )
    if actor is None:
        _warn(f"Could not place mesh: {mesh_path}")
        return None

    actor.set_actor_scale3d(scale)
    actor.set_actor_label(label)

    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_component:
        mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        mesh_component.set_collision_profile_name("BlockAll")
        material = unreal.load_asset(FLOOR_MAT)
        if material:
            mesh_component.set_material(0, material)

    return actor


def _open_terrace():
    if USE_OPEN_LEVEL:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        if world is None:
            raise RuntimeError("No level is open.")
        _log(f"Using open level: {world.get_name()}")
        return

    if not unreal.EditorAssetLibrary.does_asset_exist(TERRACE_MAP):
        raise RuntimeError(f"Map not found: {TERRACE_MAP}")

    unreal.EditorLoadingAndSavingUtils.load_map(TERRACE_MAP)
    _log(f"Opened {TERRACE_MAP}")


def _save_terrace():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world is None:
        _warn("Nothing to save.")
        return

    save_path = TERRACE_MAP
    if USE_OPEN_LEVEL:
        outer = world.get_outer()
        if outer:
            save_path = outer.get_path_name().split(".")[0]

    try:
        unreal.EditorLoadingAndSavingUtils.save_map(world, save_path)
    except Exception:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages_with_confirmation(False)

    _log(f"Saved {save_path}")


def _try_step(name, step_fn):
    try:
        step_fn()
    except Exception as error:
        _warn(f"{name}: {error}")


def _add_sun():
    if SKIP_DUPLICATES and _any_of_class(unreal.DirectionalLight):
        return

    actor = _spawn_class(
        unreal.DirectionalLight,
        unreal.Vector(0.0, 0.0, 500.0),
        SUN_ROT,
        PREFERRED_SUN_LABEL,
    )
    _configure_sun(actor)
    _log("Placed DirectionalLight")


def _add_sky_light():
    if SKIP_DUPLICATES and _any_of_class(unreal.SkyLight):
        return

    actor = _spawn_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 600.0), label="Terrace_SkyLight")
    _configure_sky_light(actor)
    _log("Placed SkyLight")


def _add_sky_atmosphere():
    if SKIP_DUPLICATES and _any_of_class(unreal.SkyAtmosphere):
        return

    _spawn_class(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0), label="Terrace_SkyAtmosphere")
    _log("Placed SkyAtmosphere")


def _add_fog():
    if SKIP_DUPLICATES and _any_of_class(unreal.ExponentialHeightFog):
        return

    actor = _spawn_class(unreal.ExponentialHeightFog, unreal.Vector(0.0, 0.0, 0.0), label="Terrace_Fog")
    _configure_fog(actor)
    _log("Placed ExponentialHeightFog")


def _add_post_process():
    if SKIP_DUPLICATES and _any_of_class(unreal.PostProcessVolume):
        return

    _spawn_class(unreal.PostProcessVolume, unreal.Vector(0.0, 0.0, 0.0), label="Terrace_PostProcess")
    _log("Placed PostProcessVolume")


def _add_floor():
    if SKIP_DUPLICATES and _any_with_label("Terrace_Floor"):
        return

    _spawn_mesh(FLOOR_MESH, FLOOR_POS, FLOOR_SCALE, "Terrace_Floor")
    _log("Placed floor")


def _add_player_start():
    if SKIP_DUPLICATES and _any_of_class(unreal.PlayerStart):
        return

    _spawn_class(unreal.PlayerStart, PLAYER_START_POS, label="Terrace_PlayerStart")
    _log("Placed PlayerStart")


def run():
    _log("Starting")
    _open_terrace()

    if FIX_LIGHTING:
        _try_step("FixLighting", _fix_lighting_conflicts)

    for label, step in (
        ("SkyAtmosphere", _add_sky_atmosphere),
        ("Sun", _add_sun),
        ("SkyLight", _add_sky_light),
        ("Fog", _add_fog),
        ("PostProcess", _add_post_process),
        ("Floor", _add_floor),
        ("PlayerStart", _add_player_start),
    ):
        _try_step(label, step)

    if FIX_LIGHTING:
        _try_step("FixLightingFinal", _fix_lighting_conflicts)

    _save_terrace()
    _log("Finished")


if __name__ == "__main__":
    run()
