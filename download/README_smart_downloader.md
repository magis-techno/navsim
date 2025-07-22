# NAVSIM 智能下载器

基于HuggingFace Hub API的智能下载器，具备断点续传、并发控制、智能重试等高级功能。

## 🚀 特性

- ✅ **断点续传**：网络中断后自动恢复下载
- ✅ **并发下载**：同时下载多个文件，可配置并发数
- ✅ **智能重试**：指数退避重试机制，避免频率限制
- ✅ **进度监控**：实时显示下载进度和统计信息
- ✅ **文件校验**：自动验证文件大小和完整性
- ✅ **状态持久化**：支持暂停和恢复下载会话
- ✅ **优先级调度**：按优先级下载重要文件

## 📦 安装依赖

```bash
# 安装Python依赖
pip install -r requirements_downloader.txt

# 或手动安装
pip install huggingface_hub tqdm PyYAML requests
```

## 🛠️ 使用方法

### 1. 生成配置文件

```bash
# 根据已完成下载状态生成完整配置
python smart_downloader.py --generate-config

# 或手动运行配置生成器
python generate_download_config.py
```

### 2. 开始下载

```bash
# 使用默认配置
python smart_downloader.py

# 指定配置文件
python smart_downloader.py --config my_config.yaml
```

### 3. 监控进度

下载器会显示：
- 实时进度条
- 当前下载状态
- 成功/失败统计
- 完成时间估算

## 📁 文件结构

```
download/
├── smart_downloader.py              # 主下载器
├── generate_download_config.py      # 配置生成器
├── smart_download_config_complete.yaml  # 完整配置文件
├── downloads/                       # 下载目录
│   ├── download_status.json        # 下载状态
│   ├── download.log                 # 下载日志
│   └── *.tgz                       # 下载的文件
└── README_smart_downloader.md       # 本文档
```

## ⚙️ 配置说明

### 全局设置
```yaml
global_settings:
  max_concurrent: 3          # 最大并发下载数
  max_retries: 5            # 最大重试次数
  retry_delay_base: 2       # 重试延迟基数(秒)
  timeout: 300              # 下载超时(秒)
  verify_size: true         # 验证文件大小
```

### 任务优先级
- **1**: 最高优先级（trainval数据）
- **2**: 中等优先级（mini、test数据）
- **3**: 低优先级（navhard数据）
- **4**: 最低优先级（private test数据）

## 🔧 故障排除

### 常见问题

1. **403 Forbidden 错误**
   - 降低并发数：`max_concurrent: 1`
   - 增加重试延迟：`retry_delay_base: 5`

2. **网络超时**
   - 增加超时时间：`timeout: 600`
   - 检查网络连接

3. **文件大小异常**
   - 检查磁盘空间
   - 手动删除损坏文件重新下载

### 恢复下载

下载器支持自动恢复：
1. 中断下载（Ctrl+C）
2. 重新运行下载器
3. 自动跳过已完成文件
4. 从中断点继续下载

### 日志分析

查看详细日志：
```bash
tail -f downloads/download.log
```

## 📊 状态文件

`downloads/download_status.json` 记录每个文件的下载状态：

```json
{
  "filename.tgz": {
    "status": "completed",
    "completed_time": 1678901234,
    "attempts": 2
  }
}
```

状态类型：
- `downloading`: 正在下载
- `completed`: 下载成功
- `failed`: 下载失败

## 🎯 性能优化建议

1. **网络优化**
   - 使用稳定的网络连接
   - 考虑使用VPN改善连接质量
   - 避免高峰时段下载

2. **系统优化**
   - 确保足够的磁盘空间
   - 关闭不必要的网络应用
   - 设置合适的并发数

3. **配置调优**
   ```yaml
   # 稳定网络配置
   max_concurrent: 3
   max_retries: 3
   retry_delay_base: 2
   
   # 不稳定网络配置
   max_concurrent: 1
   max_retries: 10
   retry_delay_base: 5
   ```

## 🆘 获取帮助

如果遇到问题：
1. 检查 `downloads/download.log` 获取详细错误信息
2. 确认网络连接正常
3. 验证配置文件格式正确
4. 尝试手动下载单个文件测试

## 📈 进度追踪

下载完成后，使用以下命令检查下载状态：

```bash
# 运行状态检查
python check_download_status.py

# 查看下载摘要
python smart_downloader.py --config smart_download_config_complete.yaml
``` 