---
id: OPD-V4-HF-DATASET-011
type: current-design
status: accepted
related_work: [OPD-011]
source_map: []
---
# HF dataset组织迁移 / OPD-011

当前网络地址为 `AIGeeksGroup/QLM-Bench`。只将已知旧地址 `dontKnow23456/QLM-Bench`
映射为该地址，不接受任意owner别名，也不在失败时回退旧owner。
QLM CLI默认值、publication目标和MuJoCo case获取，以及WAM snapshot download均使用新地址。
代码仓库仍是 `JalenLoong/QLM-Bench`，本次只迁移HF dataset，不改变GitHub来源。

原catalog、DataRef.repo_id/to_dict、SFT训练配置、发布过的release manifests和controller scope是已认证的历史身份，
保留原字节；否则会破坏step5000 checkpoint和已准备reset pool的绑定。
新增 `DatasetRef.hub_repo_id` 专用于HF网络地址；manifest/DataRef与private scope验证只认可这两个已知namespace的等价关系。
固定revision、release路径、split、payload hash及原模型repo保持不变；没有通过改hash绕过身份检查。

只读HF API实际验证main及4个历史revision仍可在新owner下解析，10个固定release manifests共1,415,990字节，
SHA256全部与原catalog一致。查询时dataset为public；本次没有修改远端可见性。
SFT step5000的header/binding检查通过，没有加载权重；原800-case pool完整资源/来源校验通过，manifest未改写。

CPU回归覆盖默认和显式legacy网络入口、已知别名与未知repo拒绝、原manifest/DataRef保留、旧inventory模拟发布及不回退旧owner。
WAM完整测试（连同OPD-012）255 passed/21 skipped；QLM完整tests/qlm与tests/qlm_bench为304 passed/13 skipped，
另8个旧publication测试通过。Skip为既有可选dataset/media fixtures，不是此次迁移用例。

证据：workspace runs/audit/opd-v4-hf-dataset-owner-migration-20261025-v1/。
HF checkpoint自动上传是后续独立[OPD-012](opd-v4-hf-publication-012.md)，不改动旧SFT publisher。
没有连接AMD、启动训练/Slurm、加载完整5B或实际上传HF；本轮源码未commit/push。
