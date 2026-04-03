"""
问题分析器
提供多种维度的统计分析
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import re

from .parser import Question


@dataclass
class AnalysisResult:
    """分析结果"""
    total: int
    by_source: Dict[str, int]
    by_date: Dict[str, List[Question]]
    by_project: Dict[str, List[Question]]
    keywords: List[tuple]
    hourly_distribution: Dict[int, int]
    weekly_distribution: Dict[str, int]
    question_types: Dict[str, int]


class QuestionAnalyzer:
    """问题分析器"""

    # 问题类型关键词模式
    TYPE_PATTERNS = {
        '代码实现': r'写|实现|创建|添加|修改|修复|重构|优化|开发',
        '调试排错': r'错误|异常|bug|失败|问题|报错|崩溃|卡住',
        '架构设计': r'设计|架构|结构|模式|方案|如何|怎么|怎样',
        '代码审查': r'审查|review|检查|分析|评价|怎么样|可以吗',
        '查询信息': r'查询|获取|列出|查看|显示|多少|是什么',
        '配置部署': r'配置|部署|启动|运行|安装|设置|环境',
    }

    def __init__(self, questions: List[Question]):
        self.questions = questions

    def analyze(self) -> AnalysisResult:
        """执行完整分析"""
        return AnalysisResult(
            total=len(self.questions),
            by_source=self._group_by_source(),
            by_date=self._group_by_date(),
            by_project=self._group_by_project(),
            keywords=self._extract_keywords(),
            hourly_distribution=self._analyze_hourly(),
            weekly_distribution=self._analyze_weekly(),
            question_types=self._classify_types()
        )

    def _group_by_source(self) -> Dict[str, int]:
        """按来源统计"""
        return dict(Counter(q.source for q in self.questions))

    def _group_by_date(self) -> Dict[str, List[Question]]:
        """按日期分组"""
        by_date = defaultdict(list)
        for q in self.questions:
            by_date[q.date].append(q)
        return dict(sorted(by_date.items(), reverse=True))

    def _group_by_project(self) -> Dict[str, List[Question]]:
        """按项目分组"""
        by_project = defaultdict(list)
        for q in self.questions:
            by_project[q.project].append(q)
        return dict(sorted(by_project.items(), key=lambda x: len(x[1]), reverse=True))

    def _extract_keywords(self, top_n: int = 20) -> List[tuple]:
        """提取高频关键词"""
        # 简单的中文分词（按字符和常见词）
        all_text = ' '.join(q.content for q in self.questions)

        # 提取2-4字词组
        words = []
        for length in [4, 3, 2]:
            pattern = r'[\u4e00-\u9fff]{' + str(length) + r'}'
            words.extend(re.findall(pattern, all_text))

        # 过滤常见停用词
        stop_words = {'问题', '项目', '一下', '需要', '可以', '这个', '什么', '怎么'}
        word_counts = Counter(w for w in words if w not in stop_words and len(set(w)) > 1)

        return word_counts.most_common(top_n)

    def _analyze_hourly(self) -> Dict[int, int]:
        """分析小时分布"""
        hours = Counter(q.datetime.hour for q in self.questions)
        return {h: hours.get(h, 0) for h in range(24)}

    def _analyze_weekly(self) -> Dict[str, int]:
        """分析星期分布"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        counts = Counter(q.datetime.weekday() for q in self.questions)
        return {weekdays[i]: counts.get(i, 0) for i in range(7)}

    def _classify_types(self) -> Dict[str, int]:
        """问题类型分类"""
        type_counts = defaultdict(int)

        for q in self.questions:
            content = q.content.lower()
            matched = False
            for type_name, pattern in self.TYPE_PATTERNS.items():
                if re.search(pattern, content):
                    type_counts[type_name] += 1
                    matched = True
                    break
            if not matched:
                type_counts['其他'] += 1

        return dict(type_counts)

    def get_active_streaks(self) -> List[Dict[str, Any]]:
        """获取连续活跃日期"""
        dates = sorted(set(q.date for q in self.questions))
        if not dates:
            return []

        streaks = []
        current_streak = [dates[0]]

        for i in range(1, len(dates)):
            prev = datetime.strptime(dates[i-1], '%Y-%m-%d')
            curr = datetime.strptime(dates[i], '%Y-%m-%d')

            if (curr - prev).days == 1:
                current_streak.append(dates[i])
            else:
                streaks.append({
                    'start': current_streak[0],
                    'end': current_streak[-1],
                    'days': len(current_streak)
                })
                current_streak = [dates[i]]

        streaks.append({
            'start': current_streak[0],
            'end': current_streak[-1],
            'days': len(current_streak)
        })

        return sorted(streaks, key=lambda x: x['days'], reverse=True)

    def get_project_timeline(self, project: str) -> List[Question]:
        """获取指定项目的时间线"""
        return sorted(
            [q for q in self.questions if q.project == project],
            key=lambda x: x.timestamp
        )

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """获取单日摘要"""
        day_questions = [q for q in self.questions if q.date == date]

        if not day_questions:
            return {}

        by_source = defaultdict(list)
        for q in day_questions:
            by_source[q.source].append(q)

        return {
            'date': date,
            'total': len(day_questions),
            'by_source': dict(by_source),
            'projects': list(set(q.project for q in day_questions)),
            'hourly': Counter(q.datetime.hour for q in day_questions)
        }
