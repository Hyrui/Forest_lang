# -*- coding: utf-8 -*-
"""森林语言命令行入口。

用法：
    森林 文件.forest
    森林 --检查 文件.forest
    森林 --输出py 文件.forest
    森林 文件.forest -- 程序参数
"""

from pathlib import Path
import sys
import traceback

from . import ForestError, __version__, compile_src, translate


def _configure_streams():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _parse_args(argv):
    mode = "run"
    files = []
    program_args = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--":
            program_args = argv[index + 1:]
            break
        if argument in ("-h", "--help", "--帮助"):
            return "help", [], []
        if argument in ("-V", "--version", "--版本"):
            return "version", [], []
        if argument in ("--输出py", "--py", "--翻译"):
            mode = "translate"
        elif argument in ("--检查", "--check"):
            if mode == "translate":
                return "conflict", [], []
            mode = "check"
        else:
            files.append(argument)
        index += 1
    return mode, files, program_args


def _runtime_location(error, path):
    target = Path(path).resolve()
    for frame in reversed(traceback.extract_tb(error.__traceback__)):
        try:
            same_file = Path(frame.filename).resolve() == target
        except (OSError, ValueError):
            same_file = frame.filename == path
        if same_file:
            return frame.lineno
    return None


def _print_runtime_error(error, path):
    line = _runtime_location(error, path)
    print(
        "✗ 运行出错：%s: %s" % (type(error).__name__, error),
        file=sys.stderr,
    )
    if line is None:
        return
    try:
        source = Path(path).read_text(encoding="utf-8").splitlines()
        source_line = source[line - 1].strip() if 0 < line <= len(source) else ""
    except OSError:
        source_line = ""
    print("  位置：%s:%d" % (path, line), file=sys.stderr)
    if source_line:
        print("  源码：%s" % source_line, file=sys.stderr)


def main(argv=None):
    _configure_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    mode, files, program_args = _parse_args(argv)

    if mode == "help":
        print(__doc__)
        return 0
    if mode == "version":
        print("森林语言 %s" % __version__)
        return 0
    if mode == "conflict":
        print("✗ --检查 与 --输出py 不能同时使用", file=sys.stderr)
        return 2
    if not files:
        print(__doc__)
        return 2

    for path in files:
        try:
            source = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            print("✗ 打不开 %s：%s" % (path, error), file=sys.stderr)
            return 1

        try:
            if mode == "translate":
                print("===== %s 翻译结果 =====" % path)
                print(translate(source))
                continue

            code, _python_source = compile_src(source, filename=path)
            if mode == "check":
                print("✓ %s 语法检查通过" % path)
                continue

            original_argv = sys.argv
            sys.argv = [path, *program_args]
            try:
                globals_dict = {
                    "__name__": "__main__",
                    "__file__": path,
                    "__package__": None,
                }
                exec(code, globals_dict)
            finally:
                sys.argv = original_argv
        except ForestError as error:
            print("✗ %s" % error, file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("✗ 程序已中断", file=sys.stderr)
            return 130
        except Exception as error:
            _print_runtime_error(error, path)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
