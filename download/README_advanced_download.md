# NAVSIM 高级下载器

高级下载脚本提供了续点下载、并行下载和进度监控等功能，大幅提升下载效率。

## 🚀 主要特性

### ✅ 续点下载（断点续传）
- 自动检测已下载的文件
- 支持中断后继续下载
- 文件完整性验证

### ⚡ 并行下载
- **多级并行**：数据集级 + 文件级并行
- **智能调度**：自动管理并发任务
- **可配置**：灵活调整并行参数

### 📊 实时监控
- 彩色进度显示
- 实时状态更新
- 详细日志记录

### 🔄 智能重试
- 自动重试失败的下载
- 可配置重试次数和延迟

## 📋 快速开始

### 基本用法

```bash
# 下载所有数据集（推荐）
./download_all_advanced.sh --all

# 下载特定数据集
./download_all_advanced.sh mini test

# 续点下载（推荐用于中断后恢复）
./download_all_advanced.sh trainval --resume
```

### 高性能下载

```bash
# 高并发下载（16个并行任务）
./download_all_advanced.sh --all --max-jobs 16

# 专注单个大数据集，最大化文件并行
./download_all_advanced.sh trainval --max-datasets 1 --max-files 12

# 批量下载，控制数据集并行数
./download_all_advanced.sh mini trainval test --max-datasets 2 --max-files 6
```

### 状态管理

```bash
# 查看当前下载状态
./download_all_advanced.sh --status

# 清理特定数据集状态（重新开始）
./download_all_advanced.sh --clear-status trainval

# 强制重新下载（忽略已存在文件）
./download_all_advanced.sh mini --force
```

## 🛠️ 配置选项

### 并行控制

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `--max-datasets N` | 2 | 最大并行数据集数 |
| `--max-files N` | 4 | 每个数据集最大并行文件数 |
| `--max-jobs N` | 8 | 全局最大并行任务数 |

### 重试配置

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `--retry N` | 3 | 下载失败重试次数 |
| `--retry-delay N` | 5 | 重试间隔（秒） |

### 运行模式

| 参数 | 说明 |
|------|------|
| `--resume` | 续点下载模式 |
| `--force` | 强制重新下载 |
| `--quiet` | 安静模式（减少输出） |
| `--no-progress` | 禁用进度显示 |

## 📚 数据集列表

| 名称 | 说明 | 大小 | 文件数 |
|------|------|------|-------|
| `maps` | nuPlan 地图数据 | ~2GB | 1 |
| `mini` | OpenScene Mini 数据集 | ~15GB | 65 |
| `trainval` | OpenScene Trainval 数据集 | ~500GB | 401 |
| `test` | OpenScene Test 数据集 | ~100GB | 65 |
| `warmup` | Warmup Two Stage 数据集 | ~10GB | 1 |
| `navhard` | NavHard Two Stage 数据集 | ~50GB | 3 |
| `private_test` | Private Test Hard Two Stage | ~20GB | 3 |

## 💡 使用建议

### 推荐配置

**小数据集（mini, test, warmup）**：
```bash
./download_all_advanced.sh mini test warmup --max-jobs 12
```

**大数据集（trainval）**：
```bash
./download_all_advanced.sh trainval --max-datasets 1 --max-files 8 --resume
```

**全量下载**：
```bash
./download_all_advanced.sh --all --max-jobs 16 --resume
```

### 网络环境适配

**高速网络（内网）**：
```bash
--max-jobs 16 --max-files 8
```

**一般网络**：
```bash
--max-jobs 8 --max-files 4  # 默认配置
```

**不稳定网络**：
```bash
--max-jobs 4 --max-files 2 --retry 5 --retry-delay 10
```

## 📁 文件结构

下载后的目录结构：
```
download/
├── download_logs/              # 日志目录
│   ├── advanced_download_*.log # 详细日志
│   └── advanced_summary_*.txt  # 下载报告
├── .download_status.json       # 状态记录文件
├── mini_navsim_logs/           # Mini 数据集日志
├── mini_sensor_blobs/          # Mini 传感器数据
├── trainval_navsim_logs/       # Trainval 日志
├── trainval_sensor_blobs/      # Trainval 传感器数据
└── ...
```

## 🔧 状态管理器

状态管理器可以独立使用：

```bash
# 查看进度
./download_status_manager.sh show_progress

# 检查文件状态
./download_status_manager.sh get_status mini openscene_metadata_mini.tgz

# 设置文件状态
./download_status_manager.sh set_status mini file.tgz completed 1024

# 获取未完成文件
./download_status_manager.sh get_incomplete trainval
```

## ⚠️ 注意事项

1. **磁盘空间**：确保有足够的磁盘空间（trainval ~500GB）
2. **网络稳定**：建议在稳定的网络环境下使用
3. **系统要求**：需要 `jq` 命令（JSON 处理）
4. **权限**：确保脚本有执行权限
5. **中断恢复**：使用 `--resume` 从中断点继续

## 🐛 故障排除

### 常见问题

**下载卡住**：
```bash
# 重启下载，使用更保守的并行设置
./download_all_advanced.sh dataset --resume --max-jobs 4
```

**文件损坏**：
```bash
# 强制重新下载
./download_all_advanced.sh dataset --force
```

**状态异常**：
```bash
# 清理状态重新开始
./download_all_advanced.sh --clear-status dataset
```

### 日志分析

- **详细日志**：`download_logs/advanced_download_*.log`
- **下载报告**：`download_logs/advanced_summary_*.txt`
- **错误信息**：搜索日志中的 `[ERROR]` 标记

## 📞 技术支持

如遇问题，请检查：
1. 日志文件中的错误信息
2. 网络连接状态
3. 磁盘空间是否充足
4. di-mc 工具是否正常工作

---

**享受高效的数据下载体验！** 🎉 