#!/usr/bin/env python3
"""
NAVSIM Post Processor
处理下载完成后的文件校验、解压和目录整理
"""

import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import logging

class PostProcessor:
    """后处理器，负责文件校验、解压和目录整理"""
    
    def __init__(self, config: Dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.download_dir = Path('./downloads')
        
    def extract_archive(self, archive_path: Path, extract_to: Optional[Path] = None) -> bool:
        """解压压缩文件"""
        if extract_to is None:
            extract_to = archive_path.parent
            
        try:
            self.logger.info(f"🗜️ 解压: {archive_path.name}")
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_path.suffix.lower() in ['.tgz', '.gz'] or '.tar' in archive_path.name.lower():
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                self.logger.warning(f"⚠️ 不支持的压缩格式: {archive_path.name}")
                return False
                
            self.logger.info(f"✅ 解压完成: {archive_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 解压失败 {archive_path.name}: {e}")
            return False
    
    def verify_extraction(self, archive_path: Path, extract_to: Path) -> bool:
        """验证解压结果"""
        try:
            # 检查解压目录是否存在内容
            if not extract_to.exists():
                return False
                
            extracted_items = list(extract_to.iterdir())
            if not extracted_items:
                return False
                
            self.logger.info(f"✅ 解压验证通过: {archive_path.name} -> {len(extracted_items)} 个项目")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 解压验证失败 {archive_path.name}: {e}")
            return False
    
    def organize_structure(self) -> bool:
        """按照install.md要求整理目录结构"""
        try:
            self.logger.info("📁 开始整理目录结构...")
            
            # 检查是否有openscene-v1.1目录
            openscene_dir = self.download_dir / 'openscene-v1.1'
            if openscene_dir.exists():
                self.logger.info("📂 发现openscene-v1.1目录，开始整理...")
                
                # 移动meta_datas
                if (openscene_dir / 'meta_datas').exists():
                    meta_files = list((openscene_dir / 'meta_datas').iterdir())
                    for meta_file in meta_files:
                        if 'mini' in meta_file.name:
                            target = self.download_dir / 'mini_navsim_logs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(meta_file), str(target))
                        elif 'trainval' in meta_file.name:
                            target = self.download_dir / 'trainval_navsim_logs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(meta_file), str(target))
                        elif 'test' in meta_file.name:
                            target = self.download_dir / 'test_navsim_logs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(meta_file), str(target))
                
                # 移动sensor_blobs
                if (openscene_dir / 'sensor_blobs').exists():
                    sensor_files = list((openscene_dir / 'sensor_blobs').iterdir())
                    for sensor_file in sensor_files:
                        if 'mini' in sensor_file.name:
                            target = self.download_dir / 'mini_sensor_blobs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(sensor_file), str(target))
                        elif 'trainval' in sensor_file.name:
                            target = self.download_dir / 'trainval_sensor_blobs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(sensor_file), str(target))
                        elif 'test' in sensor_file.name:
                            target = self.download_dir / 'test_sensor_blobs'
                            target.mkdir(exist_ok=True)
                            shutil.move(str(sensor_file), str(target))
                
                # 清理空的openscene-v1.1目录
                if not list(openscene_dir.rglob('*')):
                    shutil.rmtree(openscene_dir)
            
            self.logger.info("✅ 目录结构整理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 目录结构整理失败: {e}")
            return False
    
    def cleanup_archives(self, keep_archives: bool = False) -> int:
        """清理压缩包文件"""
        if keep_archives:
            self.logger.info("📦 保留所有压缩包文件")
            return 0
            
        cleaned_count = 0
        archive_extensions = ['.tgz', '.tar.gz', '.zip', '.tar']
        
        try:
            for archive_file in self.download_dir.iterdir():
                if archive_file.is_file() and any(archive_file.name.endswith(ext) for ext in archive_extensions):
                    self.logger.info(f"🗑️ 删除压缩包: {archive_file.name}")
                    archive_file.unlink()
                    cleaned_count += 1
            
            self.logger.info(f"✅ 清理完成，删除了 {cleaned_count} 个压缩包")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"❌ 清理压缩包失败: {e}")
            return 0
    
    def process_downloads(self) -> Dict[str, int]:
        """处理所有下载的文件"""
        stats = {
            'extracted': 0,
            'extraction_failed': 0,
            'organized': 0,
            'cleaned': 0
        }
        
        post_config = self.config.get('post_processing', {})
        
        # 1. 自动解压
        if post_config.get('auto_extract', True):
            self.logger.info("🗜️ 开始自动解压...")
            
            archive_extensions = ['.tgz', '.tar.gz', '.zip', '.tar']
            archives = [f for f in self.download_dir.iterdir() 
                       if f.is_file() and any(f.name.endswith(ext) for ext in archive_extensions)]
            
            for archive in archives:
                if self.extract_archive(archive):
                    stats['extracted'] += 1
                    
                    # 验证解压结果
                    if post_config.get('verify_extraction', True):
                        extract_dir = self.download_dir / 'openscene-v1.1'
                        if not self.verify_extraction(archive, extract_dir):
                            stats['extraction_failed'] += 1
                else:
                    stats['extraction_failed'] += 1
        
        # 2. 整理目录结构
        if post_config.get('organize_structure', True):
            if self.organize_structure():
                stats['organized'] = 1
        
        # 3. 清理压缩包
        if post_config.get('cleanup_archives', False):
            stats['cleaned'] = self.cleanup_archives(keep_archives=False)
        else:
            stats['cleaned'] = self.cleanup_archives(keep_archives=True)
        
        return stats 