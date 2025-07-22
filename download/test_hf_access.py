#!/usr/bin/env python3
"""
HuggingFace API 访问测试脚本
用于验证仓库访问权限和文件路径
"""

import os
from pathlib import Path

try:
    from huggingface_hub import HfApi, hf_hub_download, list_repo_files
    from huggingface_hub.utils import HfFolder
    HF_AVAILABLE = True
except ImportError:
    print("❌ huggingface_hub 未安装")
    print("请运行: pip install huggingface_hub")
    exit(1)

def check_hf_login():
    """检查HuggingFace登录状态"""
    print("🔐 检查HuggingFace登录状态...")
    
    token = HfFolder.get_token()
    if token:
        print(f"✅ 已登录HuggingFace")
        try:
            api = HfApi()
            user_info = api.whoami()
            print(f"👤 用户: {user_info['name']}")
        except Exception as e:
            print(f"⚠️ 获取用户信息失败: {e}")
    else:
        print("❌ 未登录HuggingFace")
        print("💡 可能需要登录才能访问数据集")
        print("🔑 登录方法:")
        print("   1. 在线登录: huggingface-cli login")
        print("   2. 使用token: export HUGGINGFACE_HUB_TOKEN=your_token")
        print("   3. 创建账号: https://huggingface.co/join")

def test_repository_access():
    """测试仓库访问"""
    print("\n📂 测试仓库访问...")
    
    repo_id = "OpenDriveLab/OpenScene"
    
    try:
        api = HfApi()
        
        # 检查仓库是否存在
        print(f"🔍 检查仓库: {repo_id}")
        repo_info = api.repo_info(repo_id)
        print(f"✅ 仓库存在")
        print(f"   📅 更新时间: {repo_info.lastModified}")
        print(f"   👁️ 私有仓库: {repo_info.private}")
        
        if repo_info.private:
            print("⚠️ 这是一个私有仓库，需要权限访问")
        
        return True, repo_info
        
    except Exception as e:
        print(f"❌ 仓库访问失败: {e}")
        return False, None

def list_repository_files(repo_id, max_files=20):
    """列出仓库文件"""
    print(f"\n📋 列出仓库文件 (前{max_files}个)...")
    
    try:
        # 列出所有文件
        files = list_repo_files(repo_id)
        
        print(f"📁 总文件数: {len(files)}")
        
        # 显示前几个文件
        for i, file_path in enumerate(files[:max_files]):
            print(f"   {i+1:2d}. {file_path}")
        
        if len(files) > max_files:
            print(f"   ... 还有 {len(files) - max_files} 个文件")
        
        # 查找相关文件
        print(f"\n🔍 查找相关文件:")
        
        # 查找openscene相关文件
        openscene_files = [f for f in files if 'openscene' in f.lower()]
        print(f"📦 openscene相关文件: {len(openscene_files)}")
        for f in openscene_files[:5]:
            print(f"   • {f}")
        
        # 查找trainval相关文件
        trainval_files = [f for f in files if 'trainval' in f.lower()]
        print(f"🚂 trainval相关文件: {len(trainval_files)}")
        for f in trainval_files[:5]:
            print(f"   • {f}")
        
        return files
        
    except Exception as e:
        print(f"❌ 列出文件失败: {e}")
        return []

def test_download_small_file(repo_id, files):
    """尝试下载一个小文件进行测试"""
    print(f"\n📥 测试下载小文件...")
    
    # 寻找一个小的文件进行测试
    test_files = [
        f for f in files 
        if any(keyword in f.lower() for keyword in ['readme', '.md', '.txt', '.json']) 
        and f.endswith(('.md', '.txt', '.json', '.csv'))
    ]
    
    if not test_files:
        print("⚠️ 未找到合适的测试文件")
        return False
    
    test_file = test_files[0]
    print(f"🎯 测试文件: {test_file}")
    
    try:
        # 下载到临时目录
        temp_dir = Path('./temp_test')
        temp_dir.mkdir(exist_ok=True)
        
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=test_file,
            local_dir=str(temp_dir),
            local_dir_use_symlinks=False
        )
        
        file_size = Path(downloaded_path).stat().st_size
        print(f"✅ 下载成功: {test_file}")
        print(f"📁 路径: {downloaded_path}")
        print(f"💾 大小: {file_size} bytes")
        
        # 清理测试文件
        Path(downloaded_path).unlink()
        temp_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"❌ 下载测试失败: {e}")
        return False

def check_original_urls():
    """检查原始下载URL是否可访问"""
    print(f"\n🌐 检查原始下载URL...")
    
    import requests
    
    test_urls = [
        "https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1/openscene_metadata_mini.tgz",
        "https://huggingface.co/datasets/OpenDriveLab/OpenScene/tree/main",
        "https://huggingface.co/OpenDriveLab/OpenScene",
    ]
    
    for url in test_urls:
        try:
            print(f"🔗 测试: {url}")
            response = requests.head(url, timeout=10)
            print(f"   📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 可访问")
            elif response.status_code == 401:
                print(f"   🔐 需要认证")
            elif response.status_code == 404:
                print(f"   ❌ 未找到")
            else:
                print(f"   ⚠️ 其他状态")
                
        except Exception as e:
            print(f"   💥 请求失败: {e}")

def main():
    """主函数"""
    print("🧪 HuggingFace API 访问测试")
    print("=" * 50)
    
    # 1. 检查登录状态
    check_hf_login()
    
    # 2. 测试仓库访问
    success, repo_info = test_repository_access()
    
    if not success:
        print("\n🚨 无法访问仓库，可能需要:")
        print("1. 登录HuggingFace账号")
        print("2. 申请数据集访问权限")
        print("3. 检查仓库地址是否正确")
        
        # 检查原始URL
        check_original_urls()
        return
    
    # 3. 列出文件
    files = list_repository_files("OpenDriveLab/OpenScene")
    
    if files:
        # 4. 测试下载
        test_download_small_file("OpenDriveLab/OpenScene", files)
    
    print(f"\n💡 建议:")
    print("1. 如果是私有仓库，需要申请访问权限")
    print("2. 可能需要HuggingFace Pro账号")
    print("3. 考虑使用原始wget方式下载")

if __name__ == '__main__':
    main() 