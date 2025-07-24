#!/bin/bash

# 临时脚本：重新下载失败的特定文件
# 基于原始下载脚本的操作方式

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%H:%M:%S') $1"
}

# OBS 路径配置
OBS_OPENSCENE_BASE="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
OBS_NAVSIM_BASE="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2"

# 统计变量
TOTAL_FILES=0
SUCCESSFUL_DOWNLOADS=0
FAILED_DOWNLOADS=0

# 下载单个文件的函数
download_file() {
    local obs_path="$1"
    local local_filename="$2"
    local description="$3"
    
    TOTAL_FILES=$((TOTAL_FILES + 1))
    
    log_info "开始下载: $description"
    log_info "文件: $local_filename"
    
    if di-mc cp "$obs_path" "$local_filename"; then
        log_success "下载完成: $local_filename"
        SUCCESSFUL_DOWNLOADS=$((SUCCESSFUL_DOWNLOADS + 1))
        return 0
    else
        log_error "下载失败: $local_filename"
        FAILED_DOWNLOADS=$((FAILED_DOWNLOADS + 1))
        return 1
    fi
}

# 解压文件的函数
extract_file() {
    local filename="$1"
    local description="$2"
    
    if [ -f "$filename" ]; then
        log_info "开始解压: $description"
        if tar -xzf "$filename"; then
            log_success "解压完成: $filename"
            rm "$filename"
            log_info "清理压缩文件: $filename"
            return 0
        else
            log_error "解压失败: $filename"
            return 1
        fi
    else
        log_warning "文件不存在，跳过解压: $filename"
        return 1
    fi
}

echo "================================================="
echo "NAVSIM 失败文件重新下载脚本"
echo "开始时间: $(date)"
echo "================================================="

# 1. 下载 trainval camera 文件
log_info "=== 下载 openscene_sensor_trainval_camera 文件 ==="
TRAINVAL_CAMERA_SPLITS=(101)

for split in "${TRAINVAL_CAMERA_SPLITS[@]}"; do
    local_file="openscene_sensor_trainval_camera_${split}.tgz"
    obs_path="${OBS_OPENSCENE_BASE}/openscene_sensor_trainval_camera/${local_file}"
    download_file "$obs_path" "$local_file" "Trainval Camera Split $split"
    
    # 解压文件
    extract_file "$local_file" "Trainval Camera Split $split"
done

# 2. 下载 trainval lidar 文件
log_info "=== 下载 openscene_sensor_trainval_lidar 文件 ==="
TRAINVAL_LIDAR_SPLITS=(21 74)

for split in "${TRAINVAL_LIDAR_SPLITS[@]}"; do
    local_file="openscene_sensor_trainval_lidar_${split}.tgz"
    obs_path="${OBS_OPENSCENE_BASE}/openscene_sensor_trainval_lidar/${local_file}"
    download_file "$obs_path" "$local_file" "Trainval Lidar Split $split"
    
    # 解压文件
    extract_file "$local_file" "Trainval Lidar Split $split"
done

# 3. 下载 test camera 文件
log_info "=== 下载 openscene_sensor_test_camera 文件 ==="
TEST_CAMERA_SPLITS=(0 9 15)

for split in "${TEST_CAMERA_SPLITS[@]}"; do
    local_file="openscene_sensor_test_camera_${split}.tgz"
    obs_path="${OBS_OPENSCENE_BASE}/openscene_sensor_test_camera/${local_file}"
    download_file "$obs_path" "$local_file" "Test Camera Split $split"
    
    # 解压文件
    extract_file "$local_file" "Test Camera Split $split"
done

# 3. 下载 test camera 文件
log_info "=== 下载 openscene_sensor_test_lidar 文件 ==="
TEST_LIDAR_SPLITS=(30)

for split in "${TEST_LIDAR_SPLITS[@]}"; do
    local_file="openscene_sensor_test_lidar_${split}.tgz"
    obs_path="${OBS_OPENSCENE_BASE}/openscene_sensor_test_lidar/${local_file}"
    download_file "$obs_path" "$local_file" "Test Lidar Split $split"
    
    # 解压文件
    extract_file "$local_file" "Test Lidar Split $split"
done


# 5. 处理解压后的目录结构
log_info "=== 整理目录结构 ==="

# 处理 openscene-v1.1 目录（如果存在）
if [ -d "openscene-v1.1" ]; then
    log_info "处理 openscene-v1.1 目录结构..."
    
    # 合并到现有的目录
    if [ -d "openscene-v1.1/sensor_blobs/trainval" ] && [ -d "trainval_sensor_blobs/trainval" ]; then
        log_info "合并 trainval sensor blobs..."
        rsync -av openscene-v1.1/sensor_blobs/trainval/ trainval_sensor_blobs/trainval/
    elif [ -d "openscene-v1.1/sensor_blobs/trainval" ]; then
        log_info "移动 trainval sensor blobs..."
        mkdir -p trainval_sensor_blobs
        mv openscene-v1.1/sensor_blobs/trainval trainval_sensor_blobs/
    fi
    
    if [ -d "openscene-v1.1/sensor_blobs/test" ] && [ -d "test_sensor_blobs/test" ]; then
        log_info "合并 test sensor blobs..."
        rsync -av openscene-v1.1/sensor_blobs/test/ test_sensor_blobs/test/
    elif [ -d "openscene-v1.1/sensor_blobs/test" ]; then
        log_info "移动 test sensor blobs..."
        mkdir -p test_sensor_blobs
        mv openscene-v1.1/sensor_blobs/test test_sensor_blobs/
    fi
    
    # 清理临时目录
    rm -rf openscene-v1.1
    log_info "清理临时目录: openscene-v1.1"
fi

echo "================================================="
echo "下载完成统计"
echo "================================================="
echo "总文件数: $TOTAL_FILES"
echo -e "${GREEN}成功下载: $SUCCESSFUL_DOWNLOADS${NC}"
echo -e "${RED}失败下载: $FAILED_DOWNLOADS${NC}"
echo "完成时间: $(date)"
echo "================================================="

if [ $FAILED_DOWNLOADS -gt 0 ]; then
    log_warning "仍有 $FAILED_DOWNLOADS 个文件下载失败，请检查网络连接或手动重试"
    exit 1
else
    log_success "所有文件下载成功！"
    exit 0
fi 