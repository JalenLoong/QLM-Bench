"""Components shared by RAMBO's quadruped tasks."""

from importlib import import_module


def __getattr__(name):
    if name in ('create_front_rgb_camera', 'make_front_rgb_camera_cfg'):
        return getattr(import_module('.camera', __name__), name)
    if name == 'ContactGenerator':
        return import_module('.contact_generator', __name__).ContactGenerator
    raise AttributeError(name)

__all__ = ["ContactGenerator", "create_front_rgb_camera", "make_front_rgb_camera_cfg"]
