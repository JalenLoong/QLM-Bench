"""Opt-in robot-mounted Lift-basket cameras; imports Isaac only at runtime."""

from __future__ import annotations

import math

import numpy as np

SETUP_ID = "robot-dual-v3"
SETUP_IDS = (SETUP_ID,)
BASE_PATH = "/World/envs/env_0/Robot/base"
RIG_PATH = BASE_PATH + "/task_camera_rig"
CAMERAS = {
    "ego": {"path": BASE_PATH + "/front_camera", "position": (0.30, 0.0, 0.08),
            "rotation_xyzw": (0.0, 0.0, 0.0, 1.0), "focal_length_mm": 18.0},
    "task": {"path": RIG_PATH + "/task_camera", "position": (0.30, 0.0, 0.34),
             "rotation_xyzw": (0.0, math.sin(math.radians(32.5)), 0.0, math.cos(math.radians(32.5))),
             "focal_length_mm": 9.0},
}
APERTURE_MM = 20.955
EGO_DIAGONAL_FOV_DEG = 120.0  # Brochure does not identify the axis: explicit assumption.
EGO_FOCAL_MM = math.hypot(APERTURE_MM, APERTURE_MM * 720 / 1280) / (2 * math.tan(math.radians(60)))
CAMERAS["ego"].update({
    "position": (0.32715, -0.00003, 0.04297), "focal_length_mm": EGO_FOCAL_MM,
    "width": 1280, "height": 720, "horizontal_aperture_mm": APERTURE_MM,
    "vertical_aperture_mm": APERTURE_MM * 720 / 1280,
    "calibration_status": "nominal_specification_approximation_not_device_calibration",
    "fov_axis_assumption": "diagonal", "diagonal_fov_deg": 120.,
    "projection": "centered_rectilinear_pinhole_no_distortion",
    "mount_source": "https://github.com/unitreerobotics/unitree_ros/blob/master/robots/go2_description/urdf/go2_description.urdf",
    "fov_source": "https://static.generation-robots.com/media/brochure-unitree-go2-en.pdf",
})
D435I_RGB_FOCAL_LENGTH_MM = 1.88
D435I_RGB_HORIZONTAL_FOV_DEG = 69.4
D435I_RGB_VERTICAL_FOV_PUBLISHED_DEG = 42.5
D435I_RGB_HORIZONTAL_APERTURE_MM = 2 * D435I_RGB_FOCAL_LENGTH_MM * math.tan(
    math.radians(D435I_RGB_HORIZONTAL_FOV_DEG / 2)
)
D435I_RGB_VERTICAL_APERTURE_MM = D435I_RGB_HORIZONTAL_APERTURE_MM * 720 / 1280
D435I_RGB_VERTICAL_FOV_SIMULATED_DEG = math.degrees(
    2 * math.atan(D435I_RGB_VERTICAL_APERTURE_MM / (2 * D435I_RGB_FOCAL_LENGTH_MM))
)
CAMERAS["task"].update({
    "focal_length_mm": D435I_RGB_FOCAL_LENGTH_MM,
    "width": 1280,
    "height": 720,
    "horizontal_aperture_mm": D435I_RGB_HORIZONTAL_APERTURE_MM,
    "vertical_aperture_mm": D435I_RGB_VERTICAL_APERTURE_MM,
    "sensor_model": "Intel RealSense D435i RGB / OmniVision OV2740 nominal specification",
    "horizontal_fov_deg": D435I_RGB_HORIZONTAL_FOV_DEG,
    "vertical_fov_published_deg": D435I_RGB_VERTICAL_FOV_PUBLISHED_DEG,
    "vertical_fov_simulated_deg": D435I_RGB_VERTICAL_FOV_SIMULATED_DEG,
    "pixel_aspect_ratio": 1.0,
    "projection": "centered_rectilinear_pinhole_no_device_distortion",
    "specification_source": "https://www.realsenseai.com/wp-content/uploads/2022/03/Intel-RealSense-D400-Series-Datasheet-March-2022.pdf",
})


def rotation_matrix(q):
    """Quaternion XYZW to local-to-parent rotation matrix."""
    q = np.asarray(q, dtype=np.float64)
    if q.shape != (4,) or not np.isfinite(q).all() or not np.isclose(np.linalg.norm(q), 1., atol=1e-5):
        raise ValueError("Expected finite unit XYZW quaternion")
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def camera_world_transform(root_xyzw, view):
    """World XYZ and world-convention axes (+X forward, +Y left, +Z up)."""
    root = np.asarray(root_xyzw, dtype=np.float64)
    if root.shape != (7,) or not np.isfinite(root).all():
        raise ValueError("Expected finite XYZ/XYZW root pose")
    mount = CAMERAS[view]
    rotation = rotation_matrix(root[3:])
    return root[:3] + rotation @ mount["position"], rotation @ rotation_matrix(mount["rotation_xyzw"])
