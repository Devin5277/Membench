"""支持 `python -m membench ...` 方式调用。"""
import sys

from membench.cli import main

if __name__ == "__main__":
    sys.exit(main())
