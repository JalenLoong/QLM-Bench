import mujoco

from leg_manip.assets.objects import button_panel_spec


def test_button_does_not_collide_with_its_own_housing():
    model = button_panel_spec().compile()
    data = mujoco.MjData(model)
    for displacement in (0.0, 0.01, 0.03):
        data.qpos[0] = displacement
        mujoco.mj_forward(model, data)
        assert data.ncon == 0
    button_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "button_geom")
    panel_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "panel_geom")
    # External contacts must stay enabled on both object geometries.
    assert model.geom_contype[[button_id, panel_id]].all()
    assert model.geom_conaffinity[[button_id, panel_id]].all()


def test_button_can_be_pressed_and_spring_returns_it():
    model = button_panel_spec().compile()
    model.opt.timestep = 0.005
    model.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    data = mujoco.MjData(model)
    data.qfrc_applied[0] = 5.0
    for _ in range(100):
        mujoco.mj_step(model, data)
    assert 0.005 < data.qpos[0] < 0.03
    data.qfrc_applied[0] = 0.0
    for _ in range(100):
        mujoco.mj_step(model, data)
    assert abs(data.qpos[0]) < 1e-4
