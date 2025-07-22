#!/usr/bin/env python3
"""
NAVSIM Download Configuration Generator
根据用户已完成状态生成完整的下载配置文件
"""

import yaml
from pathlib import Path

def generate_complete_config():
    """生成完整的下载配置"""
    
    # 已完成的下载（根据用户提供的信息）
    completed_downloads = {
        # Maps - 全部完成
        'maps': [
            'nuplan-maps-v1.1.zip'
        ],
        
        # Warmup Two Stage - 全部完成  
        'warmup_two_stage': [
            'navsim_v2.2_warmup_two_stage.tar.gz'
        ],
        
        # Mini Dataset - 部分完成
        'mini': [
            'openscene_metadata_mini.tgz',
            'openscene_sensor_mini_camera_1.tgz',
            'openscene_sensor_mini_camera_2.tgz', 
            'openscene_sensor_mini_camera_3.tgz',
            'openscene_sensor_mini_camera_4.tgz',
            'openscene_sensor_mini_camera_5.tgz',
            'openscene_sensor_mini_camera_6.tgz'
        ],
        
        # TrainVal Dataset - 部分完成
        'trainval': [
            'openscene_sensor_trainval_camera_0.tgz',
            'openscene_sensor_trainval_camera_1.tgz'
            # 注意：metadata失败了，不在已完成列表中
        ],
        
        # Test Dataset - 部分完成
        'test': [
            'openscene_metadata_test.tgz',
            'openscene_sensor_test_camera_0.tgz',
            'openscene_sensor_test_camera_1.tgz',
            'openscene_sensor_test_camera_4.tgz'
            # 注意：camera_2,3失败了，不在已完成列表中
        ],
        
        # NavHard Two Stage - 部分完成
        'navhard_two_stage': [
            'navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz'
        ],
        
        # Private Test Hard - 部分完成
        'private_test_hard': [
            'openscene_metadata_private_test_hard.tar.gz',
            'openscene_sensor_private_test_hard.tar.gz'
        ]
    }
    
    # 生成下载任务
    download_tasks = {}
    
    # 1. Mini Dataset 剩余文件
    mini_files = []
    
    # Mini Camera files (缺少 0, 7-31)
    missing_mini_camera = [0] + list(range(7, 32))
    for i in missing_mini_camera:
        mini_files.append({
            'path': f'openscene-v1.1/openscene_sensor_mini_camera/openscene_sensor_mini_camera_{i}.tgz',
            'size_estimate_mb': 500
        })
    
    # Mini LiDAR files (全部缺失 0-31)
    for i in range(32):
        mini_files.append({
            'path': f'openscene-v1.1/openscene_sensor_mini_lidar/openscene_sensor_mini_lidar_{i}.tgz',
            'size_estimate_mb': 300
        })
    
    download_tasks['mini_remaining'] = {
        'priority': 2,
        'repository': 'OpenDriveLab/OpenScene',
        'files': mini_files
    }
    
    # 2. TrainVal Dataset 剩余文件
    trainval_files = []
    
    # TrainVal Metadata (失败重下)
    trainval_files.append({
        'path': 'openscene-v1.1/openscene_metadata_trainval.tgz',
        'size_estimate_mb': 100
    })
    
    # TrainVal Camera files (缺少 2-199)
    for i in range(2, 200):
        trainval_files.append({
            'path': f'openscene-v1.1/openscene_sensor_trainval_camera/openscene_sensor_trainval_camera_{i}.tgz',
            'size_estimate_mb': 800
        })
    
    # TrainVal LiDAR files (全部缺失 0-199)
    for i in range(200):
        trainval_files.append({
            'path': f'openscene-v1.1/openscene_sensor_trainval_lidar/openscene_sensor_trainval_lidar_{i}.tgz',
            'size_estimate_mb': 500
        })
    
    download_tasks['trainval_remaining'] = {
        'priority': 1,  # 最高优先级
        'repository': 'OpenDriveLab/OpenScene',
        'files': trainval_files
    }
    
    # 3. Test Dataset 剩余文件
    test_files = []
    
    # Test Camera files (失败重下: 2,3 + 缺少: 5-31)
    missing_test_camera = [2, 3] + list(range(5, 32))
    for i in missing_test_camera:
        test_files.append({
            'path': f'openscene-v1.1/openscene_sensor_test_camera/openscene_sensor_test_camera_{i}.tgz',
            'size_estimate_mb': 500
        })
    
    # Test LiDAR files (全部缺失 0-31)
    for i in range(32):
        test_files.append({
            'path': f'openscene-v1.1/openscene_sensor_test_lidar/openscene_sensor_test_lidar_{i}.tgz',
            'size_estimate_mb': 300
        })
    
    download_tasks['test_remaining'] = {
        'priority': 2,
        'repository': 'OpenDriveLab/OpenScene',
        'files': test_files
    }
    
    # 4. NavHard Two Stage 剩余文件
    navhard_files = [
        {
            'path': 'navsim-v2/navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz',
            'size_estimate_mb': 2000
        },
        {
            'path': 'navsim-v2/navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz',
            'size_estimate_mb': 1000
        }
    ]
    
    download_tasks['navhard_remaining'] = {
        'priority': 3,
        'repository': 'OpenDriveLab/OpenScene',
        'files': navhard_files
    }
    
    # 5. Private Test Hard 剩余文件
    private_test_files = [
        {
            'path': 'navsim-v2/navsim_v2.2_private_test_hard_two_stage.tar.gz',
            'size_estimate_mb': 3000
        }
    ]
    
    download_tasks['private_test_remaining'] = {
        'priority': 4,
        'repository': 'OpenDriveLab/OpenScene',
        'files': private_test_files
    }
    
    # 完整配置
    config = {
        'repository': 'OpenDriveLab/OpenScene',
        'base_path': 'openscene-v1.1',
        
        'global_settings': {
            'max_concurrent': 3,
            'max_retries': 5,
            'retry_delay_base': 2,
            'chunk_size': 8388608,  # 8MB
            'timeout': 300,
            'verify_size': True,
            'keep_temp': True
        },
        
        'completed_downloads': completed_downloads,
        'download_tasks': download_tasks,
        
        'post_processing': {
            'auto_extract': True,
            'verify_extraction': True,
            'cleanup_archives': False,
            'organize_structure': True
        }
    }
    
    return config

def save_config(config, output_path):
    """保存配置到YAML文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)

def print_summary(config):
    """打印下载任务摘要"""
    print("🔍 NAVSIM 智能下载配置生成完成")
    print("=" * 50)
    
    total_files = 0
    total_size_mb = 0
    
    for task_name, task_info in config['download_tasks'].items():
        file_count = len(task_info['files'])
        task_size = sum(f['size_estimate_mb'] for f in task_info['files'])
        priority = task_info['priority']
        
        print(f"\n📁 {task_name}:")
        print(f"   优先级: {priority}")
        print(f"   文件数: {file_count}")
        print(f"   预估大小: {task_size:.0f} MB ({task_size/1024:.1f} GB)")
        
        total_files += file_count
        total_size_mb += task_size
    
    print(f"\n📊 总计:")
    print(f"   总文件数: {total_files}")
    print(f"   总大小: {total_size_mb:.0f} MB ({total_size_mb/1024:.1f} GB)")
    
    # 已完成统计
    completed_count = sum(len(files) for files in config['completed_downloads'].values())
    print(f"   已完成: {completed_count} 个文件")
    print(f"   完成率: {completed_count/(completed_count + total_files)*100:.1f}%")

if __name__ == '__main__':
    # 生成配置
    config = generate_complete_config()
    
    # 保存配置文件
    output_path = Path(__file__).parent / 'smart_download_config_complete.yaml'
    save_config(config, output_path)
    
    # 打印摘要
    print_summary(config)
    
    print(f"\n✅ 完整配置已保存到: {output_path}")
    print("📝 你可以编辑此文件来调整下载优先级或添加/移除特定文件") 