#!/usr/bin/env python3
"""
NAVSIM 智能下载器一键运行脚本
自动安装依赖、生成配置、开始下载
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖...")
    requirements_file = Path(__file__).parent / 'requirements_downloader.txt'
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True)
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError:
        print("⚠️ 依赖安装失败，尝试手动安装核心包...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                'huggingface_hub', 'tqdm', 'PyYAML', 'requests'
            ], check=True)
            print("✅ 核心依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败，请手动安装:")
            print("pip install huggingface_hub tqdm PyYAML requests")
            return False
    
    return True

def generate_config():
    """生成配置文件"""
    print("⚙️ 生成下载配置...")
    
    try:
        from generate_download_config import generate_complete_config, save_config, print_summary
        
        config = generate_complete_config()
        config_path = Path(__file__).parent / 'smart_download_config_complete.yaml'
        save_config(config, config_path)
        print_summary(config)
        print(f"✅ 配置文件已生成: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ 配置生成失败: {e}")
        return False

def run_downloader():
    """运行下载器"""
    print("🚀 启动智能下载器...")
    
    try:
        from smart_downloader import SmartDownloader
        
        config_path = Path(__file__).parent / 'smart_download_config_complete.yaml'
        downloader = SmartDownloader(str(config_path))
        downloader.run()
        return True
        
    except Exception as e:
        print(f"❌ 下载器运行失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 NAVSIM 智能下载器 - 一键运行")
    print("=" * 50)
    
    # 1. 检查Python版本
    check_python_version()
    
    # 2. 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 3. 生成配置
    if not generate_config():
        sys.exit(1)
    
    # 4. 用户确认
    print("\n" + "=" * 50)
    print("📋 准备开始下载，预计文件数量较多，可能需要几小时到几天时间")
    print("💡 下载过程中可以随时按Ctrl+C中断，下次运行会自动继续")
    print("📁 所有文件将下载到 ./downloads/ 目录")
    
    while True:
        choice = input("\n是否继续？(y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            break
        elif choice in ['n', 'no', '否']:
            print("🛑 用户取消下载")
            sys.exit(0)
        else:
            print("请输入 y 或 n")
    
    # 5. 开始下载
    try:
        run_downloader()
        print("\n🎉 下载完成！")
        
        # 6. 运行后处理
        print("📁 开始后处理...")
        # 这里可以添加后处理逻辑
        
    except KeyboardInterrupt:
        print("\n🛑 下载被用户中断")
        print("💡 下次运行时会自动从中断点继续")
    except Exception as e:
        print(f"\n💥 下载过程出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 