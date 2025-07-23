#!/bin/bash

# NAVSIM 高级下载脚本
# 支持续点下载、并行下载、进度监控

# 导入状态管理器
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/download_status_manager.sh"

# 配置参数
DEFAULT_MAX_PARALLEL_DATASETS=2
DEFAULT_MAX_PARALLEL_FILES=4
DEFAULT_MAX_TOTAL_JOBS=8
DEFAULT_RETRY_ATTEMPTS=3
DEFAULT_RETRY_DELAY=5

# 命令行参数
MAX_PARALLEL_DATASETS=${DEFAULT_MAX_PARALLEL_DATASETS}
MAX_PARALLEL_FILES=${DEFAULT_MAX_PARALLEL_FILES}
MAX_TOTAL_JOBS=${DEFAULT_MAX_TOTAL_JOBS}
RETRY_ATTEMPTS=${DEFAULT_RETRY_ATTEMPTS}
RETRY_DELAY=${DEFAULT_RETRY_DELAY}
RESUME_MODE=false
FORCE_REDOWNLOAD=false
SHOW_PROGRESS=true
QUIET_MODE=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志配置
LOG_DIR="./download_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/advanced_download_${TIMESTAMP}.log"
SUMMARY_FILE="${LOG_DIR}/advanced_summary_${TIMESTAMP}.txt"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 全局变量
declare -A ACTIVE_JOBS
declare -A DATASET_JOBS
declare -A DOWNLOAD_PIDS
TOTAL_ACTIVE_JOBS=0
JOBS_COMPLETED=0
JOBS_FAILED=0

# 日志函数
log_msg() {
    local level="$1"
    local color="$2"
    local message="$3"
    local timestamp=$(date '+%H:%M:%S')
    
    if [ "$QUIET_MODE" != "true" ]; then
        echo -e "${color}[${level}]${NC} ${timestamp} ${message}" | tee -a "${LOG_FILE}"
    else
        echo -e "${color}[${level}]${NC} ${timestamp} ${message}" >> "${LOG_FILE}"
    fi
}

log_info() {
    log_msg "INFO" "$BLUE" "$1"
}

log_success() {
    log_msg "SUCCESS" "$GREEN" "$1"
}

log_warning() {
    log_msg "WARNING" "$YELLOW" "$1"
}

log_error() {
    log_msg "ERROR" "$RED" "$1"
}

log_debug() {
    log_msg "DEBUG" "$PURPLE" "$1"
}

# 进度显示函数
show_progress_bar() {
    local current="$1"
    local total="$2"
    local width=50
    local percentage=0
    
    if [ "$total" -gt 0 ]; then
        percentage=$((current * 100 / total))
    fi
    
    local completed=$((current * width / total))
    local remaining=$((width - completed))
    
    printf "["
    printf "%*s" $completed | tr ' ' '='
    if [ $remaining -gt 0 ]; then
        printf ">"
        printf "%*s" $((remaining - 1)) | tr ' ' '-'
    fi
    printf "] %d%% (%d/%d)" $percentage $current $total
}

# 实时状态显示
show_live_status() {
    if [ "$SHOW_PROGRESS" != "true" ] || [ "$QUIET_MODE" = "true" ]; then
        return
    fi
    
    clear
    echo -e "${CYAN}===================================${NC}"
    echo -e "${CYAN}    NAVSIM 高级下载器 - 实时状态    ${NC}"
    echo -e "${CYAN}===================================${NC}"
    echo ""
    
    # 显示总体进度
    local total_jobs=$((JOBS_COMPLETED + JOBS_FAILED + TOTAL_ACTIVE_JOBS))
    if [ $total_jobs -gt 0 ]; then
        echo -e "${BLUE}总体进度:${NC}"
        show_progress_bar $((JOBS_COMPLETED + JOBS_FAILED)) $total_jobs
        echo ""
        echo ""
    fi
    
    # 显示活跃任务
    echo -e "${BLUE}活跃任务: ${GREEN}${TOTAL_ACTIVE_JOBS}${NC}/${MAX_TOTAL_JOBS}"
    echo -e "${BLUE}已完成: ${GREEN}${JOBS_COMPLETED}${NC} | ${BLUE}失败: ${RED}${JOBS_FAILED}${NC}"
    echo ""
    
    # 显示各数据集状态
    for dataset in "${!DATASET_JOBS[@]}"; do
        local active_count=${DATASET_JOBS[$dataset]}
        if [ "$active_count" -gt 0 ]; then
            echo -e "${YELLOW}${dataset}:${NC} ${active_count} 个任务进行中"
        fi
    done
    
    echo ""
    echo -e "${PURPLE}按 Ctrl+C 取消下载${NC}"
}

# 任务管理
start_job() {
    local dataset="$1"
    local job_id="$2"
    
    ACTIVE_JOBS["$job_id"]=1
    DATASET_JOBS["$dataset"]=$((${DATASET_JOBS["$dataset"]:-0} + 1))
    TOTAL_ACTIVE_JOBS=$((TOTAL_ACTIVE_JOBS + 1))
}

finish_job() {
    local dataset="$1"
    local job_id="$2"
    local success="$3"
    
    unset ACTIVE_JOBS["$job_id"]
    DATASET_JOBS["$dataset"]=$((${DATASET_JOBS["$dataset"]:-1} - 1))
    TOTAL_ACTIVE_JOBS=$((TOTAL_ACTIVE_JOBS - 1))
    
    if [ "$success" = "true" ]; then
        JOBS_COMPLETED=$((JOBS_COMPLETED + 1))
    else
        JOBS_FAILED=$((JOBS_FAILED + 1))
    fi
}

# 等待可用槽位
wait_for_slot() {
    local max_jobs="$1"
    
    while [ "$TOTAL_ACTIVE_JOBS" -ge "$max_jobs" ]; do
        sleep 1
        # 清理已完成的后台任务
        for pid in "${!DOWNLOAD_PIDS[@]}"; do
            if ! kill -0 "$pid" 2>/dev/null; then
                local job_info="${DOWNLOAD_PIDS[$pid]}"
                local dataset=$(echo "$job_info" | cut -d: -f1)
                local filename=$(echo "$job_info" | cut -d: -f2)
                
                wait "$pid"
                local exit_code=$?
                
                if [ $exit_code -eq 0 ]; then
                    finish_job "$dataset" "$pid" "true"
                    set_file_status "$dataset" "$filename" "completed"
                    log_success "$dataset/$filename 下载完成"
                else
                    finish_job "$dataset" "$pid" "false"
                    set_file_status "$dataset" "$filename" "failed"
                    log_error "$dataset/$filename 下载失败"
                fi
                
                unset DOWNLOAD_PIDS["$pid"]
            fi
        done
        
        show_live_status
    done
}

# 下载单个文件（支持重试）
download_file_with_retry() {
    local obs_path="$1"
    local local_filename="$2"
    local dataset="$3"
    local expected_size="$4"
    
    local attempt=1
    
    while [ $attempt -le $RETRY_ATTEMPTS ]; do
        log_debug "下载 $local_filename (尝试 $attempt/$RETRY_ATTEMPTS)"
        
        set_file_status "$dataset" "$local_filename" "downloading"
        
        if di-mc cp "$obs_path" "$local_filename" >> "${LOG_FILE}" 2>&1; then
            # 检查文件完整性
            if [ "$expected_size" != "0" ]; then
                local integrity=$(check_file_integrity "$local_filename" "$expected_size")
                if [ "$integrity" = "complete" ]; then
                    return 0
                else
                    log_warning "$local_filename 下载不完整，重试中..."
                    rm -f "$local_filename"
                fi
            else
                return 0
            fi
        else
            log_warning "$local_filename 下载失败，重试中..."
        fi
        
        if [ $attempt -lt $RETRY_ATTEMPTS ]; then
            sleep $RETRY_DELAY
        fi
        
        attempt=$((attempt + 1))
    done
    
    return 1
}

# 并行下载文件列表
download_files_parallel() {
    local dataset="$1"
    local base_path="$2"
    shift 2
    local files=("$@")
    
    local max_parallel_files_for_dataset=$MAX_PARALLEL_FILES
    
    # 根据当前总活跃任务数调整每个数据集的并行数
    if [ $TOTAL_ACTIVE_JOBS -gt 0 ]; then
        local available_slots=$((MAX_TOTAL_JOBS - TOTAL_ACTIVE_JOBS))
        if [ $available_slots -lt $max_parallel_files_for_dataset ]; then
            max_parallel_files_for_dataset=$available_slots
        fi
    fi
    
    if [ $max_parallel_files_for_dataset -le 0 ]; then
        max_parallel_files_for_dataset=1
    fi
    
    log_info "开始并行下载 $dataset (最大并行: $max_parallel_files_for_dataset)"
    
    for file_info in "${files[@]}"; do
        # 等待可用槽位
        wait_for_slot $MAX_TOTAL_JOBS
        
        # 检查数据集级别的并行限制
        while [ "${DATASET_JOBS[$dataset]:-0}" -ge "$max_parallel_files_for_dataset" ]; do
            sleep 1
            show_live_status
        done
        
        # 解析文件信息 (格式: remote_path:local_filename:expected_size)
        local remote_path=$(echo "$file_info" | cut -d: -f1)
        local local_filename=$(echo "$file_info" | cut -d: -f2)
        local expected_size=$(echo "$file_info" | cut -d: -f3)
        
        # 检查是否需要下载
        if [ "$RESUME_MODE" = "true" ] && [ "$FORCE_REDOWNLOAD" != "true" ]; then
            local status=$(get_file_status "$dataset" "$local_filename")
            if [ "$status" = "completed" ]; then
                local integrity=$(check_file_integrity "$local_filename" "$expected_size")
                if [ "$integrity" = "complete" ]; then
                    log_info "$dataset/$local_filename 已存在，跳过"
                    continue
                fi
            fi
        fi
        
        # 启动下载任务
        (
            download_file_with_retry "${base_path}/${remote_path}" "$local_filename" "$dataset" "$expected_size"
        ) &
        
        local pid=$!
        DOWNLOAD_PIDS["$pid"]="$dataset:$local_filename"
        start_job "$dataset" "$pid"
        
        show_live_status
        sleep 0.1  # 避免过快启动任务
    done
    
    # 等待该数据集的所有任务完成
    while [ "${DATASET_JOBS[$dataset]:-0}" -gt 0 ]; do
        sleep 1
        show_live_status
        
        # 清理已完成的任务
        for pid in "${!DOWNLOAD_PIDS[@]}"; do
            local job_info="${DOWNLOAD_PIDS[$pid]}"
            local job_dataset=$(echo "$job_info" | cut -d: -f1)
            
            if [ "$job_dataset" = "$dataset" ] && ! kill -0 "$pid" 2>/dev/null; then
                local filename=$(echo "$job_info" | cut -d: -f2)
                
                wait "$pid"
                local exit_code=$?
                
                if [ $exit_code -eq 0 ]; then
                    finish_job "$dataset" "$pid" "true"
                    set_file_status "$dataset" "$filename" "completed"
                    log_success "$dataset/$filename 下载完成"
                else
                    finish_job "$dataset" "$pid" "false"
                    set_file_status "$dataset" "$filename" "failed"
                    log_error "$dataset/$filename 下载失败"
                fi
                
                unset DOWNLOAD_PIDS["$pid"]
            fi
        done
    done
    
    log_success "$dataset 数据集下载完成"
}

# 下载 Mini 数据集
download_mini_advanced() {
    local dataset="mini"
    local obs_base="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
    
    log_info "开始下载 $dataset 数据集"
    
    # 准备文件列表
    local files=()
    
    # Metadata
    files+=("openscene_metadata_mini.tgz:openscene_metadata_mini.tgz:0")
    
    # Camera files
    for split in {0..31}; do
        files+=("openscene_sensor_mini_camera/openscene_sensor_mini_camera_${split}.tgz:openscene_sensor_mini_camera_${split}.tgz:0")
    done
    
    # Lidar files
    for split in {0..31}; do
        files+=("openscene_sensor_mini_lidar/openscene_sensor_mini_lidar_${split}.tgz:openscene_sensor_mini_lidar_${split}.tgz:0")
    done
    
    # 开始并行下载
    download_files_parallel "$dataset" "$obs_base" "${files[@]}"
    
    # 解压文件
    log_info "开始解压 $dataset 文件..."
    
    if [ -f "openscene_metadata_mini.tgz" ]; then
        tar -xzf openscene_metadata_mini.tgz && rm openscene_metadata_mini.tgz
        mv openscene-v1.1/meta_datas mini_navsim_logs
        rm -rf openscene-v1.1
    fi
    
    # 解压 sensor 文件
    for split in {0..31}; do
        for sensor in camera lidar; do
            local file="openscene_sensor_mini_${sensor}_${split}.tgz"
            if [ -f "$file" ]; then
                tar -xzf "$file" && rm "$file"
            fi
        done
    done
    
    if [ -d "openscene-v1.1/sensor_blobs" ]; then
        mv openscene-v1.1/sensor_blobs mini_sensor_blobs
        rm -rf openscene-v1.1
    fi
    
    log_success "$dataset 数据集处理完成"
}

# 下载 Trainval 数据集  
download_trainval_advanced() {
    local dataset="trainval"
    local obs_base="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
    
    log_info "开始下载 $dataset 数据集"
    
    local files=()
    
    # Metadata
    files+=("openscene_metadata_trainval.tgz:openscene_metadata_trainval.tgz:0")
    
    # Camera files
    for split in {0..199}; do
        files+=("openscene_sensor_trainval_camera/openscene_sensor_trainval_camera_${split}.tgz:openscene_sensor_trainval_camera_${split}.tgz:0")
    done
    
    # Lidar files
    for split in {0..199}; do
        files+=("openscene_sensor_trainval_lidar/openscene_sensor_trainval_lidar_${split}.tgz:openscene_sensor_trainval_lidar_${split}.tgz:0")
    done
    
    download_files_parallel "$dataset" "$obs_base" "${files[@]}"
    
    # 解压处理
    log_info "开始解压 $dataset 文件..."
    
    if [ -f "openscene_metadata_trainval.tgz" ]; then
        tar -xzf openscene_metadata_trainval.tgz && rm openscene_metadata_trainval.tgz
    fi
    
    for split in {0..199}; do
        for sensor in camera lidar; do
            local file="openscene_sensor_trainval_${sensor}_${split}.tgz"
            if [ -f "$file" ]; then
                tar -xzf "$file" && rm "$file"
            fi
        done
    done
    
    if [ -d "openscene-v1.1" ]; then
        mv openscene-v1.1/meta_datas trainval_navsim_logs
        mv openscene-v1.1/sensor_blobs trainval_sensor_blobs
        rm -rf openscene-v1.1
    fi
    
    log_success "$dataset 数据集处理完成"
}

# 下载其他数据集的函数...
download_test_advanced() {
    local dataset="test"
    local obs_base="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
    
    log_info "开始下载 $dataset 数据集"
    
    local files=()
    files+=("openscene_metadata_test.tgz:openscene_metadata_test.tgz:0")
    
    for split in {0..31}; do
        files+=("openscene_sensor_test_camera/openscene_sensor_test_camera_${split}.tgz:openscene_sensor_test_camera_${split}.tgz:0")
        files+=("openscene_sensor_test_lidar/openscene_sensor_test_lidar_${split}.tgz:openscene_sensor_test_lidar_${split}.tgz:0")
    done
    
    download_files_parallel "$dataset" "$obs_base" "${files[@]}"
    
    # 解压处理逻辑...
    log_info "开始解压 $dataset 文件..."
    
    if [ -f "openscene_metadata_test.tgz" ]; then
        tar -xzf openscene_metadata_test.tgz && rm openscene_metadata_test.tgz
    fi
    
    for split in {0..31}; do
        for sensor in camera lidar; do
            local file="openscene_sensor_test_${sensor}_${split}.tgz"
            if [ -f "$file" ]; then
                tar -xzf "$file" && rm "$file"
            fi
        done
    done
    
    if [ -d "openscene-v1.1" ]; then
        mv openscene-v1.1/meta_datas test_navsim_logs  
        mv openscene-v1.1/sensor_blobs test_sensor_blobs
        rm -rf openscene-v1.1
    fi
    
    log_success "$dataset 数据集处理完成"
}

# 简单数据集下载（单文件）
download_simple_dataset() {
    local dataset="$1"
    local obs_base="$2" 
    local filename="$3"
    local extract_cmd="$4"
    
    log_info "开始下载 $dataset 数据集"
    
    local files=("$filename:$filename:0")
    download_files_parallel "$dataset" "$obs_base" "${files[@]}"
    
    if [ -f "$filename" ] && [ -n "$extract_cmd" ]; then
        log_info "解压 $filename..."
        eval "$extract_cmd"
    fi
    
    log_success "$dataset 数据集处理完成"
}

# 主下载函数
download_dataset_advanced() {
    local dataset="$1"
    
    case "$dataset" in
        "maps")
            # Maps 仍然使用原始下载方式
            log_info "下载 nuPlan Maps (使用原始方式)"
            bash download_maps.sh >> "${LOG_FILE}" 2>&1
            ;;
        "mini")
            download_mini_advanced
            ;;
        "trainval") 
            download_trainval_advanced
            ;;
        "test")
            download_test_advanced
            ;;
        "warmup")
            download_simple_dataset "warmup" \
                "training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2" \
                "navsim_v2.2_warmup_two_stage.tar.gz" \
                "tar -xzvf navsim_v2.2_warmup_two_stage.tar.gz && rm navsim_v2.2_warmup_two_stage.tar.gz"
            ;;
        "navhard")
            local dataset="navhard"
            local obs_base="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2"
            
            local files=(
                "navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz:navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz:0"
                "navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz:navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz:0"
                "navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz:navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz:0"
            )
            
            download_files_parallel "$dataset" "$obs_base" "${files[@]}"
            
            # 解压
            for file in navsim_v2.2_navhard_two_stage_*.tar.gz; do
                if [ -f "$file" ]; then
                    tar -xzvf "$file" && rm "$file"
                fi
            done
            ;;
        "private_test")
            # 复合下载：先下载 navsim-v2，再下载 openscene-v1.1
            log_info "下载 Private Test Hard Two Stage 数据集"
            
            # navsim-v2 部分
            download_simple_dataset "private_test_navsim" \
                "training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2" \
                "navsim_v2.2_private_test_hard_two_stage.tar.gz" \
                "tar -xzf navsim_v2.2_private_test_hard_two_stage.tar.gz && rm navsim_v2.2_private_test_hard_two_stage.tar.gz"
            
            # openscene-v1.1 部分
            local obs_base="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
            local files=(
                "openscene_sensor_private_test_hard.tar.gz:openscene_sensor_private_test_hard.tar.gz:0"
                "openscene_metadata_private_test_hard.tar.gz:openscene_metadata_private_test_hard.tar.gz:0"
            )
            
            download_files_parallel "private_test_openscene" "$obs_base" "${files[@]}"
            
            # 解压和整理
            if [ -f "openscene_sensor_private_test_hard.tar.gz" ]; then
                tar -xzf openscene_sensor_private_test_hard.tar.gz && rm openscene_sensor_private_test_hard.tar.gz
                mv openscene-v1.1/sensor_blobs/ private_test_hard_navsim_sensor
                rm -rf openscene-v1.1
            fi
            
            if [ -f "openscene_metadata_private_test_hard.tar.gz" ]; then
                tar -xzf openscene_metadata_private_test_hard.tar.gz && rm openscene_metadata_private_test_hard.tar.gz
                mv openscene-v1.1/meta_datas/ private_test_hard_navsim_log
                rm -rf openscene-v1.1
            fi
            ;;
        *)
            log_error "未知的数据集: $dataset"
            return 1
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
NAVSIM 高级下载脚本

用法: $0 [选项] [数据集...]

选项:
  -h, --help                    显示此帮助信息
  -l, --list                    列出所有可用的数据集
  -a, --all                     下载所有数据集
  -r, --resume                  续点下载模式
  -f, --force                   强制重新下载（忽略已存在文件）
  -q, --quiet                   安静模式（减少输出）
  --no-progress                 禁用进度显示
  --max-datasets N              最大并行数据集数 (默认: $DEFAULT_MAX_PARALLEL_DATASETS)
  --max-files N                 每个数据集最大并行文件数 (默认: $DEFAULT_MAX_PARALLEL_FILES)
  --max-jobs N                  全局最大并行任务数 (默认: $DEFAULT_MAX_TOTAL_JOBS)
  --retry N                     重试次数 (默认: $DEFAULT_RETRY_ATTEMPTS)
  --retry-delay N               重试延迟秒数 (默认: $DEFAULT_RETRY_DELAY)
  --status                      显示下载状态
  --clear-status DATASET        清理指定数据集的状态

可用的数据集:
  maps           nuPlan 地图数据
  mini           OpenScene Mini 数据集
  trainval       OpenScene Trainval 数据集  
  test           OpenScene Test 数据集
  warmup         Warmup Two Stage 数据集
  navhard        NavHard Two Stage 数据集
  private_test   Private Test Hard Two Stage 数据集

示例:
  $0 --all                                    # 下载所有数据集
  $0 mini test --max-jobs 12                  # 下载mini和test，最大12个并行任务
  $0 trainval --resume                        # 续点下载trainval数据集
  $0 --status                                 # 显示当前下载状态
  $0 --clear-status mini                      # 清理mini数据集状态

高级示例:
  $0 trainval --max-datasets 1 --max-files 8 # 只下载trainval，8个文件并行
  $0 --all --quiet --max-jobs 16             # 安静模式下载所有，16个并行任务
EOF
}

# 解析命令行参数
parse_arguments() {
    local datasets=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                echo "可用的数据集: maps mini trainval test warmup navhard private_test"
                exit 0
                ;;
            -a|--all)
                datasets=("maps" "mini" "trainval" "test" "warmup" "navhard" "private_test")
                shift
                ;;
            -r|--resume)
                RESUME_MODE=true
                shift
                ;;
            -f|--force)
                FORCE_REDOWNLOAD=true
                shift
                ;;
            -q|--quiet)
                QUIET_MODE=true
                shift
                ;;
            --no-progress)
                SHOW_PROGRESS=false
                shift
                ;;
            --max-datasets)
                MAX_PARALLEL_DATASETS="$2"
                shift 2
                ;;
            --max-files)
                MAX_PARALLEL_FILES="$2"
                shift 2
                ;;
            --max-jobs)
                MAX_TOTAL_JOBS="$2"
                shift 2
                ;;
            --retry)
                RETRY_ATTEMPTS="$2"
                shift 2
                ;;
            --retry-delay)
                RETRY_DELAY="$2"
                shift 2
                ;;
            --status)
                show_overall_progress
                exit 0
                ;;
            --clear-status)
                clear_dataset_status "$2"
                exit 0
                ;;
            maps|mini|trainval|test|warmup|navhard|private_test)
                datasets+=("$1")
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [ ${#datasets[@]} -eq 0 ]; then
        show_help
        exit 1
    fi
    
    echo "${datasets[@]}"
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    
    # 终止所有下载进程
    for pid in "${!DOWNLOAD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
        fi
    done
    
    # 等待进程结束
    sleep 2
    
    # 强制终止
    for pid in "${!DOWNLOAD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
    done
    
    if [ "$SHOW_PROGRESS" = "true" ]; then
        clear
    fi
    
    log_info "下载已取消"
    exit 1
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    local datasets=($(parse_arguments "$@"))
    
    log_info "NAVSIM 高级下载器启动"
    log_info "配置 - 最大数据集并行: $MAX_PARALLEL_DATASETS, 最大文件并行: $MAX_PARALLEL_FILES, 最大总任务: $MAX_TOTAL_JOBS"
    log_info "重试配置 - 次数: $RETRY_ATTEMPTS, 延迟: ${RETRY_DELAY}秒"
    
    if [ "$RESUME_MODE" = "true" ]; then
        log_info "续点下载模式已启用"
    fi
    
    # 初始化状态文件
    init_status_file
    
    # 开始下载
    local dataset_count=0
    for dataset in "${datasets[@]}"; do
        if [ "$dataset_count" -ge "$MAX_PARALLEL_DATASETS" ]; then
            # 等待一个数据集完成
            while [ "$TOTAL_ACTIVE_JOBS" -gt 0 ]; do
                sleep 1
                show_live_status
            done
            dataset_count=0
        fi
        
        # 启动数据集下载
        (
            download_dataset_advanced "$dataset"
        ) &
        
        dataset_count=$((dataset_count + 1))
        
        # 短暂延迟避免同时启动
        sleep 1
    done
    
    # 等待所有下载完成
    while [ "$TOTAL_ACTIVE_JOBS" -gt 0 ]; do
        sleep 1
        show_live_status
        
        # 清理完成的进程
        for pid in "${!DOWNLOAD_PIDS[@]}"; do
            if ! kill -0 "$pid" 2>/dev/null; then
                local job_info="${DOWNLOAD_PIDS[$pid]}"
                local dataset=$(echo "$job_info" | cut -d: -f1)
                local filename=$(echo "$job_info" | cut -d: -f2)
                
                wait "$pid" 2>/dev/null
                local exit_code=$?
                
                if [ $exit_code -eq 0 ]; then
                    finish_job "$dataset" "$pid" "true"
                    set_file_status "$dataset" "$filename" "completed"
                    log_success "$dataset/$filename 下载完成"
                else
                    finish_job "$dataset" "$pid" "false"
                    set_file_status "$dataset" "$filename" "failed"
                    log_error "$dataset/$filename 下载失败"
                fi
                
                unset DOWNLOAD_PIDS["$pid"]
            fi
        done
    done
    
    # 等待所有数据集处理完成
    wait
    
    if [ "$SHOW_PROGRESS" = "true" ]; then
        clear
    fi
    
    # 显示最终报告
    log_success "所有下载任务完成！"
    show_overall_progress
    
    log_info "详细日志: $LOG_FILE"
    
    if [ "$JOBS_FAILED" -gt 0 ]; then
        log_warning "有 $JOBS_FAILED 个任务失败，请检查日志"
        exit 1
    fi
    
    exit 0
}

# 执行主函数
main "$@" 