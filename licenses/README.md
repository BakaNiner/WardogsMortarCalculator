# 第三方许可 / Third-party notices

本目录记录第三方组件的许可，不替代项目顶层许可证。`third_party/` 内的包版本及许可从 `requirements-lock.txt` 对应的已安装依赖收集；它也包含构建工具的许可。请随程序分发保留这些文件。

This directory records third-party licenses and does not replace the top-level project license. Package versions and notices in `third_party/` are collected from installed dependencies listed in `requirements-lock.txt`, including build tools. Preserve these files with distributions.

- **L81 射表 / Firing table**：[Apollyon / wardogs-calculator](https://github.com/apollyon-sys/wardogs-calculator)，MIT，见 `Apollyon-MIT.txt`。仅使用数值射表。 / MIT; see `Apollyon-MIT.txt`. Only the numerical firing table is used.
- **Python**：打包的解释器许可见 `Python-LICENSE.txt`，由构建环境复制。 / The bundled interpreter's license is copied from the build environment to `Python-LICENSE.txt`.
- **PySide6、Shiboken6 与 Qt / PySide6, Shiboken6, and Qt**：使用动态库，组件版本见对应 `PACKAGE.txt`；保留 `LGPL-3.0.txt` 和其引用的 `GPL-3.0.txt`。上游包附带的商业许可文本也按原样保留，不表示本项目拥有 Qt 商业授权。 / Shared libraries are used; see the relevant `PACKAGE.txt` for versions. `LGPL-3.0.txt` and the referenced `GPL-3.0.txt` are included. Upstream commercial-license notices are preserved as supplied and do not imply that this project holds a Qt commercial license.
- **OCR 与其他依赖 / OCR and other dependencies**：RapidOCR、ONNX Runtime、OpenCV、MSS、NumPy 等的许可见 `third_party/`。 / See `third_party/` for the licenses of RapidOCR, ONNX Runtime, OpenCV, MSS, NumPy, and other dependencies.

Qt/PySide/Shiboken 未作修改。对应版本源码可从 [Qt 源码归档](https://download.qt.io/archive/qt/) 与 [Qt for Python 源码归档](https://download.qt.io/official_releases/QtForPython/) 获取；版本号见包清单。Qt 动态库位于程序的 `_internal/PySide6/`；用户可以使用兼容接口的修改版本替换，或按项目 README 从源码重新构建。允许为调试这些库的修改而进行逆向工程。分发时应保留许可，并按所用组件条款提供相应源码的获取方式。

Qt/PySide/Shiboken are unmodified. Matching source versions are available from the [Qt source archive](https://download.qt.io/archive/qt/) and [Qt for Python source archive](https://download.qt.io/official_releases/QtForPython/); consult the package records for version numbers. Qt shared libraries reside in `_internal/PySide6/`. Users may replace them with interface-compatible modified versions or rebuild the application using the project README. Reverse engineering for debugging modifications to these libraries is permitted. Preserve notices and provide corresponding source access as required by the component licenses when redistributing.

许可文本来源：[GNU LGPL v3](https://www.gnu.org/licenses/lgpl-3.0.txt)、[GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.txt)。更多说明：[Qt 许可](https://doc.qt.io/qt-6/licensing.html)、[Qt for Python 第三方许可](https://doc.qt.io/qtforpython-6/licenses.html)。

License-text sources: [GNU LGPL v3](https://www.gnu.org/licenses/lgpl-3.0.txt) and [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.txt). Further information: [Qt licensing](https://doc.qt.io/qt-6/licensing.html) and [Qt for Python third-party notices](https://doc.qt.io/qtforpython-6/licenses.html).
