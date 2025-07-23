#!/bin/bash

# 下载状态管理器
# 负责状态记录、文件完整性检查、续点功能

STATUS_FILE=".download_status.json"
LOCK_FILE=".download_status.lock"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[STATUS]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[STATUS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[STATUS]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[STATUS]${NC} $1" >&2
}

# 文件锁定机制
acquire_lock() {
    local timeout=30
    local count=0
    
    while [ -f "$LOCK_FILE" ] && [ $count -lt $timeout ]; do
        sleep 1
        ((count++))
    done
    
    if [ $count -ge $timeout ]; then
        log_error "无法获取状态文件锁，超时"
        return 1
    fi
    
    echo $$ > "$LOCK_FILE"
    return 0
}

release_lock() {
    if [ -f "$LOCK_FILE" ]; then
        rm -f "$LOCK_FILE"
    fi
}

# 清理函数
cleanup() {
    release_lock
}
trap cleanup EXIT

# 初始化状态文件
init_status_file() {
    if [ ! -f "$STATUS_FILE" ]; then
        echo '{}' > "$STATUS_FILE"
        log_info "初始化状态文件: $STATUS_FILE"
    fi
}

# 获取文件状态
get_file_status() {
    local dataset="$1"
    local filename="$2"
    
    if [ ! -f "$STATUS_FILE" ]; then
        echo "not_started"
        return
    fi
    
    acquire_lock || return 1
    
    local status=$(jq -r ".\"$dataset\".\"$filename\".status // \"not_started\"" "$STATUS_FILE" 2>/dev/null)
    
    release_lock
    echo "$status"
}

# 设置文件状态
set_file_status() {
    local dataset="$1"
    local filename="$2"
    local status="$3"
    local file_size="${4:-0}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    acquire_lock || return 1
    
    init_status_file
    
    # 使用 jq 更新状态
    local temp_file=$(mktemp)
    jq ".\"$dataset\".\"$filename\" = {
        \"status\": \"$status\",
        \"size\": $file_size,
        \"timestamp\": \"$timestamp\"
    }" "$STATUS_FILE" > "$temp_file" && mv "$temp_file" "$STATUS_FILE"
    
    release_lock
    log_info "设置 $dataset/$filename 状态为: $status"
}

# 检查文件完整性
check_file_integrity() {
    local filepath="$1"
    local expected_size="$2"
    
    if [ ! -f "$filepath" ]; then
        echo "missing"
        return
    fi
    
    local actual_size=$(stat -c%s "$filepath" 2>/dev/null || echo 0)
    
    if [ "$expected_size" != "0" ] && [ "$actual_size" != "$expected_size" ]; then
        echo "incomplete"
        return
    fi
    
    echo "complete"
}

# 获取数据集进度
get_dataset_progress() {
    local dataset="$1"
    
    if [ ! -f "$STATUS_FILE" ]; then
        echo "0 0 0"
        return
    fi
    
    acquire_lock || return 1
    
    local total=$(jq -r ".\"$dataset\" // {} | length" "$STATUS_FILE" 2>/dev/null)
    local completed=$(jq -r ".\"$dataset\" // {} | to_entries | map(select(.value.status == \"completed\")) | length" "$STATUS_FILE" 2>/dev/null)
    local failed=$(jq -r ".\"$dataset\" // {} | to_entries | map(select(.value.status == \"failed\")) | length" "$STATUS_FILE" 2>/dev/null)
    
    release_lock
    echo "$completed $total $failed"
}

# 获取未完成的文件列表
get_incomplete_files() {
    local dataset="$1"
    
    if [ ! -f "$STATUS_FILE" ]; then
        return
    fi
    
    acquire_lock || return 1
    
    jq -r ".\"$dataset\" // {} | to_entries | map(select(.value.status != \"completed\")) | .[].key" "$STATUS_FILE" 2>/dev/null
    
    release_lock
}

# 清理数据集状态
clear_dataset_status() {
    local dataset="$1"
    
    acquire_lock || return 1
    
    if [ -f "$STATUS_FILE" ]; then
        local temp_file=$(mktemp)
        jq "del(.\"$dataset\")" "$STATUS_FILE" > "$temp_file" && mv "$temp_file" "$STATUS_FILE"
        log_info "清理数据集 $dataset 的状态记录"
    fi
    
    release_lock
}

# 显示总体进度
show_overall_progress() {
    echo "==================================="
    echo "总体下载进度"
    echo "==================================="
    
    if [ ! -f "$STATUS_FILE" ]; then
        echo "暂无下载记录"
        return
    fi
    
    acquire_lock || return 1
    
    local datasets=$(jq -r 'keys[]' "$STATUS_FILE" 2>/dev/null)
    
    printf "%-15s %-10s %-10s %-10s\n" "数据集" "已完成" "总计" "进度"
    echo "-----------------------------------"
    
    while IFS= read -r dataset; do
        if [ -n "$dataset" ]; then
            local progress=($(get_dataset_progress "$dataset"))
            local completed=${progress[0]}
            local total=${progress[1]}
            local failed=${progress[2]}
            
            local percentage=0
            if [ "$total" -gt 0 ]; then
                percentage=$((completed * 100 / total))
            fi
            
            local status_color="$GREEN"
            if [ "$failed" -gt 0 ]; then
                status_color="$RED"
            elif [ "$completed" -lt "$total" ]; then
                status_color="$YELLOW"
            fi
            
            printf "${status_color}%-15s %-10s %-10s %-10s${NC}\n" "$dataset" "$completed" "$total" "${percentage}%"
        fi
    done <<< "$datasets"
    
    release_lock
    echo "==================================="
}

# 显示帮助
show_help() {
    echo "下载状态管理器"
    echo ""
    echo "用法: $0 <命令> [参数...]"
    echo ""
    echo "命令:"
    echo "  get_status <dataset> <filename>     获取文件状态"
    echo "  set_status <dataset> <filename> <status> [size]  设置文件状态"
    echo "  check_file <filepath> [expected_size]  检查文件完整性"
    echo "  get_progress <dataset>              获取数据集进度"
    echo "  get_incomplete <dataset>            获取未完成文件列表"
    echo "  clear_dataset <dataset>             清理数据集状态"
    echo "  show_progress                       显示总体进度"
    echo ""
    echo "状态值: not_started, downloading, completed, failed"
}

# 主函数
main() {
    case "$1" in
        "get_status")
            get_file_status "$2" "$3"
            ;;
        "set_status")
            set_file_status "$2" "$3" "$4" "$5"
            ;;
        "check_file")
            check_file_integrity "$2" "$3"
            ;;
        "get_progress")
            get_dataset_progress "$2"
            ;;
        "get_incomplete")
            get_incomplete_files "$2"
            ;;
        "clear_dataset")
            clear_dataset_status "$2"
            ;;
        "show_progress")
            show_overall_progress
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi 