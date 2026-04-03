# 🤖 AI Conversation Analyzer

高性能分析 **Claude Code** 和 **Codex CLI** 历史对话的命令行工具。

## 功能特性

- ⚡ **高性能解析** - 使用 mmap 处理大文件
- 🔌 **多源支持** - 同时支持 Claude Code 和 Codex CLI
- 📊 **多维分析** - 时间分布、关键词、问题类型、活跃度
- 📋 **清单模式** - 便于快速浏览和勾选
- 📁 **多种格式** - Markdown、JSON、CSV、控制台、HTML
- 🎯 **灵活筛选** - 按日期、项目、来源筛选

## 快速开始

```bash
# 克隆项目
git clone https://github.com/song/ai-conversation-analyzer.git
cd ai-conversation-analyzer

# 运行（无需安装依赖）
python3 aica.py analyze

# 或安装后使用
pip install -e .
aica analyze
```

## 使用示例

### 完整分析

```bash
# 生成完整 Markdown 报告
aica analyze -o report.md

# 控制台彩色输出
aica analyze -f console

# 清单格式（便于任务追踪）
aica analyze -f checklist -o todo.md
```

### 快速统计

```bash
aica stats
```

输出示例：
```
============================================================
🤖 AI 对话统计概览
============================================================

总问题数: 5460
时间跨度: 2025-09-05 ~ 2026-04-03
涉及项目: 250 个

【数据来源】
  🟣 Claude Code: 4500 (82.4%)
  🔵 Codex: 960 (17.6%)

【问题类型】
  代码实现   ████████████ 1800 (33.0%)
  调试排错   ████████ 1200 (22.0%)
  ...
```

### 查看单日详情

```bash
aica daily 2026-04-03
```

### 查看项目详情

```bash
# 精确匹配或模糊匹配
aica project futu_copy
aica project neuronos
```

### 时间线视图

```bash
# 最近 7 天
aica timeline

# 最近 30 天
aica timeline --days 30
```

### 关键词分析

```bash
# Top 20 关键词
aica keywords

# Top 50 关键词，仅 Codex
aica keywords --top 50 --source codex
```

### 导出数据

```bash
# JSON 格式
aica export -f json -o data.json

# CSV 格式
aica export -f csv -o data.csv
```

## 报告内容

### 清单格式示例

```markdown
# 📋 问题清单

## 2026-04-03 (58 个问题)

### 🟣 /Users/song/33/cli
- [ ] [00:08:02] 分析一下整个项目设计的功能性吧
- [ ] [00:11:40] 有什么特别的设计吗？

### 🔵 codex:019d53a3
- [ ] [22:13:17] 你有能力把 Codex 的 API 完整地解码出来吗？
```

### 分析维度

1. **问题类型分类**
   - 代码实现
   - 调试排错
   - 架构设计
   - 代码审查
   - 查询信息
   - 配置部署

2. **时间分布**
   - 小时热力图
   - 星期分布
   - 连续活跃记录

3. **关键词提取**
   - Top 20 高频词
   - 中文词组识别

4. **项目统计**
   - 问题数量排行
   - 活跃度时间线
   - 来源分布

## 项目结构

```
ai-conversation-analyzer/
├── aica.py              # 入口脚本
├── src/
│   ├── __init__.py
│   ├── cli.py           # 命令行接口
│   ├── parser.py        # 历史记录解析器
│   ├── analyzer.py      # 问题分析器
│   └── formatters.py    # 输出格式化
├── tests/               # 测试文件
├── docs/                # 文档
├── requirements.txt     # 依赖
└── README.md            # 说明文档
```

## 高级用法

### 自定义历史文件路径

```bash
aica analyze \
  --claude-path /path/to/claude/history.jsonl \
  --codex-path /path/to/codex/history.jsonl
```

### 仅分析特定数据源

```bash
# 仅 Claude Code
aica stats --codex-path /dev/null

# 仅 Codex
aica stats --claude-path /dev/null
```

## 性能

- 处理 5000+ 条记录 < 1 秒
- 内存占用 ~50MB（5K 条记录）
- 支持百万级数据量（mmap 优化）

## 扩展计划

- [ ] Web UI 可视化
- [ ] 问题相似度聚类
- [ ] 知识图谱生成
- [ ] 自动标签推荐
- [ ] 趋势预测

## License

MIT

## 贡献

欢迎提交 Issue 和 PR！
