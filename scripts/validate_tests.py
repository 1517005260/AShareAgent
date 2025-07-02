#!/usr/bin/env python3
"""
测试验证脚本：自动运行所有测试并生成报告

功能:
1. 运行全部测试套件
2. 生成测试报告
3. 验证测试结果
4. 检查代码覆盖率
5. 生成性能分析

使用方法:
    python scripts/validate_tests.py [options]
    
参数:
    --fast: 快速模式，跳过慢速测试
    --coverage: 生成覆盖率报告
    --report: 生成详细报告
    --fix: 自动修复可修复的问题
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestValidator:
    """测试验证器"""
    
    def __init__(self, fast_mode: bool = False, with_coverage: bool = False, 
                 generate_report: bool = True, auto_fix: bool = False):
        self.project_root = project_root
        self.fast_mode = fast_mode
        self.with_coverage = with_coverage
        self.generate_report = generate_report
        self.auto_fix = auto_fix
        
        self.reports_dir = project_root / 'tests' / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'project_info': self._get_project_info(),
            'configuration': {
                'fast_mode': fast_mode,
                'with_coverage': with_coverage,
                'auto_fix': auto_fix
            },
            'test_results': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'error_tests': 0,
                'skipped_tests': 0,
                'execution_time': 0,
                'success_rate': 0
            },
            'issues': [],
            'recommendations': []
        }
    
    def run_validation(self) -> bool:
        """运行完整的测试验证"""
        print("\n🚀 开始测试验证...")
        start_time = time.time()
        
        success = True
        
        try:
            # 1. 环境检查
            print("\n1️⃣ 检查环境...")
            if not self._check_environment():
                success = False
            
            # 2. 运行单元测试
            print("\n2️⃣ 运行单元测试...")
            unit_result = self._run_unit_tests()
            self.validation_results['test_results']['unit_tests'] = unit_result
            if not unit_result['success']:
                success = False
            
            # 3. 运行集成测试
            print("\n3️⃣ 运行集成测试...")
            integration_result = self._run_integration_tests()
            self.validation_results['test_results']['integration_tests'] = integration_result
            if not integration_result['success']:
                success = False
            
            # 4. 运行数据验证测试
            print("\n4️⃣ 运行数据验证测试...")
            data_validation_result = self._run_data_validation_tests()
            self.validation_results['test_results']['data_validation'] = data_validation_result
            if not data_validation_result['success']:
                success = False
            
            # 5. 运行性能测试（如果不是快速模式）
            if not self.fast_mode:
                print("\n5️⃣ 运行性能测试...")
                performance_result = self._run_performance_tests()
                self.validation_results['test_results']['performance'] = performance_result
                if not performance_result['success']:
                    success = False
            
            # 6. 代码质量检查
            print("\n6️⃣ 检查代码质量...")
            quality_result = self._check_code_quality()
            self.validation_results['test_results']['code_quality'] = quality_result
            if not quality_result['success'] and not self.auto_fix:
                success = False
            
            # 7. 生成覆盖率报告（如果需要）
            if self.with_coverage:
                print("\n7️⃣ 生成覆盖率报告...")
                coverage_result = self._generate_coverage_report()
                self.validation_results['test_results']['coverage'] = coverage_result
            
            # 8. 统计结果
            self._calculate_summary()
            
        except Exception as e:
            print(f"\n❗ 验证过程发生错误: {e}")
            self.validation_results['issues'].append(f"验证过程错误: {e}")
            success = False
        
        # 记录执行时间
        self.validation_results['summary']['execution_time'] = time.time() - start_time
        
        # 9. 生成报告
        if self.generate_report:
            print("\n8️⃣ 生成验证报告...")
            self._generate_final_report()
        
        # 10. 显示结果
        self._display_summary(success)
        
        return success
    
    def _check_environment(self) -> bool:
        """检查环境配置"""
        success = True
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 9):
            self.validation_results['issues'].append(f"Python版本过低: {python_version}, 需要 >= 3.9")
            success = False
        
        # 检查必要的文件
        required_files = [
            'pyproject.toml',
            'src/__init__.py',
            'tests/__init__.py',
            'tests/conftest.py'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                self.validation_results['issues'].append(f"缺失必要文件: {file_path}")
                success = False
        
        # 检查依赖
        try:
            import pytest
            import pandas
            import numpy
            print("  ✅ 所有依赖已安装")
        except ImportError as e:
            self.validation_results['issues'].append(f"缺失依赖: {e}")
            success = False
        
        return success
    
    def _run_unit_tests(self) -> Dict[str, Any]:
        """运行单元测试"""
        cmd = ['python', '-m', 'pytest', 'tests/unit/', '-v', '--tb=short']
        
        if self.fast_mode:
            cmd.extend(['-x'])  # 遇到第一个失败就停止
        
        result = self._run_command(cmd)
        stats = self._parse_pytest_output(result['stdout'])
        
        return {
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stats': stats,
            'duration': result.get('duration', 0),
            'success': result['returncode'] == 0 and stats['failed'] == 0,
            'output': result['stdout'][-1000:] if len(result['stdout']) > 1000 else result['stdout']
        }
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        cmd = ['python', '-m', 'pytest', 'tests/integration/', '-v', '--tb=short']
        
        if self.fast_mode:
            cmd.extend(['-m', 'not slow'])
        
        result = self._run_command(cmd)
        stats = self._parse_pytest_output(result['stdout'])
        
        return {
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stats': stats,
            'duration': result.get('duration', 0),
            'success': result['returncode'] == 0 and stats['failed'] == 0,
            'output': result['stdout'][-1000:] if len(result['stdout']) > 1000 else result['stdout']
        }
    
    def _run_data_validation_tests(self) -> Dict[str, Any]:
        """运行数据验证测试"""
        cmd = ['python', '-m', 'pytest', 'tests/data_validation/', '-v', '--tb=short']
        
        result = self._run_command(cmd)
        stats = self._parse_pytest_output(result['stdout'])
        
        return {
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stats': stats,
            'duration': result.get('duration', 0),
            'success': result['returncode'] == 0 and stats['failed'] == 0,
            'output': result['stdout'][-1000:] if len(result['stdout']) > 1000 else result['stdout']
        }
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
        cmd = ['python', '-m', 'pytest', 'tests/performance/', '-v', '--tb=short', '--durations=10']
        
        result = self._run_command(cmd)
        stats = self._parse_pytest_output(result['stdout'])
        
        return {
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'stats': stats,
            'duration': result.get('duration', 0),
            'success': result['returncode'] == 0 and stats['failed'] == 0,
            'output': result['stdout'][-1000:] if len(result['stdout']) > 1000 else result['stdout']
        }
    
    def _check_code_quality(self) -> Dict[str, Any]:
        """检查代码质量"""
        issues = []
        checks_performed = []
        
        # 检查flake8
        if self._has_command('flake8'):
            flake8_result = self._run_command(['flake8', 'src/', 'tests/', '--max-line-length=100'])
            checks_performed.append('flake8')
            if flake8_result['returncode'] != 0:
                issues.append(f"Flake8代码质量问题")
                if self.auto_fix:
                    print("    🔧 尝试修复flake8问题...")
                    # 这里可以添加自动修复逻辑
        
        # 检查black代码格式
        if self._has_command('black'):
            black_result = self._run_command(['black', '--check', 'src/', 'tests/'])
            checks_performed.append('black')
            if black_result['returncode'] != 0:
                issues.append("Black代码格式不符合要求")
                if self.auto_fix:
                    print("    🔧 自动修复代码格式...")
                    fix_result = self._run_command(['black', 'src/', 'tests/'])
                    if fix_result['returncode'] == 0:
                        issues.remove("Black代码格式不符合要求")
                        print("      ✅ 代码格式已修复")
        
        # 检查isort导入排序
        if self._has_command('isort'):
            isort_result = self._run_command(['isort', '--check-only', 'src/', 'tests/'])
            checks_performed.append('isort')
            if isort_result['returncode'] != 0:
                issues.append("Isort导入排序不符合要求")
                if self.auto_fix:
                    print("    🔧 自动修复导入排序...")
                    fix_result = self._run_command(['isort', 'src/', 'tests/'])
                    if fix_result['returncode'] == 0:
                        issues.remove("Isort导入排序不符合要求")
                        print("      ✅ 导入排序已修复")
        
        return {
            'checks_performed': checks_performed,
            'issues': issues,
            'issues_count': len(issues),
            'success': len(issues) == 0
        }
    
    def _generate_coverage_report(self) -> Dict[str, Any]:
        """生成覆盖率报告"""
        cmd = [
            'python', '-m', 'pytest', 
            'tests/',
            '--cov=src',
            '--cov-report=term',
            '--cov-report=html',
            '--cov-report=json',
            '--cov-fail-under=50'
        ]
        
        if self.fast_mode:
            cmd.extend(['-m', 'not slow'])
        
        result = self._run_command(cmd)
        
        # 解析覆盖率数据
        coverage_data = self._parse_coverage_data()
        
        return {
            'command': ' '.join(cmd),
            'returncode': result['returncode'],
            'coverage_data': coverage_data,
            'success': result['returncode'] == 0
        }
    
    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """运行命令并返回结果"""
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            duration = time.time() - start_time
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timeout after 300 seconds',
                'duration': 300
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """解析pytest输出统计信息"""
        stats = {
            'passed': 0,
            'failed': 0,
            'error': 0,
            'skipped': 0,
            'warnings': 0
        }
        
        lines = output.strip().split('\n')
        for line in reversed(lines):
            if any(keyword in line for keyword in ['passed', 'failed', 'error', 'skipped']):
                # 解析类似 "5 passed, 1 failed" 的格式
                import re
                
                passed_match = re.search(r'(\d+)\s+passed', line)
                if passed_match:
                    stats['passed'] = int(passed_match.group(1))
                
                failed_match = re.search(r'(\d+)\s+failed', line)
                if failed_match:
                    stats['failed'] = int(failed_match.group(1))
                
                error_match = re.search(r'(\d+)\s+error', line)
                if error_match:
                    stats['error'] = int(error_match.group(1))
                
                skipped_match = re.search(r'(\d+)\s+skipped', line)
                if skipped_match:
                    stats['skipped'] = int(skipped_match.group(1))
                
                warnings_match = re.search(r'(\d+)\s+warning', line)
                if warnings_match:
                    stats['warnings'] = int(warnings_match.group(1))
                
                break
        
        return stats
    
    def _parse_coverage_data(self) -> Dict[str, Any]:
        """解析覆盖率数据"""
        coverage_json_file = self.project_root / 'coverage.json'
        if coverage_json_file.exists():
            try:
                with open(coverage_json_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _calculate_summary(self):
        """计算测试统计摘要"""
        summary = self.validation_results['summary']
        
        for test_type, result in self.validation_results['test_results'].items():
            if 'stats' in result:
                stats = result['stats']
                summary['total_tests'] += stats['passed'] + stats['failed'] + stats['error']
                summary['passed_tests'] += stats['passed']
                summary['failed_tests'] += stats['failed']
                summary['error_tests'] += stats['error']
                summary['skipped_tests'] += stats['skipped']
        
        # 计算成功率
        if summary['total_tests'] > 0:
            summary['success_rate'] = (summary['passed_tests'] / summary['total_tests']) * 100
    
    def _generate_final_report(self):
        """生成最终报告"""
        # 生成JSON报告
        json_report_file = self.reports_dir / f'test_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        html_report_file = self.reports_dir / f'test_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        self._generate_html_report(html_report_file)
        
        print(f"  📄 JSON报告: {json_report_file}")
        print(f"  📊 HTML报告: {html_report_file}")
    
    def _generate_html_report(self, output_file: Path):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>测试验证报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .warning {{ color: orange; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 测试验证报告</h1>
        <p><strong>生成时间:</strong> {self.validation_results['timestamp']}</p>
        <p><strong>项目:</strong> {self.validation_results['project_info']['name']}</p>
    </div>
    
    <div class="section">
        <h2>📊 测试概览</h2>
        <div class="metric">
            <h3>{self.validation_results['summary']['total_tests']}</h3>
            <p>总测试数</p>
        </div>
        <div class="metric">
            <h3 class="success">{self.validation_results['summary']['passed_tests']}</h3>
            <p>通过</p>
        </div>
        <div class="metric">
            <h3 class="failure">{self.validation_results['summary']['failed_tests']}</h3>
            <p>失败</p>
        </div>
        <div class="metric">
            <h3>{self.validation_results['summary']['skipped_tests']}</h3>
            <p>跳过</p>
        </div>
        <div class="metric">
            <h3>{self.validation_results['summary']['success_rate']:.1f}%</h3>
            <p>成功率</p>
        </div>
    </div>
    
    <div class="section">
        <h2>📄 测试结果详情</h2>
        <table>
            <tr>
                <th>测试类型</th>
                <th>状态</th>
                <th>通过</th>
                <th>失败</th>
                <th>耗时(秒)</th>
            </tr>
"""
        
        for test_type, result in self.validation_results['test_results'].items():
            status = "✅ 成功" if result.get('success', False) else "❌ 失败"
            stats = result.get('stats', {})
            duration = result.get('duration', 0)
            
            html_content += f"""
            <tr>
                <td>{test_type}</td>
                <td>{status}</td>
                <td>{stats.get('passed', 0)}</td>
                <td>{stats.get('failed', 0)}</td>
                <td>{duration:.2f}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>⚠️ 问题和建议</h2>
"""
        
        if self.validation_results['issues']:
            html_content += "<h3>🚨 发现的问题:</h3><ul>"
            for issue in self.validation_results['issues']:
                html_content += f"<li class='failure'>{issue}</li>"
            html_content += "</ul>"
        
        if self.validation_results['recommendations']:
            html_content += "<h3>💡 建议:</h3><ul>"
            for rec in self.validation_results['recommendations']:
                html_content += f"<li>{rec}</li>"
            html_content += "</ul>"
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _display_summary(self, success: bool):
        """显示测试结果摘要"""
        summary = self.validation_results['summary']
        
        print("\n" + "="*60)
        print("📈 测试验证结果摘要")
        print("="*60)
        
        status_icon = "✅" if success else "❌"
        status_text = "所有测试通过" if success else "有测试失败"
        print(f"{status_icon} 总体状态: {status_text}")
        
        print(f"\n📊 测试统计:")
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  通过: {summary['passed_tests']} ✅")
        print(f"  失败: {summary['failed_tests']} ❌")
        print(f"  错误: {summary['error_tests']} ⚠️")
        print(f"  跳过: {summary['skipped_tests']} ⏭️")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        print(f"  执行时间: {summary['execution_time']:.2f}秒")
        
        if self.validation_results['issues']:
            print(f"\n⚠️ 发现 {len(self.validation_results['issues'])} 个问题:")
            for i, issue in enumerate(self.validation_results['issues'][:5], 1):
                print(f"  {i}. {issue}")
            if len(self.validation_results['issues']) > 5:
                print(f"  ... 还有 {len(self.validation_results['issues']) - 5} 个问题")
        
        print("\n📄 详细报告已生成在 tests/reports/ 目录")
    
    def _get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        try:
            import toml
            pyproject_file = self.project_root / 'pyproject.toml'
            if pyproject_file.exists():
                with open(pyproject_file, 'r') as f:
                    pyproject_data = toml.load(f)
                    return pyproject_data.get('tool', {}).get('poetry', {})
        except ImportError:
            pass
        
        return {
            'name': 'AShare Agent',
            'version': '0.1.0',
            'description': 'AI-powered hedge fund system'
        }
    
    def _has_command(self, command: str) -> bool:
        """检查命令是否存在"""
        result = self._run_command([command, '--version'])
        return result['returncode'] == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试验证脚本')
    parser.add_argument('--fast', action='store_true', help='快速模式，跳过慢速测试')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--no-report', action='store_true', help='不生成详细报告')
    parser.add_argument('--fix', action='store_true', help='自动修复可修复的问题')
    
    args = parser.parse_args()
    
    validator = TestValidator(
        fast_mode=args.fast,
        with_coverage=args.coverage,
        generate_report=not args.no_report,
        auto_fix=args.fix
    )
    
    success = validator.run_validation()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
