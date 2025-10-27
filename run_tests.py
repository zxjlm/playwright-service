#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本
"""

import subprocess
import sys
import os


def run_tests():
    """运行所有测试"""
    print("🚀 开始运行单元测试...")
    
    # 确保在项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行测试命令
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=apis",
        "--cov=utils",
        "--cov=base_proxy",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ 所有测试通过!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试失败: {e}")
        return e.returncode


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    print(f"🚀 运行测试文件: {test_file}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ {test_file} 测试通过!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ {test_file} 测试失败: {e}")
        return e.returncode


def run_unit_tests_only():
    """只运行单元测试"""
    print("🚀 运行单元测试...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "not integration"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ 单元测试通过!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ 单元测试失败: {e}")
        return e.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            sys.exit(run_unit_tests_only())
        elif sys.argv[1].endswith(".py"):
            sys.exit(run_specific_test(sys.argv[1]))
        else:
            print("用法: python run_tests.py [unit|test_file.py]")
            sys.exit(1)
    else:
        sys.exit(run_tests())
