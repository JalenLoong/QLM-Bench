---
id: QLM-DATA-041
type: change
status: active
source_map: []
---

# 十task prompt更新与MuJoCo1000增量发布

用户2026-10-17明确授权：十task使用authorization.json中的精确新prompt；原始physics/source/acceptance历史不回写，新的正式语言版本统一1000条text并按需生成对应text embedding（非训练）。先完成本地字节/字段差分与data-only验证，再HF private staging上传新增600、既有400仅prompt及必要校验/索引更新，保护旧400所有视频/数值/snapshot及Isaac-based完整树。验证远端LFS/Gitblob/代表回读后以已核对旧HEAD保护更新main，保持private。随后治理收尾并将三repo所有尚未提交的tracked/untracked源码/文档改动一并commit/push到配置的origin push targets；不丢弃原dirty修改，不上传token/模型/环境/大数据到GitHub。禁止训练/AMD/physics/render；不得把旧scope失败改为成功。

审计根workspace runs/audit/mujoco1000-prompt-publication-20261017-v1；原1000验收receipt和Observer更新receipt保持，HF新增600采用最新左后Observer。原prompt/embedding和生产frozen-source作为历史保持，新语言版本显式lineage。现有模型输入/历史TRAIN/EVAL声明不自动更换。

## Progress
- [x] 用户明确授权与原source库存。
- [x] 精确prompt语言版本/embedding/数据字段及必要hash同步。
- [x] HF旧400仅prompt差分与新增600本地验证。
- [x] private HF上传/回读/完整远端身份/Isaac保护与main更新。
- [ ] 治理收尾、三repo全部未提交改动commit/push、远端核对。

## 实际HF发布完成
main=470e0a1f290ef65a25ca1933a91a51ccd6427fcf，payload=b84488eca8a723767cef27fa455ec2ea8169f81c，1000条/10tasks，private与Isaac保持。远端数据/metadata实际回读通过。源码提交/归档在此后单独记录，不伪造源commit身份。
