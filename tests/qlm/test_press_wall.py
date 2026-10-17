"""Inertia and mounting checks against independent analytical geometry."""
from itertools import product
import numpy as np
import pytest
from qlm_bench.backends.mujoco.press_wall import WALL, convex_mass_properties, wall_mount_translation


def test_translated_cuboid_inertia_matches_analytic_solution():
    sides = np.array([.04, .08, .12]); center = np.array([.19, -.04, .23]); mass = .1
    points = np.array(list(product(*[[-s / 2, s / 2] for s in sides]))) + center
    result = convex_mass_properties([points], mass)
    expected = mass / 12 * np.diag([sides[1]**2 + sides[2]**2,
                                   sides[0]**2 + sides[2]**2,
                                   sides[0]**2 + sides[1]**2])
    np.testing.assert_allclose(result['center_m'], center, atol=1e-12)
    np.testing.assert_allclose(result['inertia_kg_m2'], expected, atol=1e-12)
    assert result['volume_m3'] == pytest.approx(float(np.prod(sides)), abs=1e-12)


def test_disjoint_components_keep_parallel_axis_contribution():
    cube = np.array(list(product([-.01, .01], repeat=3)))
    result = convex_mass_properties([cube + [-.04, 0, 0], cube + [.04, 0, 0]], .1)
    np.testing.assert_allclose(result['center_m'], 0., atol=1e-12)
    own = .1 * .02**2 / 6
    np.testing.assert_allclose(np.diag(result['inertia_kg_m2']),
                               [own, own + .1*.04**2, own + .1*.04**2], atol=1e-12)


def test_wall_plane_mounting_is_preserved_for_different_asset_depths():
    for depth in (.17, .115):
        bounds = [[0, -.09, -.09], [depth, .09, .09]]
        for y, z in [(.1, .3), (.13, .32), (.07, .28)]:
            translation = wall_mount_translation(bounds, y, z)
            assert translation[0] + depth == pytest.approx(WALL['front_x_m'])
            np.testing.assert_allclose(translation[1:], [y, z])
    with pytest.raises(ValueError, match='floor'):
        wall_mount_translation(bounds, .1, .02)
    with pytest.raises(ValueError, match='wall edge'):
        wall_mount_translation(bounds, 3., .3)
