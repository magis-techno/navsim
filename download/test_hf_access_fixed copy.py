#!/usr/bin/env python3
"""
HuggingFace API 访问测试脚本 (修正版)
正确使用数据集API类型
"""

import os
import requests
from pathlib import Path

try:
    from huggingface_hub import HfApi, hf_hub_download, list_repo_files
    from huggingface_hub.utils import HfFolder
    HF_AVAILABLE = True
except ImportError:
    print("❌ huggingface_hub 未安装")
    HF_AVAILABLE = False

def test_direct_http_access():
    """测试直接HTTP访问（像wget一样）"""
    print("🌐 测试直接HTTP访问（wget方式）...")
    
    test_urls = [
        "https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1/openscene_metadata_mini.tgz",
        "https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1/openscene_sensor_mini_camera/openscene_sensor_mini_camera_0.tgz",
    ]
    
    working_urls = []
    
    for url in test_urls:
        try:
            print(f"🔗 测试: {url}")
            
            # 发送HEAD请求检查
            response = requests.head(url, timeout=10, allow_redirects=True)
            print(f"   📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 可直接访问")
                content_length = response.headers.get('content-length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    print(f"   💾 文件大小: {size_mb:.1f} MB")
                working_urls.append(url)
            elif response.status_code == 302:
                print(f"   🔄 重定向到实际文件位置")
                working_urls.append(url)
            else:
                print(f"   ❌ 无法访问")
                
        except Exception as e:
            print(f"   💥 请求失败: {e}")
    
    return working_urls

def test_hf_api_with_dataset_type():
    """使用正确的数据集类型测试HF API"""
    if not HF_AVAILABLE:
        print("⚠️ HuggingFace Hub 不可用，跳过API测试")
        return False
        
    print("\n🔧 测试HuggingFace API（数据集类型）...")
    
    repo_id = "OpenDriveLab/OpenScene"
    
    try:
        api = HfApi()
        
        # 使用正确的repo_type
        print(f"🔍 检查数据集: {repo_id}")
        repo_info = api.repo_info(repo_id, repo_type="dataset")
        print(f"✅ 数据集存在")
        print(f"   📅 更新时间: {repo_info.lastModified}")
        print(f"   👁️ 私有数据集: {repo_info.private}")
        
        if repo_info.private:
            print("⚠️ 这是一个私有数据集，需要权限访问")
            return False
        
        # 列出文件
        print(f"\n📋 列出数据集文件...")
        files = list_repo_files(repo_id, repo_type="dataset")
        print(f"📁 总文件数: {len(files)}")
        
        # 显示相关文件
        openscene_files = [f for f in files if 'openscene' in f.lower()][:5]
        for f in openscene_files:
            print(f"   • {f}")
        
        return True
        
    except Exception as e:
        print(f"❌ API访问失败: {e}")
        return False

def test_small_download_via_api():
    """通过API测试小文件下载"""
    if not HF_AVAILABLE:
        return False
        
    print(f"\n📥 测试API下载...")
    
    repo_id = "OpenDriveLab/OpenScene"
    
    try:
        # 尝试下载一个相对较小的文件
        test_file = "openscene-v1.1/openscene_metadata_mini.tgz"
        
        print(f"🎯 测试文件: {test_file}")
        
        temp_dir = Path('./temp_api_test')
        temp_dir.mkdir(exist_ok=True)
        
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=test_file,
            local_dir=str(temp_dir),
            repo_type="dataset"  # 关键：指定数据集类型
        )
        
        file_size = Path(downloaded_path).stat().st_size / (1024 * 1024)
        print(f"✅ API下载成功: {test_file}")
        print(f"📁 路径: {downloaded_path}")
        print(f"💾 大小: {file_size:.1f} MB")
        
        # 清理
        Path(downloaded_path).unlink()
        temp_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"❌ API下载失败: {e}")
        return False

def test_wget_download():
    """测试wget下载"""
    print(f"\n📥 测试wget下载...")
    
    import subprocess
    
    # 测试一个小文件
    test_url = "https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/openscene-v1.1/openscene_metadata_mini.tgz"
    output_file = Path('./temp_wget_test.tgz')
    
    try:
        print(f"🎯 wget下载: openscene_metadata_mini.tgz")
        
        cmd = [
            'wget',
            '--timeout=30',
            '--tries=2',
            '-O', str(output_file),
            test_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and output_file.exists():
            file_size = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ wget下载成功")
            print(f"💾 大小: {file_size:.1f} MB")
            
            # 清理
            output_file.unlink()
            return True
        else:
            print(f"❌ wget下载失败")
            print(f"错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ wget测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 HuggingFace 访问测试 (修正版)")
    print("=" * 50)
    
    # 1. 测试直接HTTP访问
    working_urls = test_direct_http_access()
    
    # 2. 测试HF API（正确的数据集类型）
    api_works = test_hf_api_with_dataset_type()
    
    # 3. 如果API可用，测试API下载
    if api_works:
        api_download_works = test_small_download_via_api()
    else:
        api_download_works = False
    
    # 4. 测试wget下载
    wget_works = test_wget_download()
    
    # 总结
    print(f"\n📊 测试结果总结:")
    print("=" * 30)
    print(f"🌐 HTTP直接访问: {'✅ 可用' if working_urls else '❌ 不可用'}")
    print(f"🔧 HuggingFace API: {'✅ 可用' if api_works else '❌ 需要登录/权限'}")
    print(f"📥 API下载: {'✅ 可用' if api_download_works else '❌ 不可用'}")
    print(f"📥 wget下载: {'✅ 可用' if wget_works else '❌ 不可用'}")
    
    print(f"\n💡 建议方案:")
    if api_download_works:
        print("🥇 优先使用HuggingFace API（最稳定）")
    elif wget_works:
        print("🥈 使用wget下载（直接HTTP访问）")
        print("   原因：API需要认证，但HTTP直接访问不需要")
    else:
        print("🆘 需要进一步排查网络连接问题")

if __name__ == '__main__':
    main() 