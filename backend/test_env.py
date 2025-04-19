"""
环境变量测试脚本
"""

import os
import sys

def main():
    """打印重要的环境变量"""
    print("===== 环境变量值 =====")
    print(f"SEVENDIGITAL_API_KEY: {os.environ.get('SEVENDIGITAL_API_KEY', '未设置')}")
    print(f"SEVENDIGITAL_API_SECRET: {os.environ.get('SEVENDIGITAL_API_SECRET', '未设置')}")
    print(f"DIGITAL7_API_KEY: {os.environ.get('DIGITAL7_API_KEY', '未设置')}")
    print("=====================")

if __name__ == "__main__":
    main() 