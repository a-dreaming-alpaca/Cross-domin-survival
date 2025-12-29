"""
在项目最顶层的启动钩子：
- 立即设置 `sys.pycache_prefix` 指向项目的 `.cache` 文件夹
- 创建 `.cache`（如果不存在）
- 将已有的 `__pycache__` 中的文件迁移到 `.cache`（best-effort）

使用方式：在任何其他模块导入前先执行 `import pycache_init`。
"""
import os
import sys
import shutil

# project root 是本文件所在目录
project_root = os.path.dirname(os.path.abspath(__file__))
pycache_dir = os.path.join(project_root, ".cache")
try:
    if not os.path.exists(pycache_dir):
        os.makedirs(pycache_dir, exist_ok=True)
    sys.pycache_prefix = pycache_dir
except Exception:
    # 忽略设置失败，继续执行（best-effort）
    pass

# 将旧的 __pycache__ 文件迁移到 .cache
old_cache = os.path.join(project_root, "__pycache__")
try:
    if os.path.exists(old_cache) and os.path.isdir(old_cache):
        for name in os.listdir(old_cache):
            src = os.path.join(old_cache, name)
            dst = os.path.join(pycache_dir, name)
            try:
                shutil.move(src, dst)
            except Exception:
                pass
        try:
            os.rmdir(old_cache)
        except Exception:
            pass
except Exception:
    pass

# 可选地，向外导出当前使用的 pycache 路径
CURRENT_PYCACHE_DIR = getattr(sys, 'pycache_prefix', None) or pycache_dir
