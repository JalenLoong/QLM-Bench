---
id: RGB-RESOLUTION-360P
type: decision
status: accepted
related_work: [QLM-DATA-012]
source_map: [src/qlm_bench/backends/mujoco/render.py]
---
# Versioned policy RGB 640×360

用户于2026-10-14明确授权仅降低两路 policy RGB 空间分辨率。QLM-DATA-012、v2/DATA-014、v3/DATA-004 同等覆盖 producer 与两条 consumer。治理记录和诊断验收不授权正式合成、训练、AMD、发布、commit/push。

## 接口与兼容性

`dual-rgb-360p-v1`：go2_ego/d435i_rgb_task 640×360，intrinsics 前两行×0.5；原 FoV、projection、mount、extrinsics、physics/资源不变。Observer 原1280×720/25 FPS不变。OSMesa和实际CUDA-MJWarp保持。

原始RGB/action 50Hz、controller100Hz、physics500Hz；Raw N+1、Canonical N、terminal独立，不引入12.5FPS原始视频。H.264/CRF/preset/GOP/BT709/CFR参数保持。新空间profile/hash派生于原冻结bundle，旧spec JSON/lock/hash不变；不混合不同空间profile的collection。

WAM继续每4帧采样（12.5Hz）；640×360→bilinear/antialias320×180→上下各6pixel黑色padding→320×192→原frozenWan2.2CausalVAE；dual-view latent [B,48,T,24,20]。v2 video/action、v3 video+10D/action保持各自协议。两条Reader由dataset profile_hash选择preprocessing；新cache使用各自的新hash，并拒绝旧hash。历史stage2和checkpoint训练preprocessing保留720p。

## 使用新版输入

QLM MuJoCoRuntime和record_trace的新默认是`dual-rgb-360p-v1`；历史RenderMirror直接调用保留720p，明确指定rgb_profile可对比/重建。VideoSink/Raw转换按声明profile编码/验证；Observer单独保留原尺寸。

v2 online config在`resources.rgb_profile`选择`dual-rgb-360p-v1`；v3 online config在根`rgb_profile`选择同值。未指定时保留旧720p，避免静默更改旧checkpoint的输入身份。新runtime同时记录`input_preprocessing_sha256`和旧checkpoint训练`preprocessing_sha256`，不重新标记历史训练。完整本地可复核配置在本次audit目录v2-inference.json/v3-inference.json。

## 验收与边界

Actual同状态三边界六视角比较，frustum/pose差值0，Observer逐像素相同；360p policy RGB实际shape[360,640,3]。实际MJWarp诊断101actions/102boundaries，Raw/Canonical/terminal/MP4通过。两条Reader/frozenVAE实际输出[1,48,7,24,20]，在线initial+ordinary feedback与离线前两组完全一致；v3状态时间保持80ms间隔。

完整回归及两个原正式step1000 checkpoint的strict-load/actual360p初始输入backbone commit均通过；最终报告在workspace`runs/audit/rgb-resolution-360p-20261014-v1/`。不把输入兼容性视为新规格下的policy performance。完整Slurm/full SFT、policy action rollout/SR未运行；原50episode/40-5-5训练admission保持，不把诊断数据冒充正式训练输入。

旧十条720p Push Box pilot及其cache、视频、checkpoint身份保持，仍待用户审核；不会重写为360p。后续正式360p合成须使用新的输出层与身份，旧pilot不取得360p正式验收。

旧发布CPU wheel未重建；当前360p执行需绑定更新后的QLM source及对应WAM route，保留旧安装/lock绑定。
