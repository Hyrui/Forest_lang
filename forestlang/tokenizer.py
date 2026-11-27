# -*- coding: utf-8 -*-
"""森林语言源码到 Python 源码的转换器。

森林语言采用中文关键字和可读的中文运算符，表达式、缩进、标准库与
第三方库仍遵循 Python 语义。转换器只改写代码词元，不会改动字符串、
注释或跨行文本。
"""

from dataclasses import dataclass
import re


KEYWORDS = {
    "如果": "if", "否则如果": "elif", "否则": "else",
    "当": "while", "对于": "for", "于": "in", "属于": "in",
    "定义": "def", "返回": "return", "类": "class",
    "尝试": "try", "捕获": "except", "最终": "finally",
    "抛出": "raise", "断言": "assert",
    "导入": "import", "从": "from", "自": "from", "来自": "from",
    "作为": "as", "全局": "global", "非局部": "nonlocal", "删除": "del",
    "并且": "and", "与": "and", "或者": "or", "或": "or",
    "不是": "not", "并非": "not", "真": "True", "假": "False",
    "空": "None", "是": "is",
    "继续": "continue", "打断": "break", "跳过": "pass", "通过": "pass",
    "让": "lambda", "产出": "yield", "等待": "await",
    "异步": "async", "包住": "with",
}

BUILTINS = {
    "打印": "print", "长度": "len", "输入": "input", "范围": "range",
    "整数": "int", "小数": "float", "字符串": "str", "列表": "list",
    "元组": "tuple", "字典": "dict", "集合": "set", "布尔": "bool",
    "字节": "bytes", "求和": "sum", "最大": "max", "最小": "min",
    "绝对值": "abs", "排序": "sorted", "枚举": "enumerate", "压缩": "zip",
    "映射": "map", "过滤": "filter", "反转": "reversed",
    "任意": "any", "全部": "all", "类型": "type",
    "属于类型": "isinstance", "有属性": "hasattr", "取属性": "getattr",
    "设属性": "setattr", "打开": "open", "打开文件": "open",
    "格式": "format", "四舍五入": "round",
    "异常": "Exception", "值错误": "ValueError", "类型错误": "TypeError",
    "键错误": "KeyError", "索引错误": "IndexError",
    "文件未找到错误": "FileNotFoundError",
}

MODULES = {
    "操作系统": "os", "系统": "sys", "数学": "math", "随机": "random",
    "时间": "time", "日期": "datetime", "路径库": "pathlib", "正则": "re",
    "请求库": "requests", "网址解析": "urllib.parse", "数据类": "dataclasses",
    "文件查找": "glob", "哈希库": "hashlib", "日志": "logging",
    "线程库": "threading", "子进程": "subprocess", "JSON库": "json",
    "表格库": "csv", "集合库": "collections", "迭代工具": "itertools",
}

ATTRS = {
    "获取": "get", "提交": "post", "文本": "text", "状态码": "status_code",
    "内容": "content", "请求头": "headers", "参数": "params", "数据": "data",
    "追加": "append", "扩展": "extend", "插入": "insert", "弹出": "pop",
    "移除": "remove", "清空": "clear", "更新": "update", "键": "keys",
    "值": "values", "项": "items", "复制": "copy",
    "拆分": "split", "拼接": "join", "替换": "replace", "查找": "find",
    "去除空格": "strip", "以开头": "startswith", "以结尾": "endswith",
    "小写": "lower", "大写": "upper", "出现次数": "count",
    "格式化": "format", "读取": "read", "读一行": "readline",
    "读所有行": "readlines", "写入": "write", "关闭": "close",
    "字典取值": "get",
}

OPERATORS = {
    "加": "+", "减": "-", "乘": "*", "除": "/", "整除": "//",
    "取余": "%", "次方": "**",
    "等于": "==", "不等于": "!=", "大于": ">", "小于": "<",
    "大于等于": ">=", "小于等于": "<=",
    "大于或等于": ">=", "小于或等于": "<=",
    "加等于": "+=", "减等于": "-=", "乘等于": "*=", "除等于": "/=",
    "整除等于": "//=", "取余等于": "%=", "次方等于": "**=",
}

KWARGS = {
    "超时": "timeout", "结束": "end", "分隔符": "sep", "编码": "encoding",
    "参数": "params", "数据": "data", "请求头": "headers", "文件": "files",
    "验证": "verify", "允许重定向": "allow_redirects", "数值": "value",
    "默认值": "default", "类型": "kind", "步长": "step", "起始": "start",
    "终止": "stop", "键": "key", "反转": "reverse",
}

_TRANSLATION_TABLES = (KEYWORDS, BUILTINS, MODULES, OPERATORS)
_TABLES = tuple(
    (table, tuple(sorted(table, key=len, reverse=True)))
    for table in _TRANSLATION_TABLES
)
_WORD_ORIGIN = {
    word: python
    for table in _TRANSLATION_TABLES
    for word, python in table.items()
}

_CJK = "\u3400-\u4dbf\u4e00-\u9fff"
_CJK_RE = re.compile("[%s]" % _CJK)
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[%s][%s0-9A-Za-z_]*" % (_CJK, _CJK))

PUNCT = {
    "，": ",", "（": "(", "）": ")", "：": ":", "；": ";",
    "【": "[", "】": "]", "｛": "{", "｝": "}", "？": "?", "！": "!",
}

_FROM_PREFIX = frozenset(("从", "自", "来自"))
_QUOTES = {
    "“": ("”", '"'),
    "‘": ("’", "'"),
}
_MULTI_OPS = tuple(sorted((
    "**=", "//=", ">>=", "<<=", "...", "==", "!=", "<=", ">=", "//", "**",
    "+=", "-=", "*=", "/=", "%=", ":=", "->", ">>", "<<", "@=",
), key=len, reverse=True))


class ForestError(SyntaxError):
    """翻译或编译阶段的错误。"""


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    line: int


def _error(line, message):
    raise ForestError("第 %d 行%s" % (line, message))


def _escape_for_ascii_quote(body, quote):
    result = []
    escaped = False
    for char in body:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\":
            result.append(char)
            escaped = True
        elif char == quote:
            result.append("\\" + char)
        else:
            result.append(char)
    return "".join(result)


def _read_string(src, start, line):
    start_line = line
    if src.startswith('"""', start) or src.startswith("'''", start):
        delimiter = src[start:start + 3]
        i = start + 3
        while i < len(src):
            if src.startswith(delimiter, i):
                return src[start:i + 3], i + 3, line
            if src[i] == "\\":
                if i + 1 < len(src) and src[i + 1] == "\n":
                    line += 1
                i += 2
                continue
            if src[i] == "\n":
                line += 1
            i += 1
        _error(start_line, "有多行字符串没有闭合")

    opening = src[start]
    if opening in _QUOTES:
        closing, quote = _QUOTES[opening]
        ascii_string = False
    else:
        closing = opening
        quote = opening
        ascii_string = True

    i = start + 1
    while i < len(src):
        char = src[i]
        if char == "\\":
            if i + 1 < len(src) and src[i + 1] == "\n":
                line += 1
            i += 2
            continue
        if char == closing:
            if ascii_string:
                return src[start:i + 1], i + 1, line
            body = _escape_for_ascii_quote(src[start + 1:i], quote)
            return quote + body + quote, i + 1, line
        if char == "\n":
            _error(start_line, "有字符串没有闭合")
        i += 1
    _error(start_line, "有字符串没有闭合")


def _scan_source(src):
    """把源码切分成保留原文的输出词元。"""
    tokens = []
    i = 0
    line = 1
    length = len(src)
    while i < length:
        char = src[i]
        if char in " \t\f":
            j = i + 1
            while j < length and src[j] in " \t\f":
                j += 1
            tokens.append(_Token("space", src[i:j], line))
            i = j
            continue
        if char == "\n":
            tokens.append(_Token("newline", "\n", line))
            line += 1
            i += 1
            continue
        if char == "#":
            j = src.find("\n", i)
            if j < 0:
                j = length
            tokens.append(_Token("comment", src[i:j], line))
            i = j
            continue
        if char in ('"', "'") or char in _QUOTES:
            token_line = line
            value, end, line = _read_string(src, i, line)
            tokens.append(_Token("string", value, token_line))
            i = end
            continue
        match = _IDENT.match(src, i)
        if match:
            tokens.append(_Token("ident", match.group(), line))
            i = match.end()
            continue
        op = next((candidate for candidate in _MULTI_OPS
                   if src.startswith(candidate, i)), None)
        if op is not None:
            tokens.append(_Token("op", op, line))
            i += len(op)
            continue
        tokens.append(_Token("op", PUNCT.get(char, char), line))
        i += 1
    return tokens


def _lookup(name):
    """整词查表；查不到时返回 None。"""
    for table, _keys in _TABLES:
        if name in table:
            return table[name]
    return None


def _join_parts(parts):
    text = ""
    for part in parts:
        if text and part and _is_name_char(text[-1]) and _is_name_char(part[0]):
            text += " "
        text += part
    return text


def _split_identifier(name, at_line_start=False):
    """翻译中文词元，并保留无法识别的中文标识符。"""
    hit = _lookup(name)
    if hit is not None:
        return hit
    if not _CJK_RE.search(name) or len(name) == 1:
        return name

    for prefix, python in (("不是", "not"), ("并非", "not"), ("非", "not")):
        if name.startswith(prefix) and len(name) > len(prefix):
            tail = name[len(prefix):]
            return _join_parts((python, _split_identifier(tail, at_line_start)))

    for table, keys in _TABLES:
        for word in keys:
            if ("." in _WORD_ORIGIN.get(word, "")) and not at_line_start:
                continue
            if name.startswith(word) and len(name) > len(word):
                tail = name[len(word):]
                if _IDENT.fullmatch(tail) and _CJK_RE.search(word):
                    translated_tail = _split_identifier(tail, at_line_start)
                    return _join_parts((table[word], translated_tail))
    return name


def _next_significant(tokens, start):
    for token in tokens[start + 1:]:
        if token.kind not in ("space", "comment"):
            return token
        if token.kind == "newline":
            return None
    return None


def _statement_has_import(tokens, start):
    for token in tokens[start + 1:]:
        if token.kind == "newline":
            return False
        if token.kind == "ident" and token.text == "导入":
            return True
    return False


def _translate_identifier(
    token, tokens, index, after_dot, at_line_start, inside_brackets
):
    if after_dot:
        return ATTRS.get(token.text, token.text)

    next_token = _next_significant(tokens, index)
    if (
        inside_brackets
        and next_token is not None
        and next_token.kind == "op"
        and next_token.text == "="
    ):
        if token.text in KWARGS:
            return KWARGS[token.text]

    if at_line_start and token.text in _FROM_PREFIX:
        if not _statement_has_import(tokens, index):
            return "import"

    return _split_identifier(token.text, at_line_start=at_line_start)


def _is_name_char(char):
    return char.isalnum() or char == "_"


def _append_code(out, text):
    if out and text and _is_name_char(out[-1][-1]) and _is_name_char(text[0]):
        out.append(" ")
    out.append(text)


def translate(src):
    """把森林语言源码转换为保留原始行号的 Python 源码。"""
    src = (
        src.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\ufeff", "")
    )
    tokens = _scan_source(src)
    out = []
    after_dot = False
    at_line_start = True
    bracket_depth = 0

    for index, token in enumerate(tokens):
        if token.kind == "space":
            out.append(token.text)
            continue
        if token.kind == "newline":
            out.append("\n")
            after_dot = False
            at_line_start = True
            continue
        if token.kind in ("comment", "string"):
            out.append(token.text)
            at_line_start = False
            after_dot = False
            continue
        if token.kind == "ident":
            translated = _translate_identifier(
                token,
                tokens,
                index,
                after_dot,
                at_line_start and bracket_depth == 0,
                bracket_depth > 0,
            )
            _append_code(out, translated)
            after_dot = False
            at_line_start = False
            continue

        out.append(token.text)
        if token.text in ("(", "[", "{"):
            bracket_depth += 1
        elif token.text in (")", "]", "}") and bracket_depth:
            bracket_depth -= 1
        after_dot = token.text == "."
        at_line_start = False
    return "".join(out)


def translate_line(line, lineno=0):
    """翻译一行源码，供交互式工具和兼容旧 API 使用。"""
    try:
        return translate(line)
    except ForestError as error:
        message = str(error)
        if lineno and message.startswith("第 1 行"):
            message = "第 %d 行%s" % (lineno, message[len("第 1 行"):])
        raise ForestError(message) from None


def compile_src(src, filename="<森林>"):
    """翻译并编译源码，返回 ``(code, python_source)``。"""
    python_source = translate(src)
    try:
        code = compile(python_source, filename, "exec")
    except SyntaxError as error:
        line = error.lineno or 1
        source_lines = src.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        python_lines = python_source.split("\n")
        source_line = (
            source_lines[line - 1].strip() if line <= len(source_lines) else "?"
        )
        python_line = (
            python_lines[line - 1].strip() if line <= len(python_lines) else "?"
        )
        raise ForestError(
            "第 %d 行语法错误：%s\n    森林：%s\n    Python：%s"
            % (line, error.msg, source_line, python_line)
        ) from None
    return code, python_source


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) != 2:
        print("用法：python -m forestlang.tokenizer 文件.forest")
        raise SystemExit(2)
    with open(sys.argv[1], encoding="utf-8") as source_file:
        print(translate(source_file.read()))
