# -*- coding: utf-8 -*-

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from forestlang import ForestError, __version__, compile_src, translate


ROOT = Path(__file__).resolve().parents[1]


def run_source(source):
    code, _python_source = compile_src(source, filename="<测试>")
    output = StringIO()
    with redirect_stdout(output):
        exec(code, {"__name__": "__main__"})
    return output.getvalue()


class TranslationTests(unittest.TestCase):
    def test_version_matches_package_metadata(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)

    def test_core_control_flow_and_recursion(self):
        source = """
定义 阶乘(数):
    如果 数 <= 1:
        返回 1
    返回 数 * 阶乘(数 - 1)

总和 = 0
对于 数 于 范围(1, 5):
    总和 加等于 数
打印(阶乘(5), 总和)
"""
        self.assertEqual(run_source(source).strip(), "120 10")

    def test_multiline_literals_and_chinese_quotes(self):
        source = """
文本 = “森林语言”
项目 = [
    “一”,
    “二”,
]
说明 = \"\"\"第一行
如果 这段文字不应被翻译
\"\"\"
打印(文本, 长度(项目), 说明.去除空格())
"""
        self.assertEqual(
            run_source(source).strip(),
            "森林语言 2 第一行\n如果 这段文字不应被翻译",
        )

    def test_import_aliases(self):
        source = """
导入 数学 作为 数
来自 数学
打印(数.ceil(1.2), 数学.floor(1.8))
"""
        self.assertEqual(run_source(source).strip(), "2 1")

    def test_keyword_arguments(self):
        source = """
参数 = 7
打印(参数)
打印("甲", "乙", 分隔符="|", 结束="!")
"""
        self.assertEqual(run_source(source), "7\n甲|乙!")

    def test_strings_are_not_translated(self):
        source = '打印("如果 分数 大于等于 90 并且 真")\n'
        translated = translate(source)
        self.assertIn('"如果 分数 大于等于 90 并且 真"', translated)
        self.assertEqual(run_source(source).strip(), "如果 分数 大于等于 90 并且 真")

    def test_syntax_error_reports_source_line(self):
        with self.assertRaisesRegex(ForestError, "第 2 行语法错误"):
            compile_src("跳过\n如果 真\n    跳过\n")


class CliTests(unittest.TestCase):
    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "forestlang", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_cli_run_check_and_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "参数.forest"
            path.write_text(
                "导入 系统\n打印(系统.argv[1:])\n",
                encoding="utf-8",
            )

            check = self._run_cli("--检查", str(path))
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("语法检查通过", check.stdout)

            result = self._run_cli(str(path), "--", "甲", "乙")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "['甲', '乙']")

    def test_runtime_error_contains_forest_location(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "错误.forest"
            path.write_text(
                "定义 失败():\n    返回 1 / 0\n失败()\n",
                encoding="utf-8",
            )
            result = self._run_cli(str(path))

        self.assertEqual(result.returncode, 1)
        self.assertIn("ZeroDivisionError", result.stderr)
        self.assertIn("位置：", result.stderr)
        self.assertIn("错误.forest:2", result.stderr)
        self.assertIn("返回 1 / 0", result.stderr)


if __name__ == "__main__":
    unittest.main()
