#!/usr/bin/env python3
"""
NAVSIM Smart Downloader
基于HuggingFace Hub API的智能下载器，支持断点续传、并发控制、智能重试
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import yaml

try:
    from huggingface_hub import hf_hub_download, HfFileSystem
    from tqdm import tqdm
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  huggingface_hub 未安装，将使用 wget 备选方案")

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
    """智能下载器主类"""
    
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
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'completed_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'total_size_mb': 0,
            'downloaded_size_mb': 0,
            'start_time': None,
            'end_time': None
        }
        
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
        if expected_size_mb:
            size_diff_pct = abs(actual_size_mb - expected_size_mb) / expected_size_mb
            if size_diff_pct > 0.05:  # 5%误差
                self.logger.warning(f"⚠️  文件大小异常: {file_path.name}, 预期:{expected_size_mb}MB, 实际:{actual_size_mb:.1f}MB")
                return False
        
        return True
    
    def download_with_hf_hub(self, task: DownloadTask) -> Tuple[bool, str]:
        """使用HuggingFace Hub API下载文件"""
        try:
            local_path = self.download_dir / task.local_filename
            
            # 支持断点续传的下载
            downloaded_path = hf_hub_download(
                repo_id=task.repository,
                filename=task.path,
                local_dir=str(self.download_dir),
                local_dir_use_symlinks=False,
                resume_download=True  # 关键：启用断点续传
            )
            
            # 验证下载完整性
            if self.verify_file_integrity(Path(downloaded_path), task.size_estimate_mb):
                return True, f"成功下载: {task.local_filename}"
            else:
                return False, f"文件完整性验证失败: {task.local_filename}"
                
        except Exception as e:
            return False, f"下载失败: {task.local_filename}, 错误: {str(e)}"
    
    def download_with_wget(self, task: DownloadTask) -> Tuple[bool, str]:
        """使用wget备选下载（当HF Hub不可用时）"""
        try:
            import subprocess
            
            url = f"https://huggingface.co/datasets/{task.repository}/resolve/main/{task.path}"
            local_path = self.download_dir / task.local_filename
            
            # wget命令，支持断点续传
            cmd = [
                'wget',
                '-c',  # 断点续传
                '--tries=3',  # 重试3次
                '--timeout=300',  # 5分钟超时
                '--progress=bar',
                '-O', str(local_path),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if self.verify_file_integrity(local_path, task.size_estimate_mb):
                    return True, f"wget成功下载: {task.local_filename}"
                else:
                    return False, f"wget下载文件完整性验证失败: {task.local_filename}"
            else:
                return False, f"wget下载失败: {task.local_filename}, 错误: {result.stderr}"
                
        except Exception as e:
            return False, f"wget下载异常: {task.local_filename}, 错误: {str(e)}"
    
    def download_single_file(self, task: DownloadTask) -> Tuple[bool, str]:
        """下载单个文件，包含重试逻辑"""
        retries = 0
        last_error = ""
        
        while retries < task.max_retries:
            # 更新任务状态
            self.status[task.local_filename] = {
                'status': 'downloading',
                'attempts': retries + 1,
                'last_attempt': time.time()
            }
            self.save_status()
            
            # 尝试下载
            if HF_AVAILABLE:
                success, message = self.download_with_hf_hub(task)
            else:
                success, message = self.download_with_wget(task)
            
            if success:
                # 下载成功
                self.status[task.local_filename] = {
                    'status': 'completed',
                    'completed_time': time.time(),
                    'attempts': retries + 1
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
            'last_error': last_error
        }
        self.save_status()
        self.stats['failed_files'] += 1
        return False, last_error
    
    def download_with_progress(self, tasks: List[DownloadTask]):
        """带进度条的并发下载"""
        max_workers = self.config['global_settings']['max_concurrent']
        
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
        print(f"📁 总文件数: {self.stats['total_files']}")
        print(f"✅ 成功下载: {self.stats['completed_files']}")
        print(f"⏭️  跳过文件: {self.stats['skipped_files']}")
        print(f"❌ 失败文件: {self.stats['failed_files']}")
        print(f"⏱️  耗时: {duration:.1f} 分钟")
        print(f"🎯 成功率: {(self.stats['completed_files']/max(1, self.stats['total_files']-self.stats['skipped_files']))*100:.1f}%")
        
        if self.stats['failed_files'] > 0:
            print(f"\n❌ 失败文件列表:")
            for filename, status in self.status.items():
                if status.get('status') == 'failed':
                    print(f"   • {filename}: {status.get('last_error', 'Unknown error')}")
    
    def run(self):
        """运行下载器"""
        self.logger.info("🚀 NAVSIM 智能下载器启动")
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
    
    parser = argparse.ArgumentParser(description='NAVSIM 智能下载器')
    parser.add_argument('--config', '-c', 
                       default='smart_download_config_complete.yaml',
                       help='配置文件路径')
    parser.add_argument('--generate-config', action='store_true',
                       help='生成配置文件后退出')
    
    args = parser.parse_args()
    
    if args.generate_config:
        # 生成配置文件
        from generate_download_config import generate_complete_config, save_config, print_summary
        
        config = generate_complete_config()
        config_path = Path(args.config)
        save_config(config, config_path)
        print_summary(config)
        print(f"\n✅ 配置文件已生成: {config_path}")
        return
    
    # 检查依赖
    if not HF_AVAILABLE:
        print("⚠️  建议安装 huggingface_hub 以获得最佳下载体验:")
        print("   pip install huggingface_hub")
        print("   将使用 wget 作为备选方案\n")
    
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