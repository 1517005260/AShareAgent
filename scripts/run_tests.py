#!/usr/bin/env python3
"""
测试运行脚本

提供不同类型测试的快速运行命令
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description=""):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=project_root, 
                              capture_output=False, text=True, check=True)
        print(f"\n✅ 成功: {description or cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 失败: {description or cmd}")
        print(f"错误码: {e.returncode}")
        return False


def run_unit_tests():
    """运行单元测试"""
    cmd = "python -m pytest tests/unit/ -v -m unit"
    return run_command(cmd, "单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = "python -m pytest tests/integration/ -v -m integration"
    return run_command(cmd, "集成测试")


def run_data_validation_tests():
    """运行数据验证测试"""
    cmd = "python -m pytest tests/data_validation/ -v -m data_validation"
    return run_command(cmd, "数据验证测试")


def run_performance_tests():
    """运行性能测试"""
    cmd = "python -m pytest tests/performance/ -v -m performance"
    return run_command(cmd, "性能测试")


def run_all_tests():
    """运行所有测试"""
    cmd = "python -m pytest tests/ -v"
    return run_command(cmd, "所有测试")


def run_fast_tests():
    """运行快速测试（排除慢速测试）"""
    cmd = "python -m pytest tests/ -v -m 'not slow'"
    return run_command(cmd, "快速测试")


def run_slow_tests():
    """运行慢速测试"""
    cmd = "python -m pytest tests/ -v -m slow"
    return run_command(cmd, "慢速测试")


def run_specific_test(test_path):
    """运行特定测试"""
    cmd = f"python -m pytest {test_path} -v"
    return run_command(cmd, f"特定测试: {test_path}")


def run_coverage_test():
    """运行带覆盖率的测试"""
    cmd = "python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing"
    return run_command(cmd, "覆盖率测试")


def run_parallel_tests():
    """运行并行测试"""
    cmd = "python -m pytest tests/ -n auto"
    return run_command(cmd, "并行测试")


def install_test_dependencies():
    """安装测试依赖"""
    deps = [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.0",
        "pytest-timeout>=2.1.0",
        "pytest-mock>=3.11.0"
    ]
    
    for dep in deps:
        cmd = f"pip install {dep}"
        success = run_command(cmd, f"安装依赖: {dep}")
        if not success:
            print(f"⚠️  依赖安装失败: {dep}")


def check_test_environment():
    """检查测试环境"""
    print("\n检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的包
    required_packages = ['pytest', 'pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装")
            missing_packages.append(package)
    
    # 检查测试目录
    test_dirs = ['tests/unit', 'tests/integration', 'tests/data_validation', 'tests/performance']
    for test_dir in test_dirs:
        dir_path = project_root / test_dir
        if dir_path.exists():
            test_files = list(dir_path.glob('test_*.py'))
            print(f"✅ {test_dir}: {len(test_files)} 个测试文件")
        else:
            print(f"❌ {test_dir}: 目录不存在")
    
    if missing_packages:
        print(f"\n⚠️  缺少包: {', '.join(missing_packages)}")
        print("请运行: python scripts/run_tests.py --install-deps")
    
    return len(missing_packages) == 0


def main():
    parser = argparse.ArgumentParser(description="A股Agent测试运行器")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--data-validation", action="store_true", help="运行数据验证测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--fast", action="store_true", help="运行快速测试")
    parser.add_argument("--slow", action="store_true", help="运行慢速测试")
    parser.add_argument("--coverage", action="store_true", help="运行覆盖率测试")
    parser.add_argument("--parallel", action="store_true", help="运行并行测试")
    parser.add_argument("--test", type=str, help="运行特定测试文件或目录")
    parser.add_argument("--install-deps", action="store_true", help="安装测试依赖")
    parser.add_argument("--check-env", action="store_true", help="检查测试环境")
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # 检查环境
    if args.check_env:
        check_test_environment()
        return
    
    # 安装依赖
    if args.install_deps:
        install_test_dependencies()
        return
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    success_count = 0
    total_count = 0
    
    # 运行测试
    if args.unit:
        total_count += 1
        if run_unit_tests():
            success_count += 1
    
    if args.integration:
        total_count += 1
        if run_integration_tests():
            success_count += 1
    
    if args.data_validation:
        total_count += 1
        if run_data_validation_tests():
            success_count += 1
    
    if args.performance:
        total_count += 1
        if run_performance_tests():
            success_count += 1
    
    if args.all:
        total_count += 1
        if run_all_tests():
            success_count += 1
    
    if args.fast:
        total_count += 1
        if run_fast_tests():
            success_count += 1
    
    if args.slow:
        total_count += 1
        if run_slow_tests():
            success_count += 1
    
    if args.coverage:
        total_count += 1
        if run_coverage_test():
            success_count += 1
    
    if args.parallel:
        total_count += 1
        if run_parallel_tests():
            success_count += 1
    
    if args.test:
        total_count += 1
        if run_specific_test(args.test):
            success_count += 1
    
    # 显示结果摘要
    if total_count > 0:
        print(f"\n{'='*60}")
        print(f"测试结果摘要: {success_count}/{total_count} 成功")
        print(f"{'='*60}")
        
        if success_count == total_count:
            print("🎉 所有测试都成功完成！")
            sys.exit(0)
        else:
            print("❌ 部分测试失败")
            sys.exit(1)


if __name__ == "__main__":
    main()