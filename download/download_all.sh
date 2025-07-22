#!/bin/bash

# NAVSIM 统一下载脚本
# 支持选择性下载和详细的日志记录

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_DIR="./download_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/download_${TIMESTAMP}.log"
SUMMARY_FILE="${LOG_DIR}/download_summary_${TIMESTAMP}.txt"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 初始化日志
echo "==================================" | tee "${LOG_FILE}"
echo "NAVSIM 数据下载开始时间: $(date)" | tee -a "${LOG_FILE}"
echo "==================================" | tee -a "${LOG_FILE}"

# 记录日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"
}

# 下载状态记录
declare -A download_status
declare -A download_times

# 执行下载函数
execute_download() {
    local script_name="$1"
    local description="$2"
    local start_time=$(date +%s)
    
    log_info "开始下载: ${description}"
    log_info "执行脚本: ${script_name}"
    
    if [ ! -f "${script_name}" ]; then
        log_error "脚本文件不存在: ${script_name}"
        download_status["${description}"]="FAILED"
        return 1
    fi
    
    # 执行下载脚本
    if bash "${script_name}" >> "${LOG_FILE}" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        download_times["${description}"]="${duration}"
        download_status["${description}"]="SUCCESS"
        log_success "${description} 下载完成 (耗时: ${duration}秒)"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        download_times["${description}"]="${duration}"
        download_status["${description}"]="FAILED"
        log_error "${description} 下载失败 (耗时: ${duration}秒)"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "NAVSIM 统一下载脚本"
    echo ""
    echo "用法: $0 [选项] [数据集...]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -a, --all      下载所有数据集"
    echo "  -l, --list     列出所有可用的数据集"
    echo ""
    echo "可用的数据集:"
    echo "  maps           nuPlan 地图数据"
    echo "  mini           OpenScene Mini 数据集"
    echo "  trainval       OpenScene Trainval 数据集"
    echo "  test           OpenScene Test 数据集"
    echo "  warmup         Warmup Two Stage 数据集"
    echo "  navhard        NavHard Two Stage 数据集"
    echo "  private_test   Private Test Hard Two Stage 数据集"
    echo ""
    echo "示例:"
    echo "  $0 -a                    # 下载所有数据集"
    echo "  $0 mini test             # 只下载 mini 和 test 数据集"
    echo "  $0 maps mini trainval    # 下载地图和基础训练数据"
}

# 列出可用数据集
list_datasets() {
    echo "可用的数据集:"
    echo "1. maps           - nuPlan 地图数据"
    echo "2. mini           - OpenScene Mini 数据集"
    echo "3. trainval       - OpenScene Trainval 数据集"
    echo "4. test           - OpenScene Test 数据集"
    echo "5. warmup         - Warmup Two Stage 数据集"
    echo "6. navhard        - NavHard Two Stage 数据集"
    echo "7. private_test   - Private Test Hard Two Stage 数据集"
}

# 生成下载报告
generate_report() {
    log_info "生成下载报告..."
    
    echo "==================================" | tee "${SUMMARY_FILE}"
    echo "NAVSIM 数据下载报告" | tee -a "${SUMMARY_FILE}"
    echo "报告生成时间: $(date)" | tee -a "${SUMMARY_FILE}"
    echo "==================================" | tee -a "${SUMMARY_FILE}"
    echo "" | tee -a "${SUMMARY_FILE}"
    
    local total_count=0
    local success_count=0
    local failed_count=0
    
    echo "下载结果详情:" | tee -a "${SUMMARY_FILE}"
    echo "----------------------------------------" | tee -a "${SUMMARY_FILE}"
    
    for dataset in "${!download_status[@]}"; do
        local status="${download_status[$dataset]}"
        local duration="${download_times[$dataset]}"
        total_count=$((total_count + 1))
        
        if [ "${status}" = "SUCCESS" ]; then
            success_count=$((success_count + 1))
            echo -e "${GREEN}✓${NC} ${dataset} - 成功 (${duration}秒)" | tee -a "${SUMMARY_FILE}"
        else
            failed_count=$((failed_count + 1))
            echo -e "${RED}✗${NC} ${dataset} - 失败 (${duration}秒)" | tee -a "${SUMMARY_FILE}"
        fi
    done
    
    echo "" | tee -a "${SUMMARY_FILE}"
    echo "统计信息:" | tee -a "${SUMMARY_FILE}"
    echo "----------------------------------------" | tee -a "${SUMMARY_FILE}"
    echo "总计: ${total_count}" | tee -a "${SUMMARY_FILE}"
    echo -e "${GREEN}成功: ${success_count}${NC}" | tee -a "${SUMMARY_FILE}"
    echo -e "${RED}失败: ${failed_count}${NC}" | tee -a "${SUMMARY_FILE}"
    echo "" | tee -a "${SUMMARY_FILE}"
    
    if [ ${failed_count} -gt 0 ]; then
        echo "失败的下载可以通过以下方式重试:" | tee -a "${SUMMARY_FILE}"
        for dataset in "${!download_status[@]}"; do
            if [ "${download_status[$dataset]}" = "FAILED" ]; then
                echo "- 重新运行对应的单独脚本" | tee -a "${SUMMARY_FILE}"
                echo "- 或者运行: $0 ${dataset}" | tee -a "${SUMMARY_FILE}"
            fi
        done
    fi
    
    echo "" | tee -a "${SUMMARY_FILE}"
    echo "详细日志文件: ${LOG_FILE}" | tee -a "${SUMMARY_FILE}"
    echo "==================================" | tee -a "${SUMMARY_FILE}"
}

# 主下载函数
download_dataset() {
    local dataset="$1"
    
    case "${dataset}" in
        "maps")
            execute_download "download_maps.sh" "nuPlan Maps"
            ;;
        "mini")
            execute_download "download_mini.sh" "OpenScene Mini"
            ;;
        "trainval")
            execute_download "download_trainval.sh" "OpenScene Trainval"
            ;;
        "test")
            execute_download "download_test.sh" "OpenScene Test"
            ;;
        "warmup")
            execute_download "download_warmup_two_stage.sh" "Warmup Two Stage"
            ;;
        "navhard")
            execute_download "download_navhard_two_stage.sh" "NavHard Two Stage"
            ;;
        "private_test")
            execute_download "download_private_test_hard_two_stage.sh" "Private Test Hard Two Stage"
            ;;
        *)
            log_error "未知的数据集: ${dataset}"
            return 1
            ;;
    esac
}

# 解析命令行参数
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# 所有可用的数据集
ALL_DATASETS=("maps" "mini" "trainval" "test" "warmup" "navhard" "private_test")

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -l|--list)
            list_datasets
            exit 0
            ;;
        -a|--all)
            log_info "开始下载所有数据集..."
            for dataset in "${ALL_DATASETS[@]}"; do
                download_dataset "${dataset}"
            done
            shift
            ;;
        *)
            # 检查是否是有效的数据集名称
            if [[ " ${ALL_DATASETS[*]} " =~ " $1 " ]]; then
                download_dataset "$1"
            else
                log_error "未知的数据集: $1"
                log_info "使用 '$0 --list' 查看所有可用的数据集"
                exit 1
            fi
            shift
            ;;
    esac
done

# 生成最终报告
generate_report

log_info "下载完成！"
log_info "查看详细日志: ${LOG_FILE}"
log_info "查看下载报告: ${SUMMARY_FILE}"

# 如果有失败的下载，以非零状态退出
if [ ${#download_status[@]} -gt 0 ]; then
    for status in "${download_status[@]}"; do
        if [ "${status}" = "FAILED" ]; then
            exit 1
        fi
    done
fi

exit 0 