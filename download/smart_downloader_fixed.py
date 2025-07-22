#!/usr/bin/env python3
"""
NAVSIM Smart Downloader (修正版)
支持HuggingFace数据集API + wget回退机制
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import yaml

try:
    from huggingface_hub import hf_hub_download, HfApi
    from tqdm import tqdm
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  huggingface_hub 未安装，将使用 wget 方案")

@dataclass
class DownloadTask:
    """下载任务数据类"""
    path: str
    repository: str
    local_filename: str
    size_estimate_mb: int
    priority: int
    max_retries: int = 5
    
class SmartDownloader:
    """智能下载器主类（修正版）"""
    
    def __init__(self, config_path: str):
        """初始化下载器"""
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.download_dir = Path('./downloads')
        self.download_dir.mkdir(exist_ok=True)
        
        # 状态文件
        self.status_file = self.download_dir / 'download_status.json'
        self.status = self.load_status()
        
        # 设置日志
        self.setup_logging()
        
        # 检测可用的下载方法
        self.download_method = self.detect_best_download_method()
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'completed_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'start_time': None,
            'end_time': None
        }
        
    def detect_best_download_method(self) -> str:
        """检测最佳下载方法"""
        self.logger.info("🔍 检测最佳下载方法...")
        
        if HF_AVAILABLE:
            try:
                # 测试HF API是否可用
                api = HfApi()
                repo_info = api.repo_info("OpenDriveLab/OpenScene", repo_type="dataset")
                self.logger.info("✅ HuggingFace API 可用")
                return "hf_api"
            except Exception as e:
                self.logger.warning(f"⚠️ HuggingFace API 不可用: {e}")
        
        # 检测wget
        try:
            result = subprocess.run(['wget', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info("✅ wget 可用，将使用HTTP直接下载")
                return "wget"
        except Exception:
            pass
        
        # 检测curl作为备选
        try:
            result = subprocess.run(['curl', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info("✅ curl 可用，将使用HTTP直接下载")
                return "curl"
        except Exception:
            pass
        
        self.logger.error("❌ 没有可用的下载工具")
        raise RuntimeError("无法找到可用的下载工具（HuggingFace API、wget、curl）")
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_status(self) -> Dict:
        """加载下载状态"""
        if self.status_file.exists():
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_status(self):
        """保存下载状态"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.download_dir / 'download.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_download_tasks(self) -> List[DownloadTask]:
        """生成下载任务列表"""
        tasks = []
        
        for task_group_name, task_group in self.config['download_tasks'].items():
            repository = task_group.get('repository', self.config['repository'])
            priority = task_group.get('priority', 99)
            
            for file_info in task_group['files']:
                file_path = file_info['path']
                local_filename = Path(file_path).name
                
                # 检查是否已完成
                if self.is_file_completed(local_filename):
                    self.logger.info(f"⏭️  跳过已完成文件: {local_filename}")
                    self.stats['skipped_files'] += 1
                    continue
                
                task = DownloadTask(
                    path=file_path,
                    repository=repository,
                    local_filename=local_filename,
                    size_estimate_mb=file_info['size_estimate_mb'],
                    priority=priority,
                    max_retries=self.config['global_settings']['max_retries']
                )
                tasks.append(task)
        
        # 按优先级排序
        tasks.sort(key=lambda x: x.priority)
        return tasks
    
    def is_file_completed(self, filename: str) -> bool:
        """检查文件是否已完成下载"""
        # 检查配置中的已完成列表
        for dataset_files in self.config['completed_downloads'].values():
            if filename in dataset_files:
                return True
        
        # 检查状态文件
        return self.status.get(filename, {}).get('status') == 'completed'
    
    def verify_file_integrity(self, file_path: Path, expected_size_mb: Optional[int] = None) -> bool:
        """验证文件完整性"""
        if not file_path.exists():
            return False
        
        actual_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # 如果有预期大小，检查是否接近（允许5%误差）
        if expected_size_mb and expected_size_mb > 0:
            size_diff_pct = abs(actual_size_mb - expected_size_mb) / expected_size_mb
            if size_diff_pct > 0.05:  # 5%误差
                self.logger.warning(f"⚠️  文件大小异常: {file_path.name}, 预期:{expected_size_mb}MB, 实际:{actual_size_mb:.1f}MB")
                return False
        
        # 基本检查：文件不为空
        if actual_size_mb < 0.1:  # 小于0.1MB可能有问题
            self.logger.warning(f"⚠️  文件太小: {file_path.name}, {actual_size_mb:.1f}MB")
            return False
        
        return True
    
    def download_with_hf_hub(self, task: DownloadTask) -> Tuple[bool, str]:
        """使用HuggingFace Hub API下载文件"""
        try:
            local_path = self.download_dir / task.local_filename
            
            # 支持断点续传的下载，正确指定数据集类型
            downloaded_path = hf_hub_download(
                repo_id=task.repository,
                filename=task.path,
                local_dir=str(self.download_dir),
                repo_type="dataset",  # 关键：指定为数据集
                resume_download=True
            )
            
            # 验证下载完整性
            if self.verify_file_integrity(Path(downloaded_path), task.size_estimate_mb):
                return True, f"HF API成功下载: {task.local_filename}"
            else:
                return False, f"HF API下载文件完整性验证失败: {task.local_filename}"
                
        except Exception as e:
            return False, f"HF API下载失败: {task.local_filename}, 错误: {str(e)}"
    
    def download_with_wget(self, task: DownloadTask) -> Tuple[bool, str]:
        """使用wget下载"""
        try:
            url = f"https://huggingface.co/datasets/{task.repository}/resolve/main/{task.path}"
            local_path = self.download_dir / task.local_filename
            
            # wget命令，支持断点续传
            cmd = [
                'wget',
                '-c',  # 断点续传
                '--tries=3',  # 重试3次
                '--timeout=300',  # 5分钟超时
                '--progress=bar:force',  # 强制显示进度条
                '--no-check-certificate',  # 跳过SSL验证（如果需要）
                '-O', str(local_path),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15分钟超时
            
            if result.returncode == 0:
                if self.verify_file_integrity(local_path, task.size_estimate_mb):
                    return True, f"wget成功下载: {task.local_filename}"
                else:
                    return False, f"wget下载文件完整性验证失败: {task.local_filename}"
            else:
                return False, f"wget下载失败: {task.local_filename}, 错误: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"wget下载超时: {task.local_filename}"
        except Exception as e:
            return False, f"wget下载异常: {task.local_filename}, 错误: {str(e)}"
    
    def download_with_curl(self, task: DownloadTask) -> Tuple[bool, str]:
        """使用curl下载"""
        try:
            url = f"https://huggingface.co/datasets/{task.repository}/resolve/main/{task.path}"
            local_path = self.download_dir / task.local_filename
            
            # curl命令，支持断点续传
            cmd = [
                'curl',
                '-C', '-',  # 断点续传
                '--retry', '3',  # 重试3次
                '--retry-delay', '2',  # 重试延迟
                '--max-time', '900',  # 15分钟超时
                '--progress-bar',  # 进度条
                '-L',  # 跟随重定向
                '-o', str(local_path),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                if self.verify_file_integrity(local_path, task.size_estimate_mb):
                    return True, f"curl成功下载: {task.local_filename}"
                else:
                    return False, f"curl下载文件完整性验证失败: {task.local_filename}"
            else:
                return False, f"curl下载失败: {task.local_filename}, 错误: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"curl下载超时: {task.local_filename}"
        except Exception as e:
            return False, f"curl下载异常: {task.local_filename}, 错误: {str(e)}"
    
    def download_single_file(self, task: DownloadTask) -> Tuple[bool, str]:
        """下载单个文件，包含重试逻辑"""
        retries = 0
        last_error = ""
        
        while retries < task.max_retries:
            # 更新任务状态
            self.status[task.local_filename] = {
                'status': 'downloading',
                'attempts': retries + 1,
                'last_attempt': time.time(),
                'method': self.download_method
            }
            self.save_status()
            
            # 根据检测到的方法下载
            if self.download_method == "hf_api":
                success, message = self.download_with_hf_hub(task)
            elif self.download_method == "wget":
                success, message = self.download_with_wget(task)
            elif self.download_method == "curl":
                success, message = self.download_with_curl(task)
            else:
                success, message = False, "未知下载方法"
            
            if success:
                # 下载成功
                self.status[task.local_filename] = {
                    'status': 'completed',
                    'completed_time': time.time(),
                    'attempts': retries + 1,
                    'method': self.download_method
                }
                self.save_status()
                self.stats['completed_files'] += 1
                return True, message
            
            # 下载失败，准备重试
            retries += 1
            last_error = message
            
            if retries < task.max_retries:
                # 指数退避延迟
                delay = self.config['global_settings']['retry_delay_base'] ** retries
                self.logger.warning(f"🔄 重试 {retries}/{task.max_retries}: {task.local_filename}, {delay}秒后重试")
                time.sleep(delay)
        
        # 所有重试都失败了
        self.status[task.local_filename] = {
            'status': 'failed',
            'failed_time': time.time(),
            'attempts': retries,
            'last_error': last_error,
            'method': self.download_method
        }
        self.save_status()
        self.stats['failed_files'] += 1
        return False, last_error
    
    def download_with_progress(self, tasks: List[DownloadTask]):
        """带进度条的并发下载"""
        max_workers = self.config['global_settings']['max_concurrent']
        
        # 如果使用wget/curl，降低并发数避免被限速
        if self.download_method in ["wget", "curl"]:
            max_workers = min(max_workers, 2)
            self.logger.info(f"📉 降低并发数至 {max_workers} 避免HTTP限速")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.download_single_file, task): task 
                for task in tasks
            }
            
            # 创建总体进度条
            total_progress = tqdm(
                total=len(tasks),
                desc="📦 总体进度",
                unit="文件",
                position=0
            )
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success, message = future.result()
                    if success:
                        self.logger.info(f"✅ {message}")
                    else:
                        self.logger.error(f"❌ {message}")
                        
                except Exception as e:
                    self.logger.error(f"💥 任务执行异常: {task.local_filename}, {e}")
                    self.stats['failed_files'] += 1
                
                total_progress.update(1)
            
            total_progress.close()
    
    def print_summary(self):
        """打印下载摘要"""
        duration = (self.stats['end_time'] - self.stats['start_time']) / 60  # 分钟
        
        print("\n" + "="*60)
        print("📊 下载完成摘要")
        print("="*60)
        print(f"🔧 使用方法: {self.download_method}")
        print(f"📁 总文件数: {self.stats['total_files']}")
        print(f"✅ 成功下载: {self.stats['completed_files']}")
        print(f"⏭️  跳过文件: {self.stats['skipped_files']}")
        print(f"❌ 失败文件: {self.stats['failed_files']}")
        print(f"⏱️  耗时: {duration:.1f} 分钟")
        
        if self.stats['total_files'] > self.stats['skipped_files']:
            success_rate = (self.stats['completed_files']/(self.stats['total_files']-self.stats['skipped_files']))*100
            print(f"🎯 成功率: {success_rate:.1f}%")
        
        if self.stats['failed_files'] > 0:
            print(f"\n❌ 失败文件列表:")
            for filename, status in self.status.items():
                if status.get('status') == 'failed':
                    print(f"   • {filename}: {status.get('last_error', 'Unknown error')}")
    
    def run(self):
        """运行下载器"""
        self.logger.info("🚀 NAVSIM 智能下载器启动（修正版）")
        self.logger.info(f"🔧 使用下载方法: {self.download_method}")
        self.stats['start_time'] = time.time()
        
        # 生成下载任务
        tasks = self.generate_download_tasks()
        self.stats['total_files'] = len(tasks) + self.stats['skipped_files']
        
        if not tasks:
            self.logger.info("🎉 所有文件都已下载完成！")
            return
        
        self.logger.info(f"📋 待下载文件: {len(tasks)} 个")
        
        # 开始下载
        self.download_with_progress(tasks)
        
        self.stats['end_time'] = time.time()
        self.print_summary()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NAVSIM 智能下载器（修正版）')
    parser.add_argument('--config', '-c', 
                       default='smart_download_config_complete.yaml',
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 运行下载器
    try:
        downloader = SmartDownloader(args.config)
        downloader.run()
    except KeyboardInterrupt:
        print("\n🛑 下载被用户中断")
    except Exception as e:
        print(f"\n💥 下载器运行错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 