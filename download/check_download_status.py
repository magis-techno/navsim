#!/usr/bin/env python3
"""
NAVSIM Dataset Download Status Checker
检查NAVSIM数据集的下载状态
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

def check_path_exists(path_str, description):
    """检查路径是否存在并返回状态"""
    path = Path(path_str).expanduser()
    if path.exists():
        if path.is_dir():
            item_count = len(list(path.iterdir())) if path.is_dir() else 0
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            size_mb = size / (1024 * 1024)
            return {
                'exists': True,
                'type': 'directory',
                'items': item_count,
                'size_mb': round(size_mb, 2),
                'path': str(path)
            }
        else:
            size = path.stat().st_size / (1024 * 1024)
            return {
                'exists': True,
                'type': 'file',
                'size_mb': round(size, 2),
                'path': str(path)
            }
    else:
        return {
            'exists': False,
            'type': 'missing',
            'path': str(path)
        }

def check_environment_variables():
    """检查环境变量设置"""
    env_vars = {
        'NUPLAN_MAP_VERSION': os.getenv('NUPLAN_MAP_VERSION'),
        'NUPLAN_MAPS_ROOT': os.getenv('NUPLAN_MAPS_ROOT'),
        'NAVSIM_EXP_ROOT': os.getenv('NAVSIM_EXP_ROOT'),
        'NAVSIM_DEVKIT_ROOT': os.getenv('NAVSIM_DEVKIT_ROOT'),
        'OPENSCENE_DATA_ROOT': os.getenv('OPENSCENE_DATA_ROOT')
    }
    
    print("🔧 环境变量检查:")
    print("=" * 50)
    for var, value in env_vars.items():
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")
    print()
    return env_vars

def get_expected_structure():
    """定义期望的目录结构"""
    return {
        'maps': {
            'description': 'nuPlan Maps',
            'paths': [
                '~/navsim_workspace/dataset/maps',
                './download/maps',
                './maps'
            ]
        },
        'mini_logs': {
            'description': 'Mini Dataset Logs',
            'paths': [
                '~/navsim_workspace/dataset/navsim_logs/mini',
                './download/mini_navsim_logs',
                './mini_navsim_logs'
            ]
        },
        'mini_sensors': {
            'description': 'Mini Dataset Sensor Blobs',
            'paths': [
                '~/navsim_workspace/dataset/sensor_blobs/mini',
                './download/mini_sensor_blobs',
                './mini_sensor_blobs'
            ]
        },
        'trainval_logs': {
            'description': 'TrainVal Dataset Logs',
            'paths': [
                '~/navsim_workspace/dataset/navsim_logs/trainval',
                './download/trainval_navsim_logs',
                './trainval_navsim_logs'
            ]
        },
        'trainval_sensors': {
            'description': 'TrainVal Dataset Sensor Blobs',
            'paths': [
                '~/navsim_workspace/dataset/sensor_blobs/trainval',
                './download/trainval_sensor_blobs',
                './trainval_sensor_blobs'
            ]
        },
        'test_logs': {
            'description': 'Test Dataset Logs',
            'paths': [
                '~/navsim_workspace/dataset/navsim_logs/test',
                './download/test_navsim_logs',
                './test_navsim_logs'
            ]
        },
        'test_sensors': {
            'description': 'Test Dataset Sensor Blobs',
            'paths': [
                '~/navsim_workspace/dataset/sensor_blobs/test',
                './download/test_sensor_blobs',
                './test_sensor_blobs'
            ]
        },
        'navhard_two_stage': {
            'description': 'NavHard Two Stage Dataset',
            'paths': [
                '~/navsim_workspace/dataset/navhard_two_stage',
                './download/navhard_two_stage',
                './navhard_two_stage'
            ]
        },
        'warmup_two_stage': {
            'description': 'Warmup Two Stage Dataset',
            'paths': [
                '~/navsim_workspace/dataset/warmup_two_stage',
                './download/warmup_two_stage',
                './warmup_two_stage'
            ]
        },
        'private_test_hard_two_stage': {
            'description': 'Private Test Hard Two Stage',
            'paths': [
                '~/navsim_workspace/dataset/private_test_hard_two_stage',
                './download/private_test_hard_two_stage',
                './private_test_hard_two_stage'
            ]
        },
        'private_test_hard_logs': {
            'description': 'Private Test Hard Logs',
            'paths': [
                '~/navsim_workspace/dataset/navsim_logs/private_test_hard',
                './download/private_test_hard_navsim_log',
                './private_test_hard_navsim_log'
            ]
        },
        'private_test_hard_sensors': {
            'description': 'Private Test Hard Sensor Blobs',
            'paths': [
                '~/navsim_workspace/dataset/sensor_blobs/private_test_hard',
                './download/private_test_hard_navsim_sensor',
                './private_test_hard_navsim_sensor'
            ]
        }
    }

def check_download_status():
    """检查所有数据集的下载状态"""
    print("🔍 NAVSIM 数据集下载状态检查")
    print("=" * 60)
    
    # 检查环境变量
    env_vars = check_environment_variables()
    
    # 检查数据集状态
    structure = get_expected_structure()
    found_data = {}
    total_size = 0
    
    print("📁 数据集状态检查:")
    print("=" * 50)
    
    for dataset_key, dataset_info in structure.items():
        print(f"\n🔸 {dataset_info['description']}:")
        found = False
        
        for path_str in dataset_info['paths']:
            status = check_path_exists(path_str, dataset_info['description'])
            if status['exists']:
                print(f"   ✅ 找到: {status['path']}")
                if status['type'] == 'directory':
                    print(f"      📂 {status['items']} 个项目, {status['size_mb']:.1f} MB")
                else:
                    print(f"      📄 {status['size_mb']:.1f} MB")
                found_data[dataset_key] = status
                total_size += status['size_mb']
                found = True
                break
            
        if not found:
            print(f"   ❌ 未找到")
            # 显示查找的路径
            for path_str in dataset_info['paths']:
                print(f"      🔍 已检查: {Path(path_str).expanduser()}")
    
    # 总结
    print(f"\n📊 总结:")
    print("=" * 50)
    print(f"✅ 已找到数据集: {len(found_data)}/{len(structure)}")
    print(f"💾 总数据大小: {total_size:.1f} MB ({total_size/1024:.1f} GB)")
    
    # 检查压缩包残留
    print(f"\n🗑️ 压缩包残留检查:")
    print("=" * 50)
    
    archive_patterns = [
        '*.tgz', '*.tar.gz', '*.zip', '*.tar'
    ]
    
    search_dirs = ['./download', '.', '~/navsim_workspace/dataset']
    for search_dir in search_dirs:
        search_path = Path(search_dir).expanduser()
        if search_path.exists():
            for pattern in archive_patterns:
                archives = list(search_path.glob(pattern))
                if archives:
                    print(f"📁 {search_dir}:")
                    for archive in archives:
                        size_mb = archive.stat().st_size / (1024 * 1024)
                        print(f"   📦 {archive.name} ({size_mb:.1f} MB)")
    
    # 生成状态报告
    report = {
        'timestamp': str(Path.cwd()),
        'environment_variables': env_vars,
        'found_datasets': found_data,
        'total_size_mb': total_size,
        'completion_rate': len(found_data) / len(structure)
    }
    
    # 保存状态报告
    report_file = Path('./download_status_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    
    return found_data, total_size

def suggest_next_steps(found_data):
    """建议下一步操作"""
    all_datasets = set(get_expected_structure().keys())
    missing_datasets = all_datasets - set(found_data.keys())
    
    print(f"\n💡 建议的下一步操作:")
    print("=" * 50)
    
    if missing_datasets:
        print("❌ 缺失的数据集:")
        for dataset in missing_datasets:
            description = get_expected_structure()[dataset]['description']
            print(f"   • {description} ({dataset})")
        
        print(f"\n🚀 你可以:")
        print("1. 使用我接下来创建的智能下载脚本")
        print("2. 或手动运行对应的下载脚本:")
        
        script_mapping = {
            'maps': 'download_maps.sh',
            'mini_logs': 'download_mini.sh',
            'mini_sensors': 'download_mini.sh',
            'trainval_logs': 'download_trainval.sh', 
            'trainval_sensors': 'download_trainval.sh',
            'test_logs': 'download_test.sh',
            'test_sensors': 'download_test.sh',
            'navhard_two_stage': 'download_navhard_two_stage.sh',
            'warmup_two_stage': 'download_warmup_two_stage.sh',
            'private_test_hard_two_stage': 'download_private_test_hard_two_stage.sh',
            'private_test_hard_logs': 'download_private_test_hard_two_stage.sh',
            'private_test_hard_sensors': 'download_private_test_hard_two_stage.sh'
        }
        
        for dataset in missing_datasets:
            if dataset in script_mapping:
                print(f"   • {script_mapping[dataset]} (for {dataset})")
    else:
        print("🎉 所有数据集都已下载完成!")
        print("📁 建议按照install.md整理目录结构")

if __name__ == "__main__":
    try:
        found_data, total_size = check_download_status()
        suggest_next_steps(found_data)
        
    except KeyboardInterrupt:
        print("\n\n🛑 检查被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        sys.exit(1) 