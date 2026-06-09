import os
import sys

# Make the project root importable so `import cleanvey` works under pytest.
# 把项目根目录加入导入路径，使 pytest 下 `import cleanvey` 可用。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
