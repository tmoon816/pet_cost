"""拼音工具：把中文姓名转换为全拼和首字母，用于搜索匹配。

英文/数字字符 pypinyin 会原样返回。统一小写便于大小写不敏感比较。
"""

from __future__ import annotations

from pypinyin import Style, lazy_pinyin


def to_pinyin(s: str | None) -> str:
    """全拼，无空格分隔。"张伟" → "zhangwei"；英文原样返回小写。"""
    if not s:
        return ""
    return "".join(lazy_pinyin(s, style=Style.NORMAL)).lower()


def to_initials(s: str | None) -> str:
    """首字母。"张伟" → "zw"；"Lucky" → "l"。"""
    if not s:
        return ""
    return "".join(lazy_pinyin(s, style=Style.FIRST_LETTER)).lower()
