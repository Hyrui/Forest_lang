# 森林语言

森林语言是一套使用中文关键字和可读运算符的编程语言。源码会被转换为
Python 后执行，因此可以直接使用 Python 的数据类型、标准库和第三方库。

当前版本：`0.3.1`（可用 MVP）

GitHub 仓库：<https://github.com/Hyrui/Forest_lang>

## 安装

需要 Python 3.9 或更高版本。

从源码目录安装：

```powershell
python -m pip install .
```

开发模式，并安装构建和发布工具：

```powershell
python -m pip install -e ".[dev]"
```

安装本地构建的 wheel：

```powershell
python -m pip install .\dist\forestlang-0.3.1-py3-none-any.whl
```

发行到 PyPI 或私有软件源后，可以执行：

```powershell
python -m pip install forestlang
python -m pip install --upgrade forestlang
```

安装完成后运行：

```powershell
森林 .\示例.forest
```

`forestlang` 是等价的 ASCII 命令，适合不方便输入中文命令的终端：

```powershell
forestlang .\示例.forest
```

最小示例：

```text
定义 问候(名字):
    返回 "你好，" + 名字

打印(问候("森林"))
```

## 当前能力

- 变量、表达式、函数、递归、类和异常。
- `如果 / 否则如果 / 否则`、`当`、`对于` 等控制流。
- 中文关键字参数、中文变量名和函数名。
- 中文运算符及常用模块、内置函数、属性和方法别名。
- 多行列表、字典、调用、多行字符串和中文引号。
- 森林源码行号语法检查与运行时错误定位。
- 脚本参数传递、语法检查和 Python 源码查看。

完整语法与命令见 [使用说明.md](使用说明.md)。

## 常用命令

```powershell
森林 文件.forest
forestlang 文件.forest
森林 --检查 文件.forest
森林 --输出py 文件.forest
森林 文件.forest -- 参数一 参数二
森林 --版本
```

## 运行测试

```powershell
python -m unittest discover -s tests -v
```

## 构建发行包

```powershell
python -m pip install -e ".[dev]"
python -m build
python -m twine check .\dist\*
```

发布到 TestPyPI、PyPI 以及安装发行版的完整流程见
[发布说明.md](发布说明.md)。

本项目使用 MIT 许可证，详见 [LICENSE](LICENSE)。

## 说明

森林语言目前以 Python 作为运行时和目标语义，不是独立虚拟机。未提供中文
别名的名称仍可直接使用 Python 写法，因此 Python 生态中的功能不会被语言
层隔断。
