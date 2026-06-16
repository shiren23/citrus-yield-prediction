"""
柑橘产量预测系统 - 入口
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.factory import create_ui, launch_app


def main():
    launch_app()


if __name__ == "__main__":
    main()
