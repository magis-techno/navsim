# NAVSIM 智能下载器 - 快速上手

## 🚀 一键运行（推荐）

```bash
cd download
python run_smart_download.py
```

这个脚本会自动：
1. ✅ 检查Python版本
2. 📦 安装所需依赖
3. ⚙️ 生成下载配置（基于你的完成状态）
4. 🚀 开始智能下载
5. 📁 自动解压和整理文件

## 📋 手动运行

如果需要更多控制，可以分步执行：

### 1. 安装依赖
```bash
pip install -r requirements_downloader.txt
```

### 2. 生成配置
```bash
python smart_downloader.py --generate-config
```

### 3. 查看配置（可选）
```bash
# 查看生成的配置文件
cat smart_download_config_complete.yaml
```

### 4. 开始下载
```bash
python smart_downloader.py
```

## 🎯 根据你的当前状态

基于你提供的下载状态，智能下载器将会：

### ✅ 跳过已完成（节约时间）
- Maps（全部完成）
- Warmup Two Stage（全部完成）  
- Mini Dataset：metadata + camera_1-6
- TrainVal Dataset：camera_0,1
- Test Dataset：metadata + camera_0,1,4
- NavHard：curr_sensors
- Private Test：metadata + sensor

### 🔄 自动下载剩余文件
- **Mini**：camera_0,7-31 + 全部lidar_0-31（~26个文件）
- **TrainVal**：metadata + camera_2-199 + 全部lidar_0-199（~398个文件）
- **Test**：camera_2,3,5-31 + 全部lidar_0-31（~59个文件）
- **NavHard**：hist_sensors + scene_pickles（2个文件）
- **Private Test**：主文件（1个文件）

## 📊 预计下载量

- **总文件数**：~486个文件
- **预估大小**：~240GB
- **优先级**：TrainVal > Mini/Test > NavHard > Private Test

## 🛠️ 特色功能

- 🔄 **断点续传**：网络断开自动恢复
- ⚡ **并发下载**：同时下载3个文件（可配置）
- 🔁 **智能重试**：自动重试失败的下载
- 📈 **实时进度**：显示下载进度和速度
- 💾 **状态保存**：中断后可继续
- 🎯 **优先级**：重要文件优先下载

## 🔧 常见问题

### Q: 遇到403错误怎么办？
A: 编辑配置文件，降低并发数：
```yaml
global_settings:
  max_concurrent: 1  # 改为1
  retry_delay_base: 5  # 增加延迟
```

### Q: 如何暂停下载？
A: 按 `Ctrl+C`，下次运行会自动继续

### Q: 如何查看下载进度？
A: 查看日志文件：
```bash
tail -f downloads/download.log
```

### Q: 下载的文件在哪里？
A: 所有文件在 `./downloads/` 目录

## 📞 获取帮助

如果遇到问题：
1. 查看 `downloads/download.log` 日志
2. 检查网络连接
3. 确认磁盘空间充足
4. 参考 `README_smart_downloader.md` 详细文档

## 🎉 开始下载

现在你可以开始下载了！

```bash
# 一键运行
python run_smart_download.py

# 或分步运行
python smart_downloader.py --generate-config
python smart_downloader.py
```

祝下载顺利！ 🚀 