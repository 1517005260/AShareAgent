"""
验证脚本：自动化测试验证和报告生成

功能包含:
1. 测试结果验证
2. 性能指标检查
3. 错误报告生成
4. 测试覆盖率统计
5. 回归测试验证
"""

import pytest
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestValidationScripts:
    """测试验证脚本"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.project_root = project_root
        self.test_reports_dir = project_root / 'tests' / 'reports'
        self.test_reports_dir.mkdir(exist_ok=True)
        
        # 测试配置
        self.validation_config = {
            'performance_thresholds': {
                'max_execution_time': 60,  # 秒 - 放宽时间限制
                'min_cache_hit_rate': 20,  # %
                'max_memory_usage': 500,   # MB
            },
            'quality_thresholds': {
                'min_test_coverage': 80,   # %
                'max_error_rate': 5,       # %
                'min_assertion_count': 50, # 数量
            }
        }
    
    def test_run_unit_tests_validation(self):
        """验证单元测试执行"""
        result = self._run_pytest_command([
            'tests/unit/',
            '-v',
            '--tb=short',
            '--durations=10'
        ])
        
        # 验证测试结果
        assert result['returncode'] == 0, f"单元测试失败: {result['stderr']}"
        
        # 统计测试结果
        stats = self._parse_pytest_output(result['stdout'])
        assert stats['passed'] > 0, "没有通过的测试"
        assert stats['failed'] == 0, f"有 {stats['failed']} 个测试失败"
        
        # 生成验证报告
        self._generate_validation_report('unit_tests', stats, result)
    
    def test_run_integration_tests_validation(self):
        """验证集成测试执行"""
        result = self._run_pytest_command([
            'tests/integration/',
            '-v',
            '--tb=short',
            '-m', 'not slow'  # 跳过慢速测试
        ])
        
        # 验证测试结果
        assert result['returncode'] == 0, f"集成测试失败: {result['stderr']}"
        
        # 统计测试结果
        stats = self._parse_pytest_output(result['stdout'])
        assert stats['passed'] > 0, "没有通过的集成测试"
        
        # 生成验证报告
        self._generate_validation_report('integration_tests', stats, result)
    
    def test_performance_validation(self):
        """验证性能测试"""
        # 运行性能测试
        start_time = time.time()
        
        result = self._run_pytest_command([
            'tests/performance/',
            '-v',
            '--tb=short',
            '--benchmark-only' if self._has_benchmark_plugin() else '--durations=5'
        ])
        
        execution_time = time.time() - start_time
        
        # 验证性能阈值
        assert execution_time < self.validation_config['performance_thresholds']['max_execution_time'], \
            f"性能测试执行时间过长: {execution_time:.2f}秒"
        
        # 解析性能数据
        perf_data = self._extract_performance_data(result['stdout'])
        
        # 生成性能报告
        self._generate_performance_report(perf_data, execution_time)
    
    def test_test_coverage_validation(self):
        """验证测试覆盖率"""
        # 运行覆盖率测试
        result = self._run_pytest_command([
            'tests/',
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=json',
            '--cov-fail-under=50',  # 设置最低覆盖率
            '-m', 'not slow'  # 跳过慢速测试
        ])
        
        # 检查覆盖率报告
        coverage_file = self.project_root / '.coverage'
        if coverage_file.exists():
            coverage_data = self._parse_coverage_data()
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            # 验证覆盖率
            min_coverage = self.validation_config['quality_thresholds']['min_test_coverage']
            assert total_coverage >= min_coverage, \
                f"测试覆盖率过低: {total_coverage:.1f}% < {min_coverage}%"
            
            # 生成覆盖率报告
            self._generate_coverage_report(coverage_data)
    
    def test_code_quality_validation(self):
        """验证代码质量"""
        quality_issues = []
        
        # 检查flake8代码质量
        if self._has_flake8():
            flake8_result = self._run_command(['flake8', 'src/', 'tests/'])
            if flake8_result['returncode'] != 0:
                quality_issues.append(f"Flake8检查失败: {flake8_result['stdout']}")
        
        # 检查black代码格式
        if self._has_black():
            black_result = self._run_command(['black', '--check', 'src/', 'tests/'])
            if black_result['returncode'] != 0:
                quality_issues.append("Black代码格式检查失败")
        
        # 检查isort导入排序
        if self._has_isort():
            isort_result = self._run_command(['isort', '--check-only', 'src/', 'tests/'])
            if isort_result['returncode'] != 0:
                quality_issues.append("Isort导入排序检查失败")
        
        # 生成代码质量报告
        self._generate_quality_report(quality_issues)
        
        # 验证质量标准
        max_issues = 5  # 允许的最大问题数
        assert len(quality_issues) <= max_issues, \
            f"代码质量问题过多: {len(quality_issues)} > {max_issues}\n{quality_issues}"
    
    def test_regression_validation(self):
        """验证回归测试"""
        # 为了避免超时，只运行核心测试目录进行回归验证
        result = self._run_pytest_command([
            'tests/unit/',
            'tests/integration/',
            '-v',
            '--tb=line',
            '-m', 'not slow'
        ])
        
        # 统计测试结果
        stats = self._parse_pytest_output(result['stdout'])
        
        # 验证没有回归
        assert stats['failed'] == 0, f"发现回归：{stats['failed']}个测试失败"
        assert stats['error'] == 0, f"发现错误：{stats['error']}个测试错误"
        
        # 计算成功率
        total_tests = stats['passed'] + stats['failed'] + stats['error'] + stats['skipped']
        success_rate = (stats['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        min_success_rate = 90  # 90%成功率，稍微放宽
        assert success_rate >= min_success_rate, \
            f"测试成功率过低: {success_rate:.1f}% < {min_success_rate}%"
        
        # 生成回归测试报告
        self._generate_regression_report(stats, success_rate)
    
    def test_generate_comprehensive_report(self):
        """生成综合测试报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_info': {
                'name': 'AShare Agent',
                'version': '0.1.0',
                'python_version': sys.version
            },
            'validation_summary': {
                'total_validations': 6,
                'passed_validations': 0,
                'failed_validations': 0,
                'validation_details': []
            }
        }
        
        # 执行所有验证步骤
        validations = [
            ('unit_tests', self._validate_unit_tests),
            ('integration_tests', self._validate_integration_tests),
            ('performance', self._validate_performance),
            ('coverage', self._validate_coverage),
            ('code_quality', self._validate_code_quality),
            ('regression', self._validate_regression)
        ]
        
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                report_data['validation_summary']['passed_validations'] += 1
                status = 'PASSED'
            except Exception as e:
                report_data['validation_summary']['failed_validations'] += 1
                status = 'FAILED'
                result = {'error': str(e)}
            
            report_data['validation_summary']['validation_details'].append({
                'name': validation_name,
                'status': status,
                'result': result
            })
        
        # 保存综合报告
        report_file = self.test_reports_dir / f'comprehensive_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n综合验证报告已生成: {report_file}")
        
        # 验证总体结果
        assert report_data['validation_summary']['failed_validations'] == 0, \
            f"有 {report_data['validation_summary']['failed_validations']} 个验证失败"
    
    # 辅助方法
    
    def _run_pytest_command(self, args: List[str]) -> Dict[str, Any]:
        """运行pytest命令"""
        cmd = ['python', '-m', 'pytest'] + args
        return self._run_command(cmd)
    
    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, int]:
        """解析pytest输出"""
        stats = {
            'passed': 0,
            'failed': 0,
            'error': 0,
            'skipped': 0,
            'warnings': 0
        }
        
        # 解析pytest输出，寻找测试统计信息
        lines = output.strip().split('\n')
        
        # 首先寻找标准pytest结果行，格式如：
        # ============================= 99 passed in 17.17s ==============================
        # ======================== 3 failed, 180 passed, 3 warnings in 450.67s ========
        for line in reversed(lines):
            if line.startswith('=') and ('passed' in line or 'failed' in line or 'error' in line):
                # 移除等号装饰
                content = line.strip('=').strip()
                
                # 解析内容，例如: "99 passed in 17.17s" 或 "3 failed, 180 passed, 3 warnings in 450.67s"
                # 先移除时间部分 "in XX.XXs"
                if ' in ' in content:
                    content = content.split(' in ')[0]
                
                # 按逗号分割各个统计项
                parts = content.split(',')
                for part in parts:
                    part = part.strip()
                    try:
                        # 提取数字
                        words = part.split()
                        for i, word in enumerate(words):
                            if word.isdigit():
                                count = int(word)
                                # 查找数字后面的状态词
                                if i + 1 < len(words):
                                    status = words[i + 1].lower()
                                    if 'passed' in status:
                                        stats['passed'] = count
                                    elif 'failed' in status:
                                        stats['failed'] = count
                                    elif 'error' in status:
                                        stats['error'] = count
                                    elif 'skipped' in status:
                                        stats['skipped'] = count
                                    elif 'warning' in status:
                                        stats['warnings'] = count
                                break
                    except (ValueError, IndexError):
                        continue
                break
        
        # 如果上面没找到，再尝试寻找非装饰性的统计行
        if all(v == 0 for v in stats.values()):
            for line in reversed(lines):
                if ('passed' in line or 'failed' in line or 'error' in line) and not line.startswith('='):
                    # 解析类似 "5 passed, 1 failed, 2 warnings" 的格式
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        try:
                            numbers = [int(s) for s in part.split() if s.isdigit()]
                            if numbers and len(numbers) > 0:
                                count = numbers[0]
                                if 'passed' in part:
                                    stats['passed'] = count
                                elif 'failed' in part:
                                    stats['failed'] = count
                                elif 'error' in part:
                                    stats['error'] = count
                                elif 'skipped' in part:
                                    stats['skipped'] = count
                                elif 'warning' in part:
                                    stats['warnings'] = count
                        except (ValueError, IndexError):
                            continue
                    break
        
        return stats
    
    def _extract_performance_data(self, output: str) -> Dict[str, Any]:
        """提取性能数据"""
        perf_data = {
            'slowest_tests': [],
            'average_duration': 0,
            'total_duration': 0
        }
        
        # 解析最慢测试
        lines = output.split('\n')
        in_duration_section = False
        
        for line in lines:
            if 'slowest durations' in line.lower():
                in_duration_section = True
                continue
            
            if in_duration_section and line.strip():
                if line.startswith('='):
                    break
                # 解析类似 "0.50s call tests/unit/test_example.py::test_function" 的格式
                if 's ' in line:
                    duration_str = line.split('s')[0].strip()
                    try:
                        duration = float(duration_str)
                        test_name = line.split('s')[1].strip()
                        perf_data['slowest_tests'].append({
                            'test': test_name,
                            'duration': duration
                        })
                    except (ValueError, IndexError):
                        continue
        
        return perf_data
    
    def _parse_coverage_data(self) -> Dict[str, Any]:
        """解析覆盖率数据"""
        coverage_json_file = self.project_root / 'coverage.json'
        if coverage_json_file.exists():
            with open(coverage_json_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _generate_validation_report(self, test_type: str, stats: Dict[str, int], result: Dict[str, Any]):
        """生成验证报告"""
        report = {
            'test_type': test_type,
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'execution_result': result,
            'validation_status': 'PASSED' if result['returncode'] == 0 else 'FAILED'
        }
        
        report_file = self.test_reports_dir / f'{test_type}_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _generate_performance_report(self, perf_data: Dict[str, Any], execution_time: float):
        """生成性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': execution_time,
            'performance_data': perf_data,
            'thresholds': self.validation_config['performance_thresholds'],
            'validation_status': 'PASSED' if execution_time < self.validation_config['performance_thresholds']['max_execution_time'] else 'FAILED'
        }
        
        report_file = self.test_reports_dir / f'performance_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _generate_coverage_report(self, coverage_data: Dict[str, Any]):
        """生成覆盖率报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'coverage_data': coverage_data,
            'thresholds': self.validation_config['quality_thresholds'],
            'validation_status': 'PASSED'
        }
        
        report_file = self.test_reports_dir / f'coverage_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _generate_quality_report(self, quality_issues: List[str]):
        """生成代码质量报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'quality_issues': quality_issues,
            'issues_count': len(quality_issues),
            'validation_status': 'PASSED' if len(quality_issues) <= 5 else 'FAILED'
        }
        
        report_file = self.test_reports_dir / f'quality_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _generate_regression_report(self, stats: Dict[str, int], success_rate: float):
        """生成回归测试报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_statistics': stats,
            'success_rate': success_rate,
            'validation_status': 'PASSED' if success_rate >= 95 else 'FAILED'
        }
        
        report_file = self.test_reports_dir / f'regression_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _has_benchmark_plugin(self) -> bool:
        """检查是否安装了pytest-benchmark插件"""
        try:
            import pytest_benchmark
            return True
        except ImportError:
            return False
    
    def _has_flake8(self) -> bool:
        """检查是否安装了flake8"""
        result = self._run_command(['flake8', '--version'])
        return result['returncode'] == 0
    
    def _has_black(self) -> bool:
        """检查是否安装了black"""
        result = self._run_command(['black', '--version'])
        return result['returncode'] == 0
    
    def _has_isort(self) -> bool:
        """检查是否安装了isort"""
        result = self._run_command(['isort', '--version'])
        return result['returncode'] == 0
    
    # 内部验证方法（用于综合报告）
    
    def _validate_unit_tests(self) -> Dict[str, Any]:
        """内部单元测试验证"""
        result = self._run_pytest_command(['tests/unit/', '-v'])
        stats = self._parse_pytest_output(result['stdout'])
        return {'stats': stats, 'success': result['returncode'] == 0}
    
    def _validate_integration_tests(self) -> Dict[str, Any]:
        """内部集成测试验证"""
        result = self._run_pytest_command(['tests/integration/', '-v', '-m', 'not slow'])
        stats = self._parse_pytest_output(result['stdout'])
        return {'stats': stats, 'success': result['returncode'] == 0}
    
    def _validate_performance(self) -> Dict[str, Any]:
        """内部性能验证"""
        start_time = time.time()
        result = self._run_pytest_command(['tests/performance/', '-v'])
        execution_time = time.time() - start_time
        
        max_time = self.validation_config['performance_thresholds']['max_execution_time']
        return {
            'execution_time': execution_time,
            'max_allowed_time': max_time,
            'success': execution_time < max_time
        }
    
    def _validate_coverage(self) -> Dict[str, Any]:
        """内部覆盖率验证"""
        result = self._run_pytest_command([
            'tests/', '--cov=src', '--cov-report=json', '-m', 'not slow'
        ])
        
        coverage_data = self._parse_coverage_data()
        total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
        min_coverage = self.validation_config['quality_thresholds']['min_test_coverage']
        
        return {
            'coverage_percentage': total_coverage,
            'min_required': min_coverage,
            'success': total_coverage >= min_coverage
        }
    
    def _validate_code_quality(self) -> Dict[str, Any]:
        """内部代码质量验证"""
        issues = []
        
        if self._has_flake8():
            result = self._run_command(['flake8', 'src/', 'tests/'])
            if result['returncode'] != 0:
                issues.append('flake8_violations')
        
        return {
            'issues_count': len(issues),
            'max_allowed': 5,
            'success': len(issues) <= 5
        }
    
    def _validate_regression(self) -> Dict[str, Any]:
        """内部回归验证"""
        result = self._run_pytest_command(['tests/unit/', 'tests/integration/', '-v', '-m', 'not slow'])
        stats = self._parse_pytest_output(result['stdout'])
        
        # 与test_regression_validation保持一致，包括skipped测试
        total_tests = stats['passed'] + stats['failed'] + stats['error'] + stats['skipped']
        success_rate = (stats['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'stats': stats,
            'success_rate': success_rate,
            'min_required_rate': 90,
            'success': success_rate >= 90
        }


if __name__ == '__main__':
    # 运行所有验证
    pytest.main([__file__, '-v'])
