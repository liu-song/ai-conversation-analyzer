#!/usr/bin/env python3
"""
高性能历史记录解析器
支持 Claude Code 和 Codex CLI
"""

import json
import mmap
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
import re


@dataclass
class Question:
    """问题数据模型"""
    content: str
    pasted_content: str
    timestamp: int
    datetime: datetime
    date: str
    project: str
    session_id: str
    source: str
    source_icon: str


class HistoryParser:
    """历史记录解析器基类"""

    def __init__(self, history_path: Path):
        self.history_path = history_path

    def parse(self) -> Iterator[Question]:
        """解析历史记录，生成 Question 对象"""
        raise NotImplementedError

    def _read_lines_fast(self) -> Iterator[str]:
        """使用 mmap 快速读取大文件"""
        if not self.history_path.exists():
            return

        with open(self.history_path, 'r', encoding='utf-8') as f:
            # 对于大文件使用 mmap
            try:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    for line in iter(mm.readline, b''):
                        yield line.decode('utf-8')
            except (ValueError, OSError):
                # 回退到普通读取
                for line in f:
                    yield line


class ClaudeParser(HistoryParser):
    """Claude Code 历史记录解析器"""

    EXCLUDE_PREFIXES = ('/', '[Pasted')

    def parse(self) -> Iterator[Question]:
        for line in self._read_lines_fast():
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            display = data.get('display', '')
            if not display or display.startswith(self.EXCLUDE_PREFIXES):
                continue

            timestamp = data.get('timestamp', 0)
            project = data.get('project', 'unknown')
            session_id = data.get('sessionId', '')

            # 提取粘贴内容
            pasted_text = ''
            pasted = data.get('pastedContents', {})
            if pasted:
                for val in pasted.values():
                    if isinstance(val, dict) and 'content' in val:
                        pasted_text = val['content']
                        break

            dt = datetime.fromtimestamp(timestamp / 1000)

            yield Question(
                content=display.strip(),
                pasted_content=pasted_text,
                timestamp=timestamp,
                datetime=dt,
                date=dt.strftime('%Y-%m-%d'),
                project=project,
                session_id=session_id,
                source='Claude Code',
                source_icon='🟣'
            )


class CodexParser(HistoryParser):
    """Codex CLI 历史记录解析器"""

    def __init__(self, history_path: Path):
        super().__init__(history_path)
        self.session_names = self._load_session_names()

    def _load_session_names(self) -> dict:
        """加载会话索引获取 thread_name"""
        session_index_path = self.history_path.parent / 'session_index.jsonl'
        names = {}

        if not session_index_path.exists():
            return names

        try:
            with open(session_index_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        sid = data.get('id', '')
                        name = data.get('thread_name', '')
                        if sid and name:
                            names[sid] = name
                    except:
                        pass
        except:
            pass

        return names

    def _get_project_name(self, session_id: str) -> str:
        """获取项目名称"""
        # 直接匹配
        if session_id in self.session_names:
            return self.session_names[session_id]

        # 模糊匹配前8个字符
        short_id = session_id[:8]
        for sid, name in self.session_names.items():
            if sid.startswith(short_id):
                return name

        return f'codex:{short_id}'

    def parse(self) -> Iterator[Question]:
        for line in self._read_lines_fast():
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = data.get('text', '')
            if not text or text.startswith('/'):
                continue

            timestamp = data.get('ts', 0)
            session_id = data.get('session_id', '')
            project = self._get_project_name(session_id)

            dt = datetime.fromtimestamp(timestamp)

            yield Question(
                content=text.strip(),
                pasted_content='',
                timestamp=timestamp * 1000,
                datetime=dt,
                date=dt.strftime('%Y-%m-%d'),
                project=project,
                session_id=session_id,
                source='Codex',
                source_icon='🔵'
            )


def parse_all_sources(claude_path: Optional[Path] = None,
                      codex_path: Optional[Path] = None) -> Iterator[Question]:
    """解析所有可用的数据源"""

    if claude_path is None:
        claude_path = Path.home() / '.claude' / 'history.jsonl'
    if codex_path is None:
        codex_path = Path.home() / '.codex' / 'history.jsonl'

    if claude_path.exists():
        yield from ClaudeParser(claude_path).parse()

    if codex_path.exists():
        yield from CodexParser(codex_path).parse()
