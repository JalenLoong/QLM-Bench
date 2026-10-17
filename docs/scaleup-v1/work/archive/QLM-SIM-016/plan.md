---
id: QLM-SIM-016
type: exec-plan
status: completed
source_map: []
---

# 三资产Press墙面场景与MuJoCo物理资格

## Purpose / scope

用户批准A工业红(primary)、B同几何工业蓝和C急停红(backups)整批资产，要求两个backup也完成MuJoCo物理验收，并新增一整面真实墙壁；按钮随机化在墙面平面内。继续当前reference阶段，不生成formal pilots/100。

新profile独立版本化：source mesh/texture/license/hash保留；原A包、旧无墙reference、Push100和既有source receipts不改写。A/B尽量逐字节复用原robot/collision/cameras；C沿用已批准源几何/缩放与既有convexHull机制，明确记录其新的MuJoCo inertia/collision profile与验证，不冒充原PhysX完全等价。

## Contracts / frozen semantics

原native9/RAMBO/force-zero、500/100/50Hz、dual-rgb-360p-v1、Observer720p25FPS、OSMesa、LOD a02保持。Press为真实FL接触按压，20mm行程、300N/m+8Ns/m被动弹簧40N限幅、12mm成功阈值、三个50Hz ticks且not fallen、24s horizon；不引入急停latch/twist/release。墙面为法向X、宽6m/高2.4m/厚0.12m的固定碰撞box；无隐形辅助力/constraint，source按钮背面贴墙固定，允许Y/Z变化；不沿X漂浮或每episode改变wall。

## Milestones / Progress

- [x] 记录用户资产审批与墙面环境决定，注册独立QLM-SIM-016；QLM-SIM-015仍退役。
- [x] 三个portable wall-mounted资产包、来源/license/hash、真实滑动和collision/inertia检查。
- [x] Native/CUDA无接触静止/真实碰撞按压/回弹/限位/zero-step reset与mirror检查；A/B/C实际原RAMBO FL nominal诊断。
- [x] A高质量wall reference与Y/Z retarget开发范围证据由QLM-DATA-017交用户审核；不偷缩范围。
- [x] CPU/docs/import/完整媒体验证，物理报告与治理归档，D017保留reference审核gate。

## Validation / risk

静态：全部资源closure/许可/碰撞机制和source protected参数差异。机构诊断：独立free striker只有预声明初速，通过真实contact驱动cap，不控制物体qpos或施加外力；它是physics fixture不是demonstration。Native/CUDA分别测行程、阈值、回弹、有限状态及reset。任务动作诊断：每资产至少一次实际原RAMBO/native9 FL操作、原success通过、可靠接触与非FL依赖证据、terminal/command确认。几何碰撞重建与实际CUDA force来源分开。

资产外观批准不自动赋予physics通过；一次nominal成功不宣称全部retarget范围通过。大墙可能引入body/wall碰撞、影像遮挡或接触容量风险，必须在新场景验证；user已经明确授权此环境分布变化，不改旧任务success/动作/相机接口。

## Recovery / decision log

审计根workspace runs/audit/press-wall-qualification-20261014-v1/。成功PhysicalTrace独立OSMesa replay，不因媒体失败重跑physics；失败轻量记录，development diagnostics不计formal配额。先各资产最多2个明确recipe的24s-or-terminal实际controller attempts，系统错误先修复；reference调参只在高层executor，不修改原controller。所有历史失败保留。WAM task-once检查留正式pilot，不执行训练/AMD/远端发布/commit/push。

## Source contact compliance与诊断guard修正

首次Native A wall fixture以0.6m/s撞击，实测瞬时穿入约4.50mm后回弹，超出初版脚本自定3mm阈值，原失败/partial rows保留。这不是source task/physics契约中的原验收阈值。固定原20ms compliant contact，新增0.15m/s正常速度测试(3mm guard)与独立0.6m/s stress(半FL半径11mm anti-tunnelling guard)，所有资产和Native/CUDA共用、在其余gate前冻结，记录实际penetration；不通过调solver或删除失败制造通过。Native正常速度约0.426mm，高速约4.50mm；CUDA正常约0.425mm、高速约3.65mm。原solver/camera/controller未变。

闭凸体质量积分测试初版expected表达式存在Python序列乘浮点错误，1fail/2pass；修正测试表达式后3pass，算法无需修改。

## 实际工程交付完成

A/B/C各自Native/CUDA静止、真实接触按压/回弹、正常/高速wall collision、有限行程、zero-step selected-lane reset、其他world不变与完整articulation镜像通过。三个原RAMBO/native9 nominal实际成功：A/B各501actions10.02s，C571actions11.42s；cap终态分别15.086/15.084/14.294mm，原predicate通过、无跌倒。旧Source pack/robotbody/joint/camera/solver逐字段保护检查通过，无额外equality constraints或辅助操作力。

主资产A墙面Y0.10±0.03/Z0.30±0.02m四个预声明角点全部成功，ap_00/ap_01非visual参数逐字节一致；range proposals仍等待用户审核。21路原始媒体/7个三视角preview/独立慢放及完整snapshot review交付，主资产/四角点other-geom-cap/wall/housing均0；C仅1个FL-housing边缘接触，非机身操作，不改task outcome。

QLM回归沙箱147pass/12skip、4socket权限失败；同四项host复核4pass，合计151pass/12skip。Docs/shared治理/import/compile/原资源保护通过。首轮wall stress guard失败及source-compliance分析保留；未改solver。七个真实task trace源码逐hash保存165个去重blob，原model_2000与旧Push100/receipt保持。

当前Press默认模型切换为新full-wall A resource pin，LOD a02保持；旧显式model/历史cases不改写或冒充新scene资格。无formal pilot/100、WAM模型验证、训练、AMD、commit/push或发布。本SIM技术资格完成并归档，QLM-DATA-017保持active等待reference动作质量与适用范围用户审核。证据与review见workspace runs/audit/press-wall-qualification-20261014-v1/。
