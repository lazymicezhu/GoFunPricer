# GoFun 费用计算工具

## 项目简介

GoFun 费用计算工具是一个桌面应用程序，专为 GoFun 共享汽车用户设计，帮助用户在出行前精确规划行程费用。通过输入起点和终点地址，应用程序自动计算行驶距离、时间，并提供多种计费方案的比较，帮助用户选择最经济的方案。

## 功能特点

- **地址智能搜索**：支持地址自动补全功能，方便快速输入
- **地图可视化**：提供地图查看功能，确认起终点位置是否准确
- **多种计费方案**：计算并比较多种计费方式（按日收费、按时收费等）
- **自定义行程参数**：可设置停留时间、是否返程等参数
- **推荐最优方案**：自动计算并推荐最经济的付费方案

## 安装使用

### 环境要求

- Python 3.6+
- PySide6
- requests

### 安装依赖

```bash
pip install PySide6 requests
```

### 运行程序

```bash
python Gofun.py
```

## 使用说明

1. **输入位置信息**

   - 输入城市名称（可选，但有助于提高地址搜索精度）
   - 输入起点地址（支持自动补全）
   - 输入终点地址（支持自动补全）

2. **验证位置**

   - 点击"查看地图"按钮可在地图上确认位置是否准确

3. **获取行程信息**

   - 点击"查询路线"按钮获取距离和时间估算

4. **计算费用**

   - 设置停留时间（默认 30 分钟）
   - 选择是否需要返程
   - 点击"计算费用"按钮

5. **查看费用方案**
   - 程序会显示多种计费方案（按日收费和不同的按时收费套餐）
   - 自动推荐最优方案

## 计费标准说明

程序内置的计费规则包括：

- **按日收费**：38 元车辆使用费 + 50 元保险费
- **按时收费 A**：0.3 元/分钟 + 0.8 元/公里 + 5 元/小时保险费
- **按时收费 B**：5 小时套餐 40 元，超出部分 0.3 元/分钟 + 0.8 元/公里 + 5 元/小时保险费
- **按时收费 C**：3 小时套餐 24 元，超出部分 0.3 元/分钟 + 0.8 元/公里 + 5 元/小时保险费
- **按时收费 D**：6 小时套餐 48 元，超出部分 0.3 元/分钟 + 0.8 元/公里 + 5 元/小时保险费

## 技术实现

- **前端界面**：使用 PySide6（Qt for Python）构建用户界面
- **地图服务**：集成高德地图 API 提供地址搜索、地理编码和路径规划功能
- **自动补全**：实现基于 API 的地址输入提示
- **费用计算**：内置计费规则逻辑，自动计算并比较多种方案

## 开发者信息

本工具基于 Python 和 PySide6 开发，使用高德地图 API 提供地理位置服务。费用计算逻辑基于 GoFun 共享汽车的计费规则（请注意实际费用可能会变动）。

## 注意事项

- 本工具使用高德地图 API，需要联网才能正常使用
- 计算得出的费用仅供参考，实际费用以 GoFun 官方计费为准
- 地址查询准确度取决于输入地址的精确程度和高德地图的数据覆盖
