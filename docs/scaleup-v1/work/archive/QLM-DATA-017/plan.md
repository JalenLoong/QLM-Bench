---
id: QLM-DATA-017
type: exec-plan
status: completed
source_map: []
---

# Press Button资产与高质量reference

## Purpose / Big Picture

在当前MuJoCo分支准备Press Button可审核主资产与一条真实FL高质量reference。用户批准Push100后授权下一task；选择Press因为原industrial-button来源/许可和动态关节已具备，不需先引入新资产。旧Isaac任务顺序/QLM-DATA-001..010分支预留保留历史身份，不复用其ID。

## Scope / Non-goals

核对primary＋最多2backup真实状态、来源/license/hash、geometry/collision/mass/friction/滑动弹簧；单world实际CUDA-MJWarp＋原RAMBO/native9；成功PhysicalTrace，Native OSMesa按同timestamp离线渲染；动作连续性、FL/机身接触证据与原success分别报告。补充一份stage/template描述及task-specific retarget范围建议，范围在pilot前冻结。不运行正式10-pilot/100生产、其他task、训练、AMD、WAM重复检查、commit/push或发布。

## Context and Orientation

source: repos/QLM-Bench-mujoco on migration/mujoco-foundation。复用runtime/core/ExpertAdapter/collect_trace/RenderMirror/VideoSink，原资产assets/mujoco/original-press_button-v1-step-rig-lod-a02/保持不可变。原PressSuccessHold为12mm轴向位移、not-fallen、三个50Hz ticks，24s horizon，不要求release。reference开发样本不计formal quota。QLM现有offline Raw producer包含Push专用字段，不能未经task适配直接给Press使用；本阶段使用独立reference媒体worker，正式producer适配在reference批准后的pilot工作中完成。

## Milestones / Progress

- [x] 接收Push100批准，确认现有工程来源、注册工作。
- [x] primary资源字节/许可与物理机构检查；backup仅登记真实状态。
- [x] 新wall nominal真实reference及backup操作诊断完成，未修改controller/冻结physics。
- [x] OSMesa完整snapshot媒体/terminal、行为审视、stage/template及四角点范围技术验证完成。
- [x] 提交可观看review与阶段报告。
- [x] 用户批准资产与墙面Y/Z范围。
- [x] 用户明确批准新reference动作质量。

## Decision Log / Discoveries

Press source许可为现有CC-BY-4.0声明；原作者与embedded USDZ作者差异保留双署名。新MuJoCo profile不宣称与旧Isaac资产级全等。现有按钮为真实slide joint，被动spring actuator模拟原300N/m、8Ns/m、40N限幅，不施加辅助操作力。不能把source engineering acceptance当作formal task asset/reference approval。

## Validation Plan

source/static：确认env实际导入当前QLM源码，保护Push100/原controller/模型包；affected CPU/docs/import检查。实际资源：完整manifest hashes、关节行程/质量/弹簧/接触配置及隔离被动回弹诊断(不计demo)。实际reference：完整command确认、50Hz边界、terminal，原predicate成功、不跌倒，分开报告FL可见操作/其他link接触/continuity。实际render：640×36050FPS双视角、720p25FPS Observer，完整articulation snapshot、mirror不推进physics，不加载controller/WAM。WAM本阶段not_run，task级一次检查留到合格pilot入读路径。

## Idempotence / Recovery

证据根workspace runs/audit/press-reference-20261014-v1/。每次实际attempt独立ID/source/config/hash；先最多3次reference开发执行(单次24s或terminal)，失败只轻量结果；有系统错误先修复，不无限换seed，不按失败缩小正式范围。成功trace独立render retry，不重跑physics。超出当前预算只有必要、明确针对高层reference的修复才增加，先记录理由；controller/physics/contract/任务语义重大变化集中报告。原批准Push100/source snapshot/历史attempt不改写。

## Outcomes & Retrospective

当前formal Press=0，reference与retarget用户审核pending。完成媒体和报告后保留active等待审核；批准后另行进入10-pilot，再审核后扩100。

## 资产实际检查与runtime初始化记录

92项portable closure依赖逐字节通过，accepted resource identity保持；CC-BY-4.0及双署名保留。button slide0..20mm、0.1kg、300N/m＋8Ns/m、40N限幅、zero spring gain及0 equality constraints通过。独立被动回弹fixture从16mm回到约8.18e-11m(0.5s、zero control)，明确不是reference/demo。原asset pack未修改。

首轮asset import遗漏bundled OSMesa库路径，已复用既有render_environment；reference-a01沙箱CUDA不可见、0 physical intervals，完整初始化失败日志保留；同seed同profile的reference-a02使用用户已授权host GPU正在运行。

## 最新steering：先资产确认，停止reference推进

用户明确先看候选虚拟资产。当前新stop gate为asset approval，pending。A industrial-button(红)，B industrial-button-blue(同几何蓝色)，C emergency-button-red(急停蘑菇头)；源资源许可/hash必须可核对，B/C未取得MuJoCo physics资格。只做静态audit rendering，review camera不属于policy camera、不改变runtime相机。

reference-a02于新要求到达前实际成功，501actions、502boundaries、10.02s、终态15.084mm、原predicate通过/no fall；captured runtime与独立snapshot几何各15个FL-cap接触边界，其他geom-cap0；几何重建不冒充CUDA force telemetry。OSMesa完整capture已结束，现有VideoSink partial media保留，后续full validator/finalization待资产确认后继续；没有再执行reference。新physics attempts停止，正式Press=0。reference-a01是沙箱GPU初始化失败0interval，不计真实尝试。

- [x] 原primary准备及1条工程诊断执行/capture，先前授权范围内，未计正式。
- [x] 收到asset-first steering，停止后续reference/正式采集。
- [x] A/B/C候选外观与尺寸页面交付；用户确认primary/backup仍pending。
- [ ] 资产批准后复核/开发选定profile的高质量reference及适用范围，提交第二gate。

资产审核页面为workspace runs/audit/press-reference-20261014-v1/asset-review/review.html，9个静态视角、源manifest所有文件逐字节校验通过。A/B为同几何红/蓝工业按钮(约16.98×17.89×17.89cm)，C急停按钮(约11.48×12.38×12.38cm)；cap直径均约8.85cm，缩放沿用已有source wrapper。初版视角实际显示后侧/照明过暗，保留v1并用独立review-only-v2修正到真实正面，不涉及runtime资源。资产选择pending；没有新reference执行。

## 最新批准：三资产与完整墙面

用户已批准A/B/C并要求backup均通过MuJoCo physics，明确把Press场景变更为整面物理墙。asset approval gate已通过，当前继续QLM-SIM-016的wall profile/physics qualification及本D017的高质量reference准备。randomization以墙面Y/Z位置为定义；X安装深度固定。旧无墙reference只保留历史开发身份，不能原样计入新wall正式pilot。reference用户审核仍pending，正式10/100仍0。

## 实际工程交付完成

A/B/C各自Native/CUDA静止、真实接触按压/回弹、正常/高速wall collision、有限行程、zero-step selected-lane reset、其他world不变与完整articulation镜像通过。三个原RAMBO/native9 nominal实际成功：A/B各501actions10.02s，C571actions11.42s；cap终态分别15.086/15.084/14.294mm，原predicate通过、无跌倒。旧Source pack/robotbody/joint/camera/solver逐字段保护检查通过，无额外equality constraints或辅助操作力。

主资产A墙面Y0.10±0.03/Z0.30±0.02m四个预声明角点全部成功，ap_00/ap_01非visual参数逐字节一致；range proposals仍等待用户审核。21路原始媒体/7个三视角preview/独立慢放及完整snapshot review交付，主资产/四角点other-geom-cap/wall/housing均0；C仅1个FL-housing边缘接触，非机身操作，不改task outcome。

QLM回归沙箱147pass/12skip、4socket权限失败；同四项host复核4pass，合计151pass/12skip。Docs/shared治理/import/compile/原资源保护通过。首轮wall stress guard失败及source-compliance分析保留；未改solver。七个真实task trace源码逐hash保存165个去重blob，原model_2000与旧Push100/receipt保持。

当前Press默认模型切换为新full-wall A resource pin，LOD a02保持；旧显式model/历史cases不改写或冒充新scene资格。无formal pilot/100、WAM模型验证、训练、AMD、commit/push或发布。本SIM技术资格完成并归档，QLM-DATA-017保持active等待reference动作质量与适用范围用户审核。证据与review见workspace runs/audit/press-wall-qualification-20261014-v1/。

本DATA保持active：上述是技术交付，不是user quality approval。下一步仅等待既定reference审核，不无限增加诊断、启动10/100或生成WAM缓存。正式Press Raw/Canonical producer仍需在获批后的pilot工作中去除Push专用绑定，不能直接把参考媒体当formal dataset。

## 2026-10-15：资产/墙面范围通过，旧reference动作质量未通过

用户明确批准墙面Y/Z随机化与三资产，冻结y0.10±0.03/z0.30±0.02m、固定normal深度与现有ap_00/ap_01；没有批准旧reference动作。用户指出推进中操作腿肘部大幅抖动，授权修复并重新实际生成一条reference。formal Press仍0，不进入10pilot/100。

旧trace离线分析：推进段FL hip roll实际范围约92.85deg，原IK reference最大10ms跳变13.65deg，实际最大10ms跳变8.59deg，底座vx近零切换31次。肘部横向摆动与此一致；需检查原IK workspace敏感性、world目标/body姿态及高层启停耦合，不能靠视频平滑掩盖真实执行。

当前工作在同一QLM-DATA-017中继续，审计根workspace runs/audit/press-reference-smoothing-20261015-v1/。新版本high-level executor采用低位body-relative收腿推进，先稳定底座，再缓慢伸向按钮；原native9接口保持，通过原IK/FK只读几何限制reference变化和可达空间，不改RAMBO内部history/checkpoint/PD/QP/IK算法、physics/camera/task predicate或已批准资产/范围。最多先3个明确recipe开发attempt，每次24s-or-terminal；失败轻量结果，成功trace可独立render retry。若必须改变原controller再集中报告，不以重新训练为默认。

验收：相同seed42/model/predicate下实际success/not-fallen、complete commands/terminal；对比推进段真实FL hip/thigh/calf与IK/desired角度波动、变化速度及末端轨迹，不用任务成功代替质量。完整OSMesa原始50FPS双RGB/Observer25FPS和原/新三视角对照交用户再次审阅。新recipe必须在正式pilot前针对已批准范围重新验证，批准范围不撤回、不偷偷缩小。WAM task-once检查仍not_run，不生成验证cache，不做训练/AMD/commit/push/发布。

## Smoothing attempt001实际发现 — 2026-10-15

原推进命令的100Hz body-frame目标位于原FL IK hip-circle内部：YZ radicand为负(最小-0.00679、median-0.00513m²)，加上body姿态摆动与31次vx启停，解释大幅hip roll/肘部横向摆动。新recipe使用body-relative低位carry、先对齐base、后稳定伸腿，并只对native9高层point做原IK/FK几何projection/rate限制，原controller不改。

reference-a01真实24s timeout/no fall，未press；P型base目标跟踪有约2cm lateral稳态误差，使8mm对齐条件无法满足，失败仅轻量结果/每秒诊断，未保存失败PhysicalTrace或媒体。第二版本在high-level base反馈加入有界Y积分与0.2s观测平滑，X仍P控制；velocity slew/原history/physics不变。原失败/source版本保留。不通过换seed、移按钮或缩范围解决。

## 2026-10-15实际reference修复交付

资产与墙面Y/Z范围已批准，旧reference动作质量未通过。成功的新reference-a02真实697actions/698boundaries、13.94s、终态cap18.572mm，原12mm/三个50Hz ticks/not-fallen判据通过，33个FL-cap boundary、其他geom-cap/wall/housing0。仅改high-level native9轨迹：低位body-relative收腿推进、平滑base速度、有界横向误差补偿、稳定后缓慢伸腿按压与几何reference slew；原RAMBO checkpoint、IK/PD/QP/history、physics/camera/资产/范围均未改。

推进段实际FL hip roll摆幅92.846→4.878deg(下降94.75%)，最大10ms跳变8.588→0.752deg(下降91.24%)；IK最大10ms跳变13.654→0.687deg。导致肘部横向大摆的主因改善，原gait的小幅thigh/calf波动仍在；完整三关节指标/曲线公开，不宣称所有关节振动消失。原/新推进video均1×实际速度，仅短段终帧padding；完整三视角preview未做动作动画平滑，原双RGB50FPS/Observer25FPS经过现有full media validator，Native mirror不推进physics。

第一次新recipe在base横向约2cm稳态误差下24s timeout/no fall，轻量日志/source保留，无失败完整trace/媒体；第二次加入高层Y积分和0.2s反馈平滑后成功。未换seed、移资产或缩范围。15项受影响CPU/geometry/quality checks通过，docs/import/shared治理及controller/旧evidence保护通过。

新审核包workspace runs/audit/press-reference-smoothing-20261015-v1/review.html。QLM-DATA-017保持active，只等待新reference动作质量审核；已批准的Y/Z范围不重问。new recipe在正式pilot前须重验该范围，然后进入10pilot审核；当前formal Press=0，未执行WAM/训练/AMD/commit/push/发布。

## 用户审核通过与下一工作 — 2026-10-15

用户批准新reference，资产/范围先前已通过；审批receipt在workspace runs/audit/press-formal-pilots-20261015-v1/approval.json。DATA017完成并归档；QLM-DATA-018先重验frozen新recipe在既定四角范围，再完成10formal pilots，pilot审核前不扩100。旧recipe.json/past receipts不改写。
