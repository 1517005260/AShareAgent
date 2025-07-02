#!/usr/bin/env python3
"""
测试运行器

提供不同类型的测试运行命令和配置
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """运行命令并处理输出"""
    print(f"\n{'='*60}")
    print(f"执行: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"\n✅ {description or cmd} 执行成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or cmd} 执行失败: {e}")
        return False


def run_unit_tests():
    """运行单元测试"""
    cmd = "python -m pytest tests/unit/ -m unit -v --tb=short"
    return run_command(cmd, "单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = "python -m pytest tests/integration/ -m integration -v --tb=short"
    return run_command(cmd, "集成测试")


def run_data_validation_tests():
    """运行数据验证测试"""
    cmd = "python -m pytest tests/data_validation/ -m data_validation -v --tb=short"
    return run_command(cmd, "数据验证测试")


def run_performance_tests():
    """运行性能测试"""
    cmd = "python -m pytest tests/performance/ -m performance -v --tb=short"
    return run_command(cmd, "性能测试")


def run_smoke_tests():
    """运行冒烟测试（快速验证）"""
    cmd = "python -m pytest -m smoke -v --tb=short --durations=5"
    return run_command(cmd, "冒烟测试")


def run_all_tests():
    """运行所有测试"""
    cmd = "python -m pytest tests/ -v --tb=short"
    return run_command(cmd, "全部测试")


def run_coverage_tests():
    """运行测试并生成覆盖率报告"""
    cmd = (
        "python -m pytest tests/ "
        "--cov=src "
        "--cov-report=html:tests/reports/coverage "
        "--cov-report=term-missing "
        "--cov-fail-under=70 "
        "-v --tb=short"
    )
    return run_command(cmd, "覆盖率测试")


def run_specific_test(test_path):
    """运行特定测试"""
    cmd = f"python -m pytest {test_path} -v --tb=short"
    return run_command(cmd, f"特定测试: {test_path}")


def run_tests_by_keyword(keyword):
    """按关键词运行测试"""
    cmd = f"python -m pytest -k '{keyword}' -v --tb=short"
    return run_command(cmd, f"关键词测试: {keyword}")


def run_failed_tests():
    """重新运行上次失败的测试"""
    cmd = "python -m pytest --lf -v --tb=short"
    return run_command(cmd, "重新运行失败的测试")


def setup_test_environment():
    """设置测试环境"""
    print("设置测试环境...")
    
    # 确保测试报告目录存在
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理之前的测试缓存
    cache_dir = Path(".pytest_cache")
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        print("✅ 清理测试缓存")
    
    # 确保必要的环境变量
    os.environ.setdefault("PYTHONPATH", ".")
    print("✅ 设置PYTHONPATH")
    
    print("✅ 测试环境设置完成")


def clean_test_artifacts():
    """清理测试产生的文件"""
    print("清理测试文件...")
    
    artifacts = [
        ".pytest_cache",
        "tests/reports",
        ".coverage",
        "htmlcov",
        "**/__pycache__",
        "**/*.pyc"
    ]
    
    for pattern in artifacts:
        if pattern.startswith("**"):
            # 使用glob处理通配符
            from pathlib import Path
            for path in Path(".").rglob(pattern[3:]):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
        else:
            path = Path(pattern)
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
    
    print("✅ 清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="A股Agent测试运行器")
    parser.add_argument("--setup", action="store_true", help="设置测试环境")
    parser.add_argument("--clean", action="store_true", help="清理测试文件")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--data", action="store_true", help="运行数据验证测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--smoke", action="store_true", help="运行冒烟测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--coverage", action="store_true", help="运行覆盖率测试")
    parser.add_argument("--failed", action="store_true", help="重新运行失败的测试")
    parser.add_argument("--test", type=str, help="运行特定测试文件")
    parser.add_argument("--keyword", "-k", type=str, help="按关键词运行测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    success = True
    
    # 设置测试环境
    if args.setup or not Path("tests/reports").exists():
        setup_test_environment()
    
    # 执行测试
    if args.clean:
        clean_test_artifacts()
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.data:
        success = run_data_validation_tests()
    elif args.performance:
        success = run_performance_tests()
    elif args.smoke:
        success = run_smoke_tests()
    elif args.all:
        success = run_all_tests()
    elif args.coverage:
        success = run_coverage_tests()
    elif args.failed:
        success = run_failed_tests()
    elif args.test:
        success = run_specific_test(args.test)
    elif args.keyword:
        success = run_tests_by_keyword(args.keyword)
    
    # 退出状态
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()