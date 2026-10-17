---
id: QLM-DATA-020
type: change
status: completed
source_map: []
---

# Lift Basket获批资产与高质量reference准备

## Purpose / scope

下一task为Lift Basket。本轮只核对现有OASIS几何/来源，准备至多三个候选资产的真实Native MuJoCo静态外观、接触表示、尺寸和provenance。建议一个primary、最多两个backup；角色和资产仍待用户批准，不把几何检查冒充动态物理资格。

## Contracts / non-goals

保持原FL真实接触举升、整个basket最低点离地>=2cm、not-fallen及三个50Hz ticks，native9/force-zero/原RAMBO、500/100/50Hz、dual-rgb-360p-v1、OSMesa与LOD a02。仅审核取景可自由调整，正式camera不改。自建候选保持原量级提手孔，任务难度须实际验收，不得通过更换资产简化任务，候选质量和物理适用性须在资产批准后实测。OASIS独立资产包许可未确认，不能把repo MIT自动赋给mesh/texture。新资产使用新身份，不覆盖旧pack/default/model。

资产审核→物理验收及高质量reference/retarget范围审核→10pilots(2Clean/8Randomized alltrain)审核→补至100及最终验收。初始静态阶段不执行mj_step/CUDA/controller。2026-10-15资产获批后允许实际Native/CUDA物理资格与原RAMBO高质量reference；仍不执行formal pilot/100或WAM验证，不训练/AMD/发布/commit/push。每task WAM一次正式兼容性仍留pilot阶段，不用旧三任务engineering证据代替。

## Progress

- [x] 2026-10-15 核对Press100已获用户最终验收，选择下一个原三任务Lift Basket。
- [x] 2026-10-15 A原OASIS及B/C独立Native方篮共三候选、各五视角静态预览交付。
- [x] 2026-10-15 用户批准候选资产并指定A OASIS编织篮为primary，B/C为backup。

## Discoveries / decision log

OASIS已有MuJoCo engineering pack、原cooked collision和0.53kg质量可作几何参考；旧source license unknown不改写。Native自建替代属于候选，不是冻结的dataset asset pool。主线语义/控制器无变化。每个backup只登记真实状态，不要求使用配额。

## Validation / recovery

核对模型compile、资源hash与依赖闭合、真实静态render；记录0physics steps/0new trajectories。静态预览不等于物理行为通过。完成doc/import治理校验，保护旧数据、receipt、源码、default和HEAD；候选只写新audit目录，回退不删旧证据。

## Outcomes

待静态审核包交付与用户资产确认。证据目录workspace runs/audit/lift-asset-review-20261015-v1/。未启动reference或数据合成。

## 候选准备实际交付

候选A保留原mesh/cooked hulls但asset包许可未确认；候选B/C自建单中央提手，质量0.53kg/轮廓27.6×24.7×28.2cm、几何派生惯性。建议Bprimary/Cbackup，A条件备选，不把角色建议写成已批准pool。15路NativeOSMesa静态views，0physics/controller/reference/trajectory，model compile与图片decode/依赖hash通过；完整证据workspace runs/audit/lift-asset-review-20261015-v1/。当前只等待资产审批，后续物理行为/难度资格和reference均not_run。

## 2026-10-15用户审批后的当前执行范围（覆盖早期静态停点）

资产gate已通过，A primary/B/C backup，不重新挑选资产或要求backup使用配额。QLM-SIM-017负责针对性Native/CUDA资产物理资格，复用P0–P2原primary geometry/mass/friction/solver；QLM-DATA-020继续原expert nominal真实reference与动作质量分析。最多先3个24s-or-terminal recipe诊断attempt，保留负结果/失败轻量日志；成功完整PhysicalTrace可离线重渲染。若需较大controller/physics/camera/predicate改变则停下报告。

新scope不把visual审批当动态资格或asset license已确认。A可继续现有本地工程验证，资产包许可/固定获取资格仍在发布/AMD资源交付前闭合，不上传。WAM模型不加载，task一次正式资格留pilot阶段。原success/50Hz边界/必要snapshot/command confirmations/terminal保持；高频diagnostic仅为明确reference质量分析，不能推广为所有成功demonstration永久存储。

reference阶段先真实task success且notfallen/完整terminal，再分析FL hip/thigh/calf、native目标/实际足端与Base协同和穿孔证据；unknown contact不硬失败，Native at-CUDA-state contact明确不是CUDA force telemetry。retarget范围要声明并验证，失败不偷偷缩小。针对原篮体初始XY/小yaw与两个Background形成提案，在reference审核时确认，不引入OOD或区间割split。

- [x] 2026-10-15 A/B/C Native/CUDA被动物理资格与完整snapshot同步通过。
- [x] 2026-10-15 三个成功recipe开发attempt全部保留；推荐a03真实770actions，八角点成功及full media交付。
- [ ] 用户reference和范围审核。必须停在此gate，不执行10pilot/100。

审计workspace runs/audit/lift-reference-20261015-v1/；资产批准receipt为asset-approval.json。原静态审核包保持immutable，不原地改成approved receipt。

## 工程交付完成，当前只等reference审批

## Lift Basket A reference交付；等待动作质量与范围审核 — 2026-10-15

A原OASIS编织篮为用户指定primary、B/C为backups。QLM-SIM-017的Native/CUDA被动物理资格三资产均通过；A原RAMBO实际高层recipe lift-body-lane-geometry-v2完成770actions/771boundaries、15.40s success/not-fallen，整篮最低点30.848mm，原20mm/三50Hz ticks判据未改。完整足端先穿孔后托举；实际snapshot几何为FL腿部接触38boundaries、base/其他腿0，sphere-only FL接触为0不直接拒绝。

原expert抬腿/伸腿hip最大10ms约5.3deg，推荐v2相应1.0–1.2deg、托举1.99deg；保留原gait及三成功开发trace，不宣称所有波动消失。仅高层Base/FL站位/轨迹连续性改变，原controller/IK算法/PD/QP/history/physics/camera/asset/default保持。预声明dx/dy±3cm、yaw±5deg八个product角点8/8实际成功，无重试/收缩，完整穿孔后托举/base-contact0；范围是proposal仍待用户批准，不是policy SR或全部seed验收。

完整NativeOSMesa双640×36050FPS/Observer1280×72025FPS及terminal验证通过，完整同timestamp snapshot镜像未推进physics；两个Background只换floor外观，非visual/camera/solver完全相同。主render507.4s/15.4s simulation（非稳态生产吞吐保证），scope2physics实际并发总820.1s，无guard，最低available6.97GiB/maxswap增长212.32MiB。范围trace是非formal geometry诊断，早期nominal task.goal.XY配置偏移元数据不提升为正式data；未来入口已用既有episode-goal overlay对齐初态XY，实际Native零步检查仅goal字段变、物理和其他state不变，旧trace不改写。

审核workspace runs/audit/lift-reference-20261015-v1/review.html与report.md。QLM-DATA-020保持active等待reference动作质量和范围审批，未批准前不10pilot/100。Lift正式0、Push100+Press100累计200/1000。WAM兼容性每task一次留pilot，本轮未加载WAM/checkcache/fit/训练/AMD/commit/push/发布；A asset包license unknown待资源交付前核实，未因视觉审批改写。


目标初始化XY元数据对offset模型曾保持nominal配置的诊断发现独立记录episode-metadata-correction.json；未来入口使用已存在public goal overlay对齐初态，仅配置值变不改schema/physics/predicate。实际CPU Native runtime零步验证passed，旧diagnostic不改写，不提升为formal data。11pass/1skip作用范围CPU checks、shared/v3治理通过；原623文件及三个HEAD保持。最终docs/link/sourceblob检查见completion.json。

## User reference/scope approval — 2026-10-15

用户明确批准review及既定范围，授权进入10pilot并尝试4physics+4render。新批准receipt在workspace runs/audit/lift-formal-pilots-20261015-v1/approval.json。原reference receipt不改写。DATA020按既定gate归档，QLM-DATA-021负责十条formal pilots；用户尚未批准pilot质量，不扩100。
