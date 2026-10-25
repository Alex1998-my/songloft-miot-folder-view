此目录包含可复现构建脚本和通用安装器。

- `build.py`：使用 Python 3 标准库，从 `vendor/` 固定版本发行包应用前端定制并生成 `dist/` 文件。
- `install.py`：在 macOS 上运行，输入自己的 Songloft 地址及登录信息后完成上传和版本核验。凭据不会写入文件。
