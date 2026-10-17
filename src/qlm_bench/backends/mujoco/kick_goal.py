"""Measured sphere/physical goal geometry; independent of action and data schemas."""
import numpy as np


def goal_coordinates(position, goal):
    point = np.asarray(position, dtype=float) - np.asarray(goal['front_center_xyz_m'])
    yaw = float(goal.get('yaw_rad', 0.))
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([c*point[0]+s*point[1], -s*point[0]+c*point[1], point[2]])


class GoalEntry:
    """Latch only a forward mouth crossing, then require the whole ball inside.

    Updated once at the existing completed50Hz boundary. Repeated state reads
    never advance this predicate. Initial-inside, side and back entry do not count.
    """
    def __init__(self, goal, radius):
        self.goal, self.radius = goal, float(radius)
        if self.radius <= 0 or min(goal['width_m'], goal['height_m'], goal['depth_m']) <= 2*self.radius:
            raise ValueError('A physical goal must fit the entire ball')

    def reset(self, position):
        self.previous = goal_coordinates(position, self.goal)
        self.started_in_front = self.previous[0]+self.radius < 0.
        self.entered = False
        self.last_tick = None

    def update(self, tick, position):
        if self.last_tick is not None and tick <= self.last_tick:
            raise ValueError('Goal predicate needs a fresh completed boundary')
        point = goal_coordinates(position, self.goal)
        if not np.isfinite(point).all():
            raise ValueError('Finite measured ball position required')
        radius = self.radius
        if self.started_in_front and self.previous[0] <= 0 < point[0]:
            fraction = -self.previous[0]/(point[0]-self.previous[0])
            crossing = self.previous + fraction*(point-self.previous)
            self.entered = bool(abs(crossing[1])+radius <= self.goal['width_m']/2
                and crossing[2]-radius >= -self.goal.get('floor_tolerance_m', .003)
                and crossing[2]+radius <= self.goal['height_m'])
        # Moving back out requires a new valid forward crossing.
        if point[0]+radius < 0:
            self.entered = False
        inside = bool(point[0]-radius >= 0 and point[0]+radius <= self.goal['depth_m']
            and abs(point[1])+radius <= self.goal['width_m']/2
            and point[2]-radius >= -self.goal.get('floor_tolerance_m', .003)
            and point[2]+radius <= self.goal['height_m'])
        self.previous, self.last_tick = point, int(tick)
        return bool(self.entered and inside)
