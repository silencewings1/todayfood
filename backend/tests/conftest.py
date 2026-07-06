"""pytest 配置：把 backend/ 加入 sys.path，便于 import app.*"""
import sys
import os

# tests 目录的上一级（backend/）加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
