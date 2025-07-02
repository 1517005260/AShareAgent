#!/usr/bin/env python3
"""
主测试运行脚本：运行完整的测试套件

这个脚本会：
1. 检查测试环境
2. 运行所有测试
3. 生成测试报告
4. 验证结果

使用方法:
    python run_tests.py                  # 运行所有测试
    python run_tests.py --fast           # 快速测试（跳过慢速测试）
    python run_tests.py --unit-only      # 只运行单元测试
    python run_tests.py --integration    # 只运行集成测试
    python run_tests.py --coverage       # 生成覆盖率报告
"""

import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='运行测试套件')
    parser.add_argument('--fast', action='store_true', help='快速模式，跳过慢速测试')
    parser.add_argument('--unit-only', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--performance', action='store_true', help='只运行性能测试')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--report', action='store_true', help='生成详细报告')
    parser.add_argument('--fix', action='store_true', help='自动修复可修复的问题')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent
    
    # 检查是否使用poetry
    if (project_root / 'poetry.lock').exists():
        pytest_cmd = ['poetry', 'run', 'pytest']
    else:
        pytest_cmd = ['python', '-m', 'pytest']
    
    # 基础参数
    cmd_args = ['-v', '--tb=short']
    
    # 根据参数决定测试范围
    if args.unit_only:
        cmd_args.append('tests/unit/')
    elif args.integration:
        cmd_args.append('tests/integration/')
    elif args.performance:
        cmd_args.append('tests/performance/')
    else:
        cmd_args.append('tests/')
    
    # 快速模式
    if args.fast:
        cmd_args.extend(['-m', 'not slow'])
    
    # 覆盖率报告
    if args.coverage:
        cmd_args.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html',
            '--cov-report=json'
        ])
    
    # 构建完整命令
    full_cmd = pytest_cmd + cmd_args
    
    print(f"运行命令: {' '.join(full_cmd)}")
    print("=" * 60)
    
    try:
        # 运行测试
        result = subprocess.run(full_cmd, cwd=project_root)
        
        # 如果需要生成报告，运行验证脚本
        if args.report or result.returncode != 0:
            print("\n" + "=" * 60)
            print("运行测试验证脚本...")
            
            validation_args = ['python', 'scripts/validate_tests.py']
            if args.fast:
                validation_args.append('--fast')
            if args.coverage:
                validation_args.append('--coverage')
            if args.fix:
                validation_args.append('--fix')
            
            subprocess.run(validation_args, cwd=project_root)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())