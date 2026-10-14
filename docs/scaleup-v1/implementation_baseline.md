---
id: QLM-AUTOMATED-PUSH-BASELINE
type: guide
status: accepted
related_work: [QLM-DATA-011]
source_map:
  - src/qlm_bench/backends/mujoco/trace.py
  - src/qlm_bench/backends/mujoco/replay_recording.py
  - src/qlm_bench/backends/mujoco/template.py
  - src/qlm_bench/backends/mujoco/synthesis_queue.py
---

> 当前入口已于2026-10-14收束为360p/50FPS，见 `mujoco-workspace.md`（本目录或decisions/current）。下方720p产物、旧profile-v4和未发布状态均描述其原历史阶段；旧720p frozen profile不直接用于新版代码。清理receipt记录已evict诊断payload，旧10pilot/reference仍保留待审核。

# M0–M6 Push Box 实施基线

源分支 migration/mujoco-foundation 起点4cf1c643922ff1f479577f98d06c9e75518acc63；
WAM adaptation/v3-mujoco-sft 起点02939d121b127352a4a6178acb26e3ca30a5007d。
基于本地干净 worktrees 和已验收 Box05/default LOD a02，不恢复已撤销 P3 的资产或代码。
复用原 runtime/controller/physics/task predicate、Native mirror、VideoSink 与 Canonical exporter。

## 冻结范围

首轮同一 Box05、原 Go2/FL/native9/controller、force-zero、24s horizon；
goal 保持0.4m×0.5m矩形，full-footprint/not-fallen/three50Hz-tick判据不变。
随机化为物体X±4cm、Y±2cm、yaw±0.03rad、goal X±3cm/Y±2cm的小范围ID变化。
具体候选预先序列化完整初态、goal、seed与resource identity，不根据失败降为容易条件。
三套floor颜色preset为小幅外观变体，physics/camera/material摩擦均保持；源pack不可变。

工程reference由原nominal expert实际完成：444actions、8.88s，FL接触26个boundary且
无body-object接触。固定template提取commanded FL/world目标和measured base path；
阶段是settle/base approach/normal approach/straight push。执行时使用有界base/yaw反馈、
phase几何先决条件、固定操作progression与goal行程缩放，不逐candidate生成新脚本。
reference和调参开发数据不进入正式pilot quota。三项预定开发配置均实际成功。

## 生产入口与恢复

`qlm synthesize-pilot --profile FROZEN_JSON --output NEW_BATCH --checkpoint RAMBO`
使用显式资源/源码/template hash。首轮只允许10个Push slots，2Clean/8Randomized全部train。
最新profile在workspace `runs/audit/automated-push-synthesis-20261013-v1/pilot-profile-v4.json`。
Randomized目标边框四个contact-free geoms与数值goal共同冻结；仅修改视觉goal位置，
相机/机器人/物体collision和物理参数保持。两条nominal Clean保持原goal和原有效trace。
新versioned数据在workspace `data/qlm_bench/automated-push-pilot-20261013-v1/`。
一次冻结batch保存源码hash清单，不按episode复制source tree。

无渲染physics trace保留50Hz边界、100Hzcontroller和500Hzphysics/contact telemetry。
成功trace原子提交，失败只写轻量JSONL。Native OSMesa worker从完整snapshot离线出图，
不加载controller/WAM，不重新执行physics。源data与离线RGB的来源明确记录。
正式pilot必须task成功、complete interval、FL接触/无body操作、媒体/Raw/Canonical验证。

Queue单写入者使用文件lease；复用同model的已加载physics runtime；成功trace待录制时
阻止下一physics candidate，背压上限一条。每slot≤5候选、全pilot≤30、连续失败10条停止；
录制失败最多再试2次，复用同trace。restart验证trace及accepted inventory，幂等计数。
首轮采用单world和单render worker，容量优化不得先于per-world隔离验收。

## M6实际交付 — 2026-10-14

10条正式pilot（2Clean/8Randomized全部train）技术验收通过，用户审核待完成。
合计4540actions/4550boundaries，30路原始720p视频、10份三视角预览及完整串联均保留。
原资源/模型不变，Randomized goal视觉边框与数值区域一致；不恢复旧P3资产。
14physical attempts包括10成功、3timeout、1受控工程中断；11render attempts包括
10成功和一次受控中断恢复。成功trace未重跑physics，失败只轻量JSONL留档。

独立三tick footprint/not-fallen、去重hash、逐条/合并Raw/Canonical与实际LeRobot
逐episode首末RGB/native9读取通过。Clean01和Randomized03的原frozen VAE/10D
实际读取通过，latent1x48x28x24x20、state109x10；原weights/config hash匹配。
十条contact/terminal视图已检查，完整边界同姿态Native几何审计仅FL与箱子接触，
不代替CUDA实际力telemetry。未拟合normalizer或训练。

成功stage成本约35.05min、17.12accepted/hour；含失败/工程中断的实测batch约52.51min、
11.43accepted/hour。平均33.29MB/episode；组合worker RSS约8.08GB、GPU board峰值1417MiB。
不作为完整1000条生产容量或正式evaluation SR。已停在10条审核点。

## 验收与当前事实

参考离线Raw/Canonical和实际原frozen VAE/10D readback已通过。
固定模板开发配置443/462/457actions，三项成功。CPU回归14通过、5个显式runtime
fixture门槛skip；实际CUDA/OSMesa gates另记录。初次独立CUDA rollout逐bit比较出现
约4e-5速度差异，未放宽门槛；改在同一authoritative snapshot比较数值观测路径，并
核验physics/controller/RNG/clock零变化及双mirror图像逐byte一致，实际gate通过。

运行事实、failed轻量日志与milestone报告在对应audit层。M6完成后提交实际视频、
10条数据验收和吞吐/内存/磁盘成本，等待用户审核，不进入M7/其他任务/训练/发布。

最终诊断提取修正：settle段world目标从真实projected-COM转换推导，操作路径和fixed executor AST未改变。
实际pilot沿用template-development-v1身份，corrected display为template-display-v2，最终源码/profile可幂等恢复已accepted队列。
