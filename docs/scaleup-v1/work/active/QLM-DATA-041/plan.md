---
id: QLM-DATA-041
type: exec-plan
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

## 本地入口与验证
精确registration文本、已声明历史scene语言的只读overlay和原模型文件不变检查通过；39项prompt/public-entry相关CPU tests通过。十项新版本embedding由原冻结text encoder在inference_mode生成，0 optimizer steps。新1000发布副本与既有400 prompt-only差分正在逐task data-only验证；不重复WAM策略兼容验证，不训练/physics/render/AMD。远端基线main=a8eafc5b1e6019e4431d0417d9064f9fd658cc03，private=True；Isaac-based=519725c8bc77b35fd5d3b4ac8555a3e96a8876a7。三repo配置push targets的当前branch均与本地原HEAD一致，原dirty清单已保存。

## HF引用更新恢复：已有提交逐步推进
整批payload和20条远端回读、索引及十句prompt已通过；一次从旧main跨58个已上传提交更新引用连续遇HTTP504，实际main仍旧HEAD。改用这58个现有且完整祖先链明确的提交逐步fast-forward推进main，各步保存from/to意图并以精确旧HEAD lease保护、实际远端确认，不新增payload上传或改写历史。前57步保持旧根索引，最后一步才发布1000索引；旧索引DataRef固定原revision，原400非文本保持。外部未知HEAD立即停止；private/Isaac和最终完整tree验证保持。完成后继续既定三repo Git治理，不训练/AMD/physics/render或更换上传工具。

## 实际HF发布完成
main=470e0a1f290ef65a25ca1933a91a51ccd6427fcf，payload=b84488eca8a723767cef27fa455ec2ea8169f81c，1000条/10tasks，private与Isaac保持。远端数据/metadata实际回读通过。源码提交/归档在此后单独记录，不伪造源commit身份。
