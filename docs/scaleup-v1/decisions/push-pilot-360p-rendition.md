---
id: QLM-PUSH-PILOT-360P
type: decision
status: accepted
related_work: [QLM-DATA-014]
source_map: [src/qlm_bench/backends/mujoco/rendition.py, src/qlm_bench/backends/mujoco/replay_recording.py, src/qlm_bench/compatibility/dataset_v2/pilot_rendition.py]
---
# 十条360p Push Box pilot — 工程交付，等待用户审核

本轮仅从未改变的原十份成功PhysicalTrace重录新的360p rendition，2Clean/8Randomized、全部train；不新增物理demonstration数量。原physical source/scene/template/controller/trajectory身份保留，新renderer source/camera/encoding身份独立记录。冻结recording profile为63ee2d6c71b3aac8e13b63e89d806f97852ed1497061cf34b2db636fcca0916f，三条源码HEAD保持，实际未提交实现通过source文件hash和录制source snapshot追溯。

Raw/Canonical与完整媒体验收通过：双RGB640×360/50FPS、Observer1280×720/25FPS；action50/controller100/physics500Hz。4540actions、4550boundaries、独立terminal、无dummy action。原100/500Hz telemetry、action/state/terminal数值保持。FL接触、无body接触、full-footprint/not-fallen/three-tick成功条件通过；用户对动作质量的集中审核仍待完成。

v2和v3各实际消费完整Clean与Randomized样本：frozenWanVAE编码、独立cache identity/精确reload、原SFT flow输入准备，以及online初始RGB加四帧feedback输入均通过；dual latent为[1,48,28,24,20]。v3原10D body-frame state对齐、mask与timestamp保留。原1+4完整因果分组造成的末尾未成组样本仅在模型构建中按既有规则处理，Canonical数据不丢行。旧normalizers仅用于兼容性验证，未拟合新训练统计，cache明确标为compatibility readback而非training cache。

新queue仅负责render-only恢复，绑定原trace、单writer、payload重新验证、最多三次录制尝试；缺失输出不能沿用accepted计数。实际10/10均一次成功；失败恢复边界通过测试，不宣称发生了实际录制失败。没有physics/controller/WAM owner加载或physics stepping。原720p历史payload继续保持已清理状态，旧queue/checksum/provenance不改。

证据在workspace `runs/audit/push-pilot-360p-reconstruction-20261014-v1/`：review.html提供十条实际三视角预览和原双视角50FPS MP4；pilot-data-acceptance、original-telemetry-preservation、dual-wam-compatibility、throughput和completion记录验收与范围。吞吐只衡量offline rendition，不代表新candidate完整合成效率。

此阶段到此停止并等待用户审核；未扩100/其他任务、未训练/AMD/发布/commit/push，未验证policy performance或旧checkpoint在新分辨率下的性能等价。原Isaac/OPD、历史数据/weights/normalizers与P0–P2资源不改。

## 后续源码发布授权

2026-10-14用户明确批准相关已验收源码分别commit/push，完成情况由本次publication records与workspace receipt记录。上文not-run/local-only描述重录阶段本身，保持原证据范围。此批是同一个Box05的小范围pose/goal平移和轻微floor-color变化，尚未覆盖多资产pool或显著外观差异；pipeline工程验收不等于pilot动作质量或完整研究数据分布验收。
