"""Spatial-only derivatives of immutable 720p camera/data specifications.

No simulator/model imports. Legacy bundle bytes and temporal protocols stay fixed.
"""
from copy import deepcopy
import hashlib
import json

LEGACY_RGB = "dual-rgb-720p-v1"
RGB_360 = "dual-rgb-360p-v1"
RGB_HW = {LEGACY_RGB: (720, 1280), RGB_360: (360, 640)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def camera_profile(camera, rgb_profile):
    if rgb_profile not in RGB_HW:
        raise ValueError("Unknown policy RGB profile")
    value = deepcopy(camera)
    if rgb_profile == RGB_360:
        value["width"], value["height"] = 640, 360
        value["intrinsics"] = [[v * 0.5 for v in row] if i < 2 else row
                               for i, row in enumerate(value["intrinsics"])]
        if "source_parameters" in value:
            value["source_parameters"].update(width=640, height=360)
        value["rgb_spatial_profile"] = RGB_360
    return value


def dataset_profile(base, rgb_profile):
    value = deepcopy(base)
    if rgb_profile not in RGB_HW:
        raise ValueError("Unknown policy RGB profile")
    if rgb_profile == RGB_360:
        value["rgb_spatial_profile"] = RGB_360
        value["policy_camera_geometry"] = {k: camera_profile(v, rgb_profile)
                                            for k, v in value["policy_camera_geometry"].items()}
        value["policy_video"].update(width=640, height=360)
    return value


def resolve_dataset_profile(base, sha):
    for key in RGB_HW:
        value = dataset_profile(base, key)
        if digest(value) == sha:
            return value, key
    raise ValueError("Unrecognized dataset spatial profile hash")


def camera_bundle(base, rgb_profile):
    value = deepcopy(base)
    for k in ("go2_ego", "d435i_rgb_task"):
        value[k] = camera_profile(base[k], rgb_profile)
        value["cameras"]["cameras"][k] = digest(value[k])
    if rgb_profile == RGB_360:
        value["cameras"]["id"] = RGB_360
    return value


def resolve_camera(base, camera, sha):
    for key in RGB_HW:
        value = camera_profile(base[camera], key)
        if digest(value) == sha:
            return value, key
    raise ValueError("Unrecognized camera spatial profile hash")
