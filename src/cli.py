#!/usr/bin/env python3
"""
AI Conversation Analyzer - CLI
高性能分析 Claude Code 和 Codex CLI 历史对话

Usage:
    aica analyze                    # 完整分析
    aica analyze --format checklist # 清单格式
    aica stats                      # 快速统计
    aica daily 2026-04-03           # 单日详情
    aica project futu_copy          # 项目详情
    aica timeline                   # 时间线视图
    aica keywords                   # 关键词分析
    aica export --format json       # 导出 JSON
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, List

from .parser import parse_all_sources
from .analyzer import QuestionAnalyzer
from .formatters import get_formatter


def get_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog='aica',
        description='AI Conversation Analyzer - 分析 Claude Code 和 Codex CLI 历史对话',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  aica analyze                           # 完整分析（默认 Markdown）
  aica analyze -f console                # 控制台彩色输出
  aica analyze -f checklist -o todo.md   # 清单格式保存
  aica stats                             # 快速统计
  aica daily 2026-04-03                  # 查看单日详情
  aica project myproject                 # 查看项目详情
  aica timeline                          # 时间线视图
  aica keywords --top 30                 # 关键词分析
  aica export -f json -o data.json       # 导出 JSON
        '''
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 0.1.0'
    )

    parser.add_argument(
        '--claude-path',
        type=Path,
        default=Path.home() / '.claude' / 'history.jsonl',
        help='Claude Code 历史文件路径 (默认: ~/.claude/history.jsonl)'
    )

    parser.add_argument(
        '--codex-path',
        type=Path,
        default=Path.home() / '.codex' / 'history.jsonl',
        help='Codex CLI 历史文件路径 (默认: ~/.codex/history.jsonl)'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # analyze - 完整分析
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='完整分析报告',
        description='生成完整的问题分析报告'
    )
    analyze_parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json', 'csv', 'console', 'checklist'],
        default='markdown',
        help='输出格式 (默认: markdown)'
    )
    analyze_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='输出文件路径 (默认: stdout)'
    )
    analyze_parser.add_argument(
        '--limit', '-l',
        type=int,
        help='限制处理的问题数量 (用于测试)'
    )

    # stats - 快速统计
    stats_parser = subparsers.add_parser(
        'stats',
        help='快速统计概览',
        description='显示数据概览统计'
    )

    # daily - 单日详情
    daily_parser = subparsers.add_parser(
        'daily',
        help='查看单日详情',
        description='查看指定日期的问题详情'
    )
    daily_parser.add_argument(
        'date',
        help='日期 (格式: YYYY-MM-DD)'
    )
    daily_parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'console'],
        default='console',
        help='输出格式'
    )

    # project - 项目详情
    project_parser = subparsers.add_parser(
        'project',
        help='查看项目详情',
        description='查看指定项目的问题详情'
    )
    project_parser.add_argument(
        'name',
        help='项目名称或路径片段'
    )
    project_parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'console'],
        default='console',
        help='输出格式'
    )

    # timeline - 时间线
    timeline_parser = subparsers.add_parser(
        'timeline',
        help='时间线视图',
        description='按时间顺序显示问题'
    )
    timeline_parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='显示最近 N 天 (默认: 7)'
    )

    # keywords - 关键词分析
    keywords_parser = subparsers.add_parser(
        'keywords',
        help='关键词分析',
        description='提取高频关键词'
    )
    keywords_parser.add_argument(
        '--top',
        type=int,
        default=20,
        help='显示 Top N 关键词 (默认: 20)'
    )
    keywords_parser.add_argument(
        '--source',
        choices=['all', 'claude', 'codex'],
        default='all',
        help='数据来源筛选'
    )

    # export - 导出
    export_parser = subparsers.add_parser(
        'export',
        help='导出数据',
        description='导出原始数据'
    )
    export_parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv'],
        default='json',
        help='导出格式 (默认: json)'
    )
    export_parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='输出文件路径'
    )

    return parser


def load_questions(claude_path: Path, codex_path: Path, limit: Optional[int] = None):
    """加载问题数据"""
    print("正在加载历史数据...", file=sys.stderr)
    start_time = time.time()

    questions = []
    for q in parse_all_sources(claude_path, codex_path):
        questions.append(q)
        if limit and len(questions) >= limit:
            break

    # 按时间倒序
    questions.sort(key=lambda x: x.timestamp, reverse=True)

    elapsed = time.time() - start_time
    print(f"✓ 加载完成: {len(questions)} 个问题 ({elapsed:.2f}s)", file=sys.stderr)

    return questions


def cmd_analyze(args):
    """分析命令"""
    questions = load_questions(args.claude_path, args.codex_path, args.limit)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    print("正在分析...", file=sys.stderr)
    analyzer = QuestionAnalyzer(questions)
    analysis = analyzer.analyze()

    formatter = get_formatter(args.format)
    output = formatter.format(questions, analysis)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ 已保存: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


def cmd_stats(args):
    """统计命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    analyzer = QuestionAnalyzer(questions)
    analysis = analyzer.analyze()

    print()
    print("=" * 60)
    print("🤖 AI 对话统计概览")
    print("=" * 60)
    print(f"\n总问题数: {analysis.total}")
    print(f"时间跨度: {min(analysis.by_date.keys())} ~ {max(analysis.by_date.keys())}")
    print(f"涉及项目: {len(analysis.by_project)} 个")

    print("\n【数据来源】")
    for source, count in analysis.by_source.items():
        icon = '🟣' if source == 'Claude Code' else '🔵'
        pct = count / analysis.total * 100
        print(f"  {icon} {source}: {count} ({pct:.1f}%)")

    print("\n【问题类型】")
    for type_name, count in sorted(analysis.question_types.items(), key=lambda x: x[1], reverse=True):
        pct = count / analysis.total * 100
        bar = "█" * int(pct / 2)
        print(f"  {type_name:10} {bar} {count} ({pct:.1f}%)")

    print("\n【Top 10 活跃项目】")
    for i, (project, qs) in enumerate(list(analysis.by_project.items())[:10], 1):
        claude = sum(1 for q in qs if q.source == 'Claude Code')
        codex = sum(1 for q in qs if q.source == 'Codex')
        tags = []
        if claude > 0:
            tags.append(f"🟣{claude}")
        if codex > 0:
            tags.append(f"🔵{codex}")
        print(f"  {i:2}. {project}: {len(qs)} ({' '.join(tags)})")

    print("\n【时间分布 (小时)】")
    peak_hours = sorted(analysis.hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
    for hour, count in peak_hours:
        print(f"  {hour:02d}:00 - {count} 个问题")

    print()
    return 0


def cmd_daily(args):
    """单日详情命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    analyzer = QuestionAnalyzer(questions)
    summary = analyzer.get_daily_summary(args.date)

    if not summary:
        print(f"未找到 {args.date} 的数据", file=sys.stderr)
        return 1

    print(f"\n📅 {args.date} 详情")
    print("=" * 60)
    print(f"总问题数: {summary['total']}")
    print(f"涉及项目: {len(summary['projects'])}")

    print("\n【来源分布】")
    for source, qs in summary['by_source'].items():
        icon = '🟣' if source == 'Claude Code' else '🔵'
        print(f"  {icon} {source}: {len(qs)} 个")

    print("\n【按项目】")
    for source, qs in summary['by_source'].items():
        icon = '🟣' if source == 'Claude Code' else '🔵'
        by_proj = {}
        for q in qs:
            if q.project not in by_proj:
                by_proj[q.project] = []
            by_proj[q.project].append(q)

        for project, proj_qs in by_proj.items():
            print(f"\n  {icon} {project} ({len(proj_qs)} 个)")
            for q in proj_qs:
                time_str = q.datetime.strftime('%H:%M')
                content = q.content[:50] + "..." if len(q.content) > 50 else q.content
                content = content.replace('\n', ' ')
                print(f"    [{time_str}] {content}")

    print()
    return 0


def cmd_project(args):
    """项目详情命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    # 模糊匹配项目名称
    matching = [(p, qs) for p, qs in QuestionAnalyzer(questions).by_project.items()
                if args.name.lower() in p.lower()]

    if not matching:
        print(f"未找到匹配 '{args.name}' 的项目", file=sys.stderr)
        return 1

    for project, qs in matching:
        print(f"\n📂 项目: {project}")
        print("=" * 60)
        print(f"总问题数: {len(qs)}")

        dates = sorted(set(q.date for q in qs))
        print(f"时间范围: {dates[0]} ~ {dates[-1]}")
        print(f"活跃天数: {len(dates)}")

        # 来源统计
        source_counts = {}
        for q in qs:
            source_counts[q.source] = source_counts.get(q.source, 0) + 1
        print(f"\n来源: " + " | ".join([
            f"{'🟣' if s == 'Claude Code' else '🔵'} {s}: {c}"
            for s, c in source_counts.items()
        ]))

        # 最近问题
        print(f"\n【最近 10 个问题】")
        for q in sorted(qs, key=lambda x: x.timestamp, reverse=True)[:10]:
            time_str = q.datetime.strftime('%Y-%m-%d %H:%M')
            icon = '🟣' if q.source == 'Claude Code' else '🔵'
            content = q.content[:60] + "..." if len(q.content) > 60 else q.content
            content = content.replace('\n', ' ')
            print(f"  {icon} [{time_str}] {content}")

    print()
    return 0


def cmd_timeline(args):
    """时间线命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=args.days)
    recent = [q for q in questions if q.datetime > cutoff]

    print(f"\n📈 最近 {args.days} 天时间线")
    print("=" * 60)

    # 按日期分组
    by_date = {}
    for q in recent:
        if q.date not in by_date:
            by_date[q.date] = []
        by_date[q.date].append(q)

    for date in sorted(by_date.keys(), reverse=True):
        qs = by_date[date]
        source_counts = {}
        for q in qs:
            source_counts[q.source] = source_counts.get(q.source, 0) + 1

        tags = " | ".join([
            f"{'🟣' if s == 'Claude Code' else '🔵'} {s}:{c}"
            for s, c in source_counts.items()
        ])

        print(f"\n{date} ({len(qs)} 个问题)")
        print(f"  {tags}")

        # 显示项目摘要
        by_proj = {}
        for q in qs:
            if q.project not in by_proj:
                by_proj[q.project] = []
            by_proj[q.project].append(q)

        for project, proj_qs in by_proj.items():
            icon = '🟣' if proj_qs[0].source == 'Claude Code' else '🔵'
            print(f"  {icon} {project}: {len(proj_qs)} 个")

    print()
    return 0


def cmd_keywords(args):
    """关键词命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    # 筛选来源
    if args.source == 'claude':
        questions = [q for q in questions if q.source == 'Claude Code']
    elif args.source == 'codex':
        questions = [q for q in questions if q.source == 'Codex']

    analyzer = QuestionAnalyzer(questions)
    keywords = analyzer._extract_keywords(args.top)

    print(f"\n🔑 高频关键词 (Top {args.top})")
    print("=" * 60)

    max_count = keywords[0][1] if keywords else 1
    for i, (word, count) in enumerate(keywords, 1):
        bar_len = int(count / max_count * 30)
        bar = "█" * bar_len
        print(f"{i:2}. {word:12} {bar} {count}")

    print()
    return 0


def cmd_export(args):
    """导出命令"""
    questions = load_questions(args.claude_path, args.codex_path)

    if not questions:
        print("未找到任何问题数据", file=sys.stderr)
        return 1

    analyzer = QuestionAnalyzer(questions)
    analysis = analyzer.analyze()

    formatter = get_formatter(args.format)
    formatter.save(questions, analysis, args.output)

    print(f"✓ 已导出: {args.output}")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """主入口"""
    parser = get_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    # 检查历史文件
    if parsed.command != 'help':
        has_claude = parsed.claude_path.exists()
        has_codex = parsed.codex_path.exists()

        if not has_claude and not has_codex:
            print("错误: 未找到 Claude Code 或 Codex CLI 的历史文件", file=sys.stderr)
            print(f"  Claude: {parsed.claude_path}", file=sys.stderr)
            print(f"  Codex:  {parsed.codex_path}", file=sys.stderr)
            return 1

    # 路由命令
    commands = {
        'analyze': cmd_analyze,
        'stats': cmd_stats,
        'daily': cmd_daily,
        'project': cmd_project,
        'timeline': cmd_timeline,
        'keywords': cmd_keywords,
        'export': cmd_export,
    }

    handler = commands.get(parsed.command)
    if handler:
        return handler(parsed)

    return 0


if __name__ == '__main__':
    sys.exit(main())
