---
id: QLM-DATA-027
type: change
status: completed
source_map: []
---

# 剩余六task：批量候选资产审核

## 最新用户决定
流程具有两个整批人工gate：先审核剩余六task的全部候选资产；这批资产获批后，完成各task物理资格并各生成一条高质量reference及适用范围，六条集中交审。只有用户批准这整批六条reference/范围后，才按task顺序直接合成各100条；仅完成或批准其中一条reference不能先启动该task的100生产。

用户将剩余六task改为：全部候选资产先交审→资产批准后物理资格及各task一条高质量reference/适用范围交审→reference批准后按task顺序直接合成100，不再设十条pilot人工审核。此前已验收四task400条与source/recipe/data保持；新决定不回写旧pilot历史。100条全量检查、随机十条最终整task验收及每task一次WAM v2/v3兼容资格保持，后者移到100生产最初合格Clean＋Randomized工程准入（计入100），不新增人工pilot节点。

## 当前范围
sweep_block_to_zone、close_fridge_door、close_oven_door、turn_valve、pull_open_drawer、open_room_door。每task最多A primary proposal＋B/C backups，无使用配额。优先本项目独立参数化几何，原Go2/STEP rig/solver/camera只作尺寸和静态视图参考；不修改任何已批准旧asset、source/模型/env。真实block/zone、竖直与水平铰链门、单bar quarter-turn lever、prismatic drawer及足端可进入U把手、room door的真实lever/bolt/cam/strike框架全部必须出现在模型中。不能用teleport、辅助外力、FL焊接或逻辑开门代替交互。静态候选的尺寸/质量/摩擦/关节/handle开口仍是proposal，待用户批准后物理验收，不冒充难度或controller成功。

只生成Native compile/mj_forward/静态EGL真实像素和review，0physics steps/0controller/0reference/0formal数据。相机原接口及dual640×36050FPS/Observer720p25FPS不改；额外自由视角和关节初始姿态仅人工资产诊断，非正式数据。当前18个候选不要求asset级与旧Isaac等价；source/hash/license/版本和真实状态记录齐全。两Background、无clutter/强制Recovery、原native9/force-zero/RAMBO/500-100-50Hz、task success与quality分开、普通NativeCPU/EGL3+3/1GiB/7.6GiB/0.5GiB/4GiB新render保护保持。

## Progress / acceptance
- [x] 18个候选的独立几何、关节/contact机构、mass/inertia/friction/handle开口、来源/license/版本/hash说明。
- [x] 实际Native compile和零step数据姿态/静态EGL各task完整外观、操作细节、Go2比例参照视图；所有真实状态与未执行项。
- [x] 六task集中资产审核页已生成、治理同步；最终图片QA另列，用户资产审核pending。
- [ ] 用户批准各task的primary/backups及资产方案；批准前不physics/reference/100。

HF400发布由独立QLM-DATA-026和mujoco400-hf heartbeat收尾，不占用新task批准，不启动第二个上传写者。v2DOC-024/v3DOC-023只治理，当前不WAM/checkcache/fit/训练/AMD/source commit/push或新资产发布。

## 2026-10-15实际工程进度

18候选（每task A/B/C）均已Native compile＋mj_forward；72张NativeEGL静态图已生成，真实NVIDIA RTX5070Ti GL来源见workspace runs/audit/remaining-six-assets-20261015-v1/verification.json。全部六task overview与Room Door背面cam/bolt近景已实际检查；18模型resource identity、72图hash/尺寸及页面相对链接QA通过（workspace runs/audit/remaining-six-assets-20261015-v1/visual-qa.json），用户资产批准仍pending。原Go2 camera/inertia、独立资产inertia及parent resource identity保护通过；零step并不证明动态物理或可操作难度。

完整候选metadata含source/version/hash/license状态、mass/friction/joints/初始姿态/handle间隙/真实未验风险，审核页为workspace runs/audit/remaining-six-assets-20261015-v1/review.html。原4task400保持。physics steps/controller/reference/formal/WAM/cache/训练/AMD/source commit/push/新资产发布均未执行。Room Door实际cam/bolt解锁、Drawer真实hook、各关节动态及FL操作需要资产批准后另做资格，不以静态几何探查代替。

- [x] 18个独立候选及元数据/来源/动态未验风险。
- [x] Native compile/零step以及72静态像素实际生成，原资源及相机/惯量保护。
- [x] 六task集中review文件生成，当前table/consumer规则同步。
- [x] 主会话实际检查六task overview与门锁背面近景；visual-qa.json核对18模型resource identity、72图hash/尺寸及review相对链接通过。
- [ ] 用户资产批准；未批准前不physics/reference/100，QLM-DATA-027保持active。


## 2026-10-16用户资产批准
全部六task资产已明确获批，A primary/B-C backups。独立receipt为workspace runs/audit/remaining-six-reference-20261016-v1/asset-approval.json。原静态pending只保留历史，不改写旧review/metadata。后继QLM-SIM-020/QLM-DATA-028执行物理资格与六reference/范围集中交审，未授权100。
