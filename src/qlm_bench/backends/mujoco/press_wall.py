"""Explicit wall-mounted Press geometry and closed-convex cap inertial properties."""
import numpy as np
from scipy.spatial import ConvexHull


WALL = {'front_x_m': 0.7297601848840714, 'center_y_m': 0.,
        'width_m': 6., 'height_m': 2.4, 'thickness_m': .12}


def wall_mount_translation(bounds, y, z, wall=None):
    """Back surface remains on the fixed wall plane when Y/Z placement changes."""
    wall = WALL if wall is None else wall
    low, high = np.asarray(bounds, dtype=float)
    if low.shape != (3,) or high.shape != (3,) or not np.isfinite([low, high]).all() or np.any(high <= low):
        raise ValueError('Finite nonempty source bounds required')
    if not np.isfinite([y, z]).all():
        raise ValueError('Finite in-plane coordinates required')
    half_width = max(abs(low[1]), abs(high[1]))
    if abs(y - wall['center_y_m']) + half_width > wall['width_m'] / 2 - .02:
        raise ValueError('Button extends beyond the wall edge')
    if z + low[2] < .02 or z + high[2] > wall['height_m'] - .02:
        raise ValueError('Button intersects floor or extends beyond the wall top')
    return np.array([wall['front_x_m'] - high[0], y, z])


def convex_mass_properties(parts, mass):
    """Uniform density over disjoint convex source components; exact tetrahedral integrals.

    Component gaps remain gaps. This does not merge cap and stem into one hull.
    Overlap must be excluded by the caller's source-geometry inspection.
    """
    if not np.isfinite(mass) or mass <= 0:
        raise ValueError('Positive finite total cap mass required')
    volume = 0.; first = np.zeros(3); second = np.zeros((3, 3))
    for points in parts:
        points = np.asarray(points, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
            raise ValueError('Finite 3D source vertices required')
        hull = ConvexHull(points)
        for indices, equation in zip(hull.simplices, hull.equations):
            a, b, c = points[indices]
            if np.dot(np.cross(b - a, c - a), equation[:3]) < 0:
                b, c = c, b
            v = np.dot(a, np.cross(b, c)) / 6
            s = a + b + c
            volume += v
            first += v * s / 4
            second += v * (np.outer(s, s) + np.outer(a, a) + np.outer(b, b) + np.outer(c, c)) / 20
    if volume <= 0:
        raise ValueError('Positive closed volume required')
    center = first / volume
    covariance = second / volume - np.outer(center, center)
    inertia = mass * (np.trace(covariance) * np.eye(3) - covariance)
    if np.linalg.eigvalsh(inertia).min() <= 0:
        raise ValueError('Positive definite inertia required')
    return {'volume_m3': float(volume), 'mass_kg': float(mass),
            'center_m': center.tolist(), 'inertia_kg_m2': inertia.tolist()}
