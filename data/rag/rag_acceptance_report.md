# RAG Acceptance Report

验收日期：2026-09-03

## 1. Dataset Validation

- 当前 chunk 数：59
- `25-26` chunk 数：58
- `26-27` chunk 数：1
- `season=None`：0
- 其他 season 值：0
- JSON 加载：PASS
- chunk id 唯一性：PASS，重复 id 为 0
- 必填字段：PASS；所有 chunk 的 `id`、`text`、`metadata` 以及 `metadata.source/title/type/topic/season` 均存在，`metadata.keywords` 均为 list
- 张谢童甲错误第五轮助攻事实检查：PASS
  - `精准长传`：0 处
  - 未发现同一事实片段中同时出现“张谢童甲”与“第五轮助攻/助攻破门/精准长传”
  - 仍保留的“第五轮”和“助攻”均已人工复核，属于干宸浩、王恩博、谭丁睿、欧阳慷、陈卓、王靖皓、伍瑜航等已有事实，或张谢童甲第四轮接欧阳慷角球助攻破门，不是被禁止的错误事实

关键词全局检查结果：

| 关键词 | text 中出现次数 | 结论 |
|---|---:|---|
| `26-27` | 1 | 仅允许的队长事实 |
| `26–27` | 0 | PASS |
| `新赛季` | 0 | PASS |
| `新任队长` | 0 | PASS |
| `升任队长` | 0 | PASS |
| `九位升入大二` | 0 | PASS |
| `六名功勋` | 0 | PASS |
| `第五轮` | 11 | 已逐条复核，无张谢童甲第五轮助攻事实 |
| `助攻` | 8 | 已逐条复核，无被禁止的错误表述 |
| `精准长传` | 0 | PASS |

唯一的 `season="26-27"` chunk：

```json
{
  "id": "culture_captain_succession_001",
  "text": "26-27赛季，干宸浩和张谢童甲担任超音速球队队长。",
  "metadata": {
    "source": "user_confirmed",
    "title": "超音速 - 26-27赛季球队队长",
    "type": "team_culture",
    "topic": "captaincy",
    "player": null,
    "season": "26-27",
    "status": null,
    "keywords": ["超音速", "26-27赛季", "球队队长", "干宸浩", "张谢童甲"]
  }
}
```

`python -B -X utf8 -m scripts.validate_chunks` 结果：

```text
Validation passed
Total chunks: 59
Duplicate IDs: 0
Invalid chunks: 0
```

结论：PASS

## 2. Dense Index

- 重建方式：当前 `scripts.build_dense_index` 没有命令行入口，因此按项目函数入口执行 `build_dense_index()` 和 `save_dense_index()`
- chunk 数：59
- index 数：59
- embedding 维度：512
- 空 embedding：0
- chunk id 集合与 index id 集合：完全一致
- index 中的 `id/text/metadata` 与当前 chunks：逐条一致
- 旧错误文本 `精准长传` 在 index 中：0 处
- `dense_index.json` 重建时间晚于 `chunks.json`

结论：PASS，Dense Index 已与当前 59 条 chunks 同步重建。

## 3. Retrieval Tests

### Test A

- Query：`干宸浩有什么技术特点？`
- Hybrid Top：`player_gan_chenhao_technical_001` / 干宸浩 - 技术特点与球队角色；RRF `0.0327868852`
- Rerank Top：同一 chunk；rerank score `0.9981728792`
- 文本摘要：干宸浩主打左前卫，可客串中后卫，脚下技术细腻、远射与抢点突出，左右脚均衡，长传精准。
- 结果：PASS。首位即为干宸浩技术特点。

### Test B

- Query：`张谢童甲25-26赛季有什么技术特点？`
- Filter：`season=25-26`
- Hybrid Top：`player_zhang_xietongjia_technical_001` / 张谢童甲 - 技术特点与球队角色；RRF `0.0327868852`
- Rerank Top：`season_25_26_chance_creation_001` / 25-26 赛季 - 机会创造方式；rerank score `0.9844130874`
- Rerank 第二位：`player_zhang_xietongjia_technical_001`；rerank score `0.9805312753`
- 文本摘要：张谢童甲拥有爆发力与速度，边路突破、拦截、长传和攻防转换能力突出。
- 结果：PASS。返回内容均为 25-26，技术特点 chunk 位于结果集内，且不存在张谢童甲第五轮助攻错误事实。

### Test C

- Query：`26-27赛季球队队长是谁？`
- Filter：`season=26-27`
- Hybrid / Rerank Top：`culture_captain_succession_001` / 超音速 - 26-27赛季球队队长
- rerank score：`0.9998076558`
- 文本摘要：26-27赛季，干宸浩和张谢童甲担任超音速球队队长。
- 结果：PASS。没有返回任何其他 26-27 事实。

### Test D

- Query：`26-27赛季球队使用什么战术？`
- Filter：`season=26-27, type=tactics`
- Hybrid Top：空
- Rerank Top：空
- 结果：PASS。不存在或返回任何 26-27 战术资料。

### Test E

- Query：`天水球王是谁？`
- Hybrid Top：`player_zhang_xietongjia_performance_001` / 张谢童甲 - 代表性表现与球队故事；RRF `0.0327868852`
- Rerank Top：同一 chunk；rerank score `0.9007220268`
- 文本摘要：队内常称张谢童甲为天水球王。
- 结果：PASS。

## 4. RAG Tool Tests

### Tool Test 1

- 输入：`search_team_knowledge(query="干宸浩有什么技术特点？", player="干宸浩", season="25-26", top_k=2)`
- 关键输出：`success=true`；filters 为 `player=干宸浩, season=25-26`
- 结果 id：`player_gan_chenhao_technical_001`、`player_gan_chenhao_performance_001`
- metadata 交叉核对：两条均为干宸浩、25-26
- 结果：PASS

### Tool Test 2

- 输入：`search_team_knowledge(query="26-27赛季球队队长是谁？", season="26-27")`
- 关键输出：`success=true`；仅返回 `culture_captain_succession_001`
- 结果：PASS

### Tool Test 3

- 输入：`search_team_knowledge(query="26-27赛季球队战术是什么？", season="26-27")`
- 关键输出：`success=false`；filters 为 `season=26-27, type=tactics`；results 为空
- 结果：PASS

首次实测发现该调用会把唯一的 26-27 队长 chunk 当作结果返回。已做最小修复：问题明确包含“战术”且调用方未传 `knowledge_type` 时，使用现有 `type=tactics` metadata 过滤。未修改 Dense、BM25、RRF 或 Reranker 算法。

## 5. Agent Tests

实际发送给 LLM 的工具名称：

```text
get_player_goals
get_player_profile
get_player_number
get_scorer_ranking
get_match_result
search_team_knowledge
```

### Agent Test 1

- 用户问题：`张谢童甲25-26赛季进了几个球？他的技术特点是什么？`
- 实际 Tool：`get_player_goals(name="张谢童甲", season="25-26")`；`search_team_knowledge(query="张谢童甲 技术特点", season="25-26")`
- 最终回答摘要：25-26 赛季 3 球；技术特点包括右前卫/后腰位置、爆发力与速度、边路突破、拦截、长传和攻防转换。
- Hallucination：无；未出现错误第五轮助攻事实。
- 结果：PASS

### Agent Test 2

- 用户问题：`26-27赛季球队队长是谁？`
- 实际 Tool：`search_team_knowledge(query="队长", season="26-27", knowledge_type="team_culture")`
- 最终回答摘要：干宸浩和张谢童甲担任队长。
- Hallucination：无；未推断正副队长、职责、阵容或战术。
- 结果：PASS

### Agent Test 3

- 用户问题：`26-27赛季球队打什么战术？`
- 实际 Tool：`search_team_knowledge(query="26-27赛季球队打什么战术", season="26-27", knowledge_type="tactics", top_k=5)`
- Tool 输出：`success=false, results=[]`
- 最终回答摘要：`暂无相关数据。`
- Hallucination：无；没有套用 25-26 战术，也没有猜测缺失原因。
- 结果：PASS

### Agent Test 4

- 用户问题：`张谢童甲25-26赛季进了几个球？干宸浩有什么技术特点？`
- 实际 Tool：`get_player_goals(name="张谢童甲", season="25-26")`；`search_team_knowledge(query="干宸浩技术特点", player="干宸浩")`
- 最终回答摘要：张谢童甲 3 球；干宸浩的技术特点来自其本人技术档案。
- Hallucination：无；两个球员没有混淆。
- 结果：PASS

为修复初次 Agent 边界测试中出现的“空结果后取消赛季重搜”和“猜测无数据原因”，仅增强了现有 System Prompt 与 RAG Tool 描述：赛季参数必须与用户问题一致；空结果后立即回答暂无数据；禁止套用其他赛季、推测原因、推断正副队长或职责。Agent Loop 控制流程未改动。

## 6. Remaining Issues

- `openrouter/free` 在重复验收中出现过一次外部响应提前结束（`ChunkedEncodingError`），重试后恢复；这是外部 Provider 传输波动，不是本地 RAG 数据或索引错误。
- Retrieval Test B 中，Reranker 将“25-26 赛季机会创造方式”排在张谢童甲技术档案之前，两者分数非常接近；正确技术档案仍在第二位并被 Tool/Agent 正确使用。该现象未违反本次 Test B 的赛季边界与错误事实验收标准，但属于后续可观察的排序质量点。
- 当前 `tests` 下是直接执行并打印结果的脚本，没有 pytest 断言。三个现有测试脚本均以退出码 0 完成：
  - `tests/test_player_tools.py`
  - `tests/test_embedding_similarity.py`（相似文本 `0.9340`，无关文本 `0.4467`）
  - `tests/test_tool_call.py`（射手榜问题回答张谢童甲第 2、3 球）

## 7. Final Result

PASS

数据验证、Dense Index 同步、Retriever、RAG Tool、Agent 混合调用与 26-27 知识边界的最终关键测试均已通过。
