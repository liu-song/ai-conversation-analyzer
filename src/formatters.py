"""
输出格式化器
支持多种格式：Markdown、JSON、CSV、HTML、控制台
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

from .parser import Question
from .analyzer import AnalysisResult


class BaseFormatter:
    """格式化器基类"""

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        raise NotImplementedError

    def save(self, questions: List[Question], analysis: AnalysisResult, path: Path):
        """保存到文件"""
        content = self.format(questions, analysis)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)


class MarkdownFormatter(BaseFormatter):
    """Markdown 格式"""

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        lines = []
        lines.append("# 🤖 AI 对话问题分析报告\n")

        # 概览
        lines.append("## 📊 概览\n")
        lines.append(f"- **总问题数**: {analysis.total}")
        lines.append(f"- **时间跨度**: {min(analysis.by_date.keys())} ~ {max(analysis.by_date.keys())}")
        lines.append(f"- **涉及项目**: {len(analysis.by_project)} 个")
        lines.append(f"- **数据来源**:")
        for source, count in analysis.by_source.items():
            icon = '🟣' if source == 'Claude Code' else '🔵'
            lines.append(f"  - {icon} **{source}**: {count} 个 ({count/analysis.total*100:.1f}%)")
        lines.append("")

        # 问题类型分布
        lines.append("## 📝 问题类型分布\n")
        lines.append("| 类型 | 数量 | 占比 |")
        lines.append("|------|------|------|")
        for type_name, count in sorted(analysis.question_types.items(), key=lambda x: x[1], reverse=True):
            pct = count / analysis.total * 100
            lines.append(f"| {type_name} | {count} | {pct:.1f}% |")
        lines.append("")

        # 高频关键词
        lines.append("## 🔑 高频关键词 (Top 20)\n")
        for i, (word, count) in enumerate(analysis.keywords, 1):
            lines.append(f"{i}. **{word}** ({count}次)")
        lines.append("")

        # 时间分布
        lines.append("## ⏰ 时间分布\n")

        # 小时分布热力图
        lines.append("### 小时分布\n")
        lines.append("```")
        for hour in range(24):
            count = analysis.hourly_distribution.get(hour, 0)
            bar = "█" * min(count // 5, 20) if count > 0 else "░"
            lines.append(f"{hour:02d}:00 {bar} {count}")
        lines.append("```\n")

        # 星期分布
        lines.append("### 星期分布\n")
        lines.append("| 星期 | 数量 | 占比 |")
        lines.append("|------|------|------|")
        for day, count in analysis.weekly_distribution.items():
            pct = count / analysis.total * 100 if analysis.total > 0 else 0
            lines.append(f"| {day} | {count} | {pct:.1f}% |")
        lines.append("")

        # 连续活跃记录
        lines.append("## 🔥 连续活跃记录\n")
        # 需要在 analyzer 中获取
        lines.append("(需单独计算)\n")

        # 按日期详细列表
        lines.append("---\n")
        lines.append("## 📅 按日期详细列表\n")

        for date, qs in analysis.by_date.items():
            source_counts = Counter(q.source for q in qs)
            source_summary = " | ".join([
                f"{'🟣' if s == 'Claude Code' else '🔵'} {s}: {c}"
                for s, c in source_counts.items()
            ])

            lines.append(f"### {date}（{len(qs)} 个问题）\n")
            lines.append(f"*{source_summary}*\n")

            # 按项目和来源分组
            groups = {}
            for q in qs:
                key = (q.source, q.project)
                if key not in groups:
                    groups[key] = []
                groups[key].append(q)

            for (source, project), project_qs in groups.items():
                icon = '🟣' if source == 'Claude Code' else '🔵'
                lines.append(f"#### {icon} [{source}] {project}\n")
                for i, q in enumerate(project_qs, 1):
                    content = q.content.replace('\n', '<br>')
                    time_str = q.datetime.strftime('%H:%M:%S')
                    lines.append(f"{i}. **[{time_str}]** {content}")
                    if q.pasted_content:
                        pasted = q.pasted_content.replace('\n', ' ')[:100]
                        lines.append(f"   > 💾 {pasted}...")
                lines.append("")

        # 项目统计
        lines.append("---\n")
        lines.append("## 📂 项目统计\n")
        lines.append("| 项目路径 | 总数 | Claude Code | Codex | 首次 | 最后 |")
        lines.append("|----------|------|-------------|-------|------|------|")

        for project, qs in analysis.by_project.items():
            dates = sorted(set(q.date for q in qs))
            first = dates[0] if dates else '-'
            last = dates[-1] if dates else '-'
            claude = sum(1 for q in qs if q.source == 'Claude Code')
            codex = sum(1 for q in qs if q.source == 'Codex')
            lines.append(f"| `{project}` | {len(qs)} | {claude} | {codex} | {first} | {last} |")

        return '\n'.join(lines)


class JSONFormatter(BaseFormatter):
    """JSON 格式"""

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        data = {
            'summary': {
                'total': analysis.total,
                'by_source': analysis.by_source,
                'date_range': {
                    'start': min(analysis.by_date.keys()),
                    'end': max(analysis.by_date.keys())
                },
                'project_count': len(analysis.by_project)
            },
            'question_types': analysis.question_types,
            'keywords': analysis.keywords,
            'hourly_distribution': analysis.hourly_distribution,
            'weekly_distribution': analysis.weekly_distribution,
            'questions': [
                {
                    'content': q.content,
                    'date': q.date,
                    'time': q.datetime.strftime('%H:%M:%S'),
                    'project': q.project,
                    'source': q.source,
                    'has_pasted_content': bool(q.pasted_content)
                }
                for q in questions
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class CSVFormatter(BaseFormatter):
    """CSV 格式"""

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        import io
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['Date', 'Time', 'Source', 'Project', 'Content', 'HasPasted'])

        for q in questions:
            writer.writerow([
                q.date,
                q.datetime.strftime('%H:%M:%S'),
                q.source,
                q.project,
                q.content.replace('\n', ' '),
                'Yes' if q.pasted_content else 'No'
            ])

        return output.getvalue()


class ConsoleFormatter(BaseFormatter):
    """控制台格式（带颜色）"""

    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'green': '\033[32m',
        'blue': '\033[34m',
        'yellow': '\033[33m',
        'cyan': '\033[36m',
    }

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        c = self.COLORS
        lines = []

        lines.append(f"\n{c['bold']}🤖 AI 对话问题分析报告{c['reset']}")
        lines.append("=" * 60)

        # 概览
        lines.append(f"\n{c['bold']}📊 概览{c['reset']}")
        lines.append(f"  总问题数: {c['green']}{analysis.total}{c['reset']}")
        lines.append(f"  时间跨度: {min(analysis.by_date.keys())} ~ {max(analysis.by_date.keys())}")
        lines.append(f"  涉及项目: {len(analysis.by_project)} 个")

        lines.append(f"\n{c['bold']}数据来源:{c['reset']}")
        for source, count in analysis.by_source.items():
            icon = '🟣' if source == 'Claude Code' else '🔵'
            pct = count / analysis.total * 100
            lines.append(f"  {icon} {source}: {c['cyan']}{count}{c['reset']} ({pct:.1f}%)")

        # 问题类型
        lines.append(f"\n{c['bold']}📝 问题类型分布{c['reset']}")
        for type_name, count in sorted(analysis.question_types.items(), key=lambda x: x[1], reverse=True):
            pct = count / analysis.total * 100
            bar = "█" * int(pct / 2)
            lines.append(f"  {type_name:10} {bar} {count} ({pct:.1f}%)")

        # 高频关键词
        lines.append(f"\n{c['bold']}🔑 高频关键词 (Top 10){c['reset']}")
        for i, (word, count) in enumerate(analysis.keywords[:10], 1):
            lines.append(f"  {i:2}. {word:10} {c['yellow']}{count}{c['reset']}次")

        # 小时分布
        lines.append(f"\n{c['bold']}⏰ 小时分布热力图{c['reset']}")
        for hour in range(0, 24, 4):
            row = []
            for h in range(hour, hour + 4):
                count = analysis.hourly_distribution.get(h, 0)
                if count > 20:
                    color = c['green']
                elif count > 10:
                    color = c['yellow']
                else:
                    color = ''
                row.append(f"{h:02d}:00 {color}{count:3}{c['reset']}")
            lines.append("  " + " | ".join(row))

        # Top 5 项目
        lines.append(f"\n{c['bold']}📂 Top 5 活跃项目{c['reset']}")
        for i, (project, qs) in enumerate(list(analysis.by_project.items())[:5], 1):
            claude = sum(1 for q in qs if q.source == 'Claude Code')
            codex = sum(1 for q in qs if q.source == 'Codex')
            tags = []
            if claude > 0:
                tags.append(f"🟣{claude}")
            if codex > 0:
                tags.append(f"🔵{codex}")
            lines.append(f"  {i}. {project}: {c['cyan']}{len(qs)}{c['reset']} ({' '.join(tags)})")

        lines.append("")
        return '\n'.join(lines)


class ChecklistFormatter(BaseFormatter):
    """清单式格式 - 便于快速浏览"""

    def format(self, questions: List[Question], analysis: AnalysisResult) -> str:
        lines = []
        lines.append("# 📋 问题清单\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**总计**: {analysis.total} 个问题\n")

        for date, qs in analysis.by_date.items():
            lines.append(f"## {date} ({len(qs)} 个问题)\n")

            # 按项目分组
            by_project = {}
            for q in qs:
                if q.project not in by_project:
                    by_project[q.project] = []
                by_project[q.project].append(q)

            for project, project_qs in by_project.items():
                icon = '🟣' if project_qs[0].source == 'Claude Code' else '🔵'
                lines.append(f"### {icon} {project}\n")

                for q in project_qs:
                    time_str = q.datetime.strftime('%H:%M')
                    # 截断过长内容
                    content = q.content[:60] + "..." if len(q.content) > 60 else q.content
                    content = content.replace('\n', ' ')
                    lines.append(f"- [ ] [{time_str}] {content}")
                lines.append("")

        return '\n'.join(lines)


def get_formatter(format_name: str) -> BaseFormatter:
    """获取格式化器实例"""
    formatters = {
        'markdown': MarkdownFormatter,
        'json': JSONFormatter,
        'csv': CSVFormatter,
        'console': ConsoleFormatter,
        'checklist': ChecklistFormatter,
    }

    fmt = format_name.lower()
    if fmt not in formatters:
        raise ValueError(f"Unknown format: {format_name}. Available: {list(formatters.keys())}")

    return formatters[fmt]()
