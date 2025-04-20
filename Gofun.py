import sys
import requests
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QMessageBox, QFrame, QCompleter, QDialog,
                           QSpinBox, QCheckBox, QTextBrowser)
from PySide6.QtCore import Qt, QTimer, QStringListModel
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap
from io import BytesIO

class AddressInput(QLineEdit):
    def __init__(self, geocoder, city_input, parent=None):
        super().__init__(parent)
        self.geocoder = geocoder
        self.city_input = city_input
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(self.completer)
        
        # 创建定时器用于延迟发送请求
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.get_suggestions)
        
        # 连接文本变化信号
        self.textChanged.connect(self.on_text_changed)
        
    def on_text_changed(self, text):
        # 重置定时器
        self.timer.stop()
        if text:
            # 300毫秒后发送请求
            self.timer.start(300)
            
    def get_suggestions(self):
        """获取输入提示"""
        text = self.text().strip()
        if not text:
            return
            
        try:
            # 构建请求参数
            params = {
                'key': self.geocoder.api_key,
                'keywords': text,
                'city': self.city_input.text().strip(),
                'output': 'JSON',
                'citylimit': 'true'  # 限制在当前城市
            }
            
            # 发送请求
            url = 'https://restapi.amap.com/v3/assistant/inputtips'
            response = requests.get(url, params=params)
            result = response.json()
            
            if result['status'] == '1':
                # 提取提示信息
                suggestions = []
                for tip in result['tips']:
                    if 'district' in tip and 'address' in tip:
                        suggestions.append(f"{tip['name']} ({tip['district']})")
                    else:
                        suggestions.append(tip['name'])
                
                # 更新补全器的数据
                model = QStringListModel(suggestions)
                self.completer.setModel(model)
                
        except Exception as e:
            print(f"获取输入提示失败: {str(e)}")

class MapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("地图查看")
        self.setMinimumSize(600, 400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建标签用于显示地图
        self.map_label = QLabel()
        self.map_label.setMinimumSize(580, 380)
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setStyleSheet("""
            QLabel {
                border: 1px solid #dcdfe6;
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.map_label)
        
        # 设置窗口位置
        self.center_dialog()
        
    def center_dialog(self):
        parent_geometry = self.parent().geometry()
        x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def load_map(self, lon, lat, address):
        """加载静态地图"""
        try:
            # 构建静态地图URL
            params = {
                'key': '06e9284b7df8259f07d422995aa76685',
                'location': f"{lon},{lat}",
                'zoom': 14,
                'size': '580*380',
                'scale': 2,  # 使用2倍图以获得更清晰的显示
                'markers': f"large,0xFF0000,A:{lon},{lat}",
                'traffic': 1  # 显示路况信息
            }
            
            url = 'https://restapi.amap.com/v3/staticmap'
            print(f"请求地图URL: {url}")
            print(f"参数: {params}")
            
            response = requests.get(url, params=params)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                pixmap = QPixmap()
                load_success = pixmap.loadFromData(image_data.getvalue())
                print(f"图片加载状态: {'成功' if load_success else '失败'}")
                
                if load_success:
                    # 设置地图图片
                    scaled_pixmap = pixmap.scaled(
                        self.map_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.map_label.setPixmap(scaled_pixmap)
                else:
                    QMessageBox.warning(self, "错误", "无法解析地图图片数据")
                    print("图片数据长度:", len(response.content))
            else:
                error_msg = f"地图加载失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f"\n{error_data.get('info', '未知错误')}"
                except:
                    pass
                QMessageBox.warning(self, "错误", error_msg)
                print(f"错误响应: {response.text}")
        except Exception as e:
            error_msg = f"加载地图失败: {str(e)}"
            QMessageBox.warning(self, "错误", error_msg)
            print(f"异常详情: {str(e)}")
            import traceback
            print(f"堆栈跟踪:\n{traceback.format_exc()}")

class FeeCalculatorDialog(QDialog):
    def __init__(self, distance, duration, parent=None):
        super().__init__(parent)
        self.setWindowTitle("费用计算")
        self.setMinimumWidth(500)
        
        self.distance = distance  # 单位：公里
        self.duration = duration  # 单位：分钟
        
        layout = QVBoxLayout(self)
        
        # 停留时间输入
        stay_layout = QHBoxLayout()
        stay_label = QLabel("停留时间(分钟):")
        self.stay_input = QSpinBox()
        self.stay_input.setRange(0, 1440)  # 最多24小时
        self.stay_input.setValue(30)  # 默认30分钟
        stay_layout.addWidget(stay_label)
        stay_layout.addWidget(self.stay_input)
        layout.addLayout(stay_layout)
        
        # 是否返程
        return_layout = QHBoxLayout()
        self.return_check = QCheckBox("需要返程")
        self.return_check.setChecked(True)  # 默认需要返程
        return_layout.addWidget(self.return_check)
        layout.addLayout(return_layout)
        
        # 计算按钮
        calc_button = QPushButton("计算费用")
        calc_button.clicked.connect(self.calculate_fees)
        layout.addWidget(calc_button)
        
        # 结果显示
        self.result_browser = QTextBrowser()
        self.result_browser.setMinimumHeight(300)
        layout.addWidget(self.result_browser)
        
    def calculate_fees(self):
        stay_time = self.stay_input.value()
        need_return = self.return_check.isChecked()
        
        # 计算总距离和时间
        total_distance = self.distance * 2 if need_return else self.distance
        total_duration = (self.duration * 2 + stay_time) if need_return else (self.duration + stay_time)
        total_hours = (total_duration + 59) // 60  # 向上取整小时数
        
        result = []
        result.append(f"行程信息：")
        result.append(f"- 单程距离：{self.distance:.1f}公里")
        result.append(f"- 单程时间：{self.duration}分钟")
        result.append(f"- 停留时间：{stay_time}分钟")
        result.append(f"- 是否返程：{'是' if need_return else '否'}")
        result.append(f"- 总距离：{total_distance:.1f}公里")
        result.append(f"- 总时间：{total_duration}分钟 ({total_hours}小时)")
        result.append("\n费用方案：")
        
        # 按日收费
        daily_fee = 38 + 50  # 车辆使用费 + 保险费
        result.append(f"\n1. 按日收费：")
        result.append(f"   总计：{daily_fee}元")
        result.append(f"   - 车辆使用费：38元")
        result.append(f"   - 保险费：50元")
        
        # 按时收费A
        usage_fee_a = 0.3 * total_duration  # 每分钟0.3元
        distance_fee_a = 0.8 * total_distance  # 每公里0.8元
        insurance_fee_a = 5 * total_hours  # 每小时5元
        total_fee_a = usage_fee_a + distance_fee_a + insurance_fee_a
        result.append(f"\n2. 按时收费A：")
        result.append(f"   总计：{total_fee_a:.1f}元")
        result.append(f"   - 时间费用：{usage_fee_a:.1f}元 (0.3元/分钟)")
        result.append(f"   - 里程费用：{distance_fee_a:.1f}元 (0.8元/公里)")
        result.append(f"   - 保险费用：{insurance_fee_a}元 (5元/小时)")
        
        # 按时收费B（5小时套餐）
        base_hours_b = 5
        base_fee_b = 40
        extra_time_b = max(0, total_duration - base_hours_b * 60)
        usage_fee_b = base_fee_b + (0.3 * extra_time_b if extra_time_b > 0 else 0)
        distance_fee_b = 0.8 * total_distance
        insurance_fee_b = 5 * total_hours
        total_fee_b = usage_fee_b + distance_fee_b + insurance_fee_b
        result.append(f"\n3. 按时收费B（5小时套餐）：")
        result.append(f"   总计：{total_fee_b:.1f}元")
        result.append(f"   - 时间费用：{usage_fee_b:.1f}元 (基础40元，超出部分0.3元/分钟)")
        result.append(f"   - 里程费用：{distance_fee_b:.1f}元 (0.8元/公里)")
        result.append(f"   - 保险费用：{insurance_fee_b}元 (5元/小时)")
        
        # 按时收费C（3小时套餐）
        base_hours_c = 3
        base_fee_c = 24
        extra_time_c = max(0, total_duration - base_hours_c * 60)
        usage_fee_c = base_fee_c + (0.3 * extra_time_c if extra_time_c > 0 else 0)
        distance_fee_c = 0.8 * total_distance
        insurance_fee_c = 5 * total_hours
        total_fee_c = usage_fee_c + distance_fee_c + insurance_fee_c
        result.append(f"\n4. 按时收费C（3小时套餐）：")
        result.append(f"   总计：{total_fee_c:.1f}元")
        result.append(f"   - 时间费用：{usage_fee_c:.1f}元 (基础24元，超出部分0.3元/分钟)")
        result.append(f"   - 里程费用：{distance_fee_c:.1f}元 (0.8元/公里)")
        result.append(f"   - 保险费用：{insurance_fee_c}元 (5元/小时)")
        
        # 按时收费D（6小时套餐）
        base_hours_d = 6
        base_fee_d = 48
        extra_time_d = max(0, total_duration - base_hours_d * 60)
        usage_fee_d = base_fee_d + (0.3 * extra_time_d if extra_time_d > 0 else 0)
        distance_fee_d = 0.8 * total_distance
        insurance_fee_d = 5 * total_hours
        total_fee_d = usage_fee_d + distance_fee_d + insurance_fee_d
        result.append(f"\n5. 按时收费D（6小时套餐）：")
        result.append(f"   总计：{total_fee_d:.1f}元")
        result.append(f"   - 时间费用：{usage_fee_d:.1f}元 (基础48元，超出部分0.3元/分钟)")
        result.append(f"   - 里程费用：{distance_fee_d:.1f}元 (0.8元/公里)")
        result.append(f"   - 保险费用：{insurance_fee_d}元 (5元/小时)")
        
        # 找出最优方案
        fees = {
            "按日收费": daily_fee,
            "按时收费A": total_fee_a,
            "按时收费B(5小时套餐)": total_fee_b,
            "按时收费C(3小时套餐)": total_fee_c,
            "按时收费D(6小时套餐)": total_fee_d
        }
        best_plan = min(fees.items(), key=lambda x: x[1])
        
        result.append(f"\n推荐方案：")
        result.append(f"→ {best_plan[0]}（{best_plan[1]:.1f}元）")
        
        self.result_browser.setText("\n".join(result))

class GeoEncoder:
    def __init__(self, api_key="06e9284b7df8259f07d422995aa76685"):
        """初始化地理编码器"""
        self.api_key = api_key
        self.geo_url = "https://restapi.amap.com/v3/geocode/geo"
        self.direction_url = "https://restapi.amap.com/v3/direction/driving"

    def address_to_location(self, address, city=""):
        """将地址转换为经纬度"""
        params = {
            'key': self.api_key,
            'address': address,
            'city': city,
            'output': 'JSON'
        }
        
        try:
            response = requests.get(self.geo_url, params=params)
            result = response.json()
            
            if result['status'] == '1' and result['count'] != '0':
                location = result['geocodes'][0]['location'].split(',')
                return float(location[0]), float(location[1])
            else:
                QMessageBox.warning(None, "提示", f"地理编码失败: {result.get('info', '未知错误')}")
                return None
        except Exception as e:
            QMessageBox.warning(None, "错误", f"请求发生错误: {str(e)}")
            return None

    def get_driving_route(self, origin, destination):
        """获取驾车路线规划信息"""
        params = {
            'key': self.api_key,
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'extensions': 'base'
        }
        
        try:
            response = requests.get(self.direction_url, params=params)
            result = response.json()
            
            if result['status'] == '1' and 'route' in result:
                path = result['route']['paths'][0]
                distance = float(path['distance']) / 1000  # 转换为公里
                duration = int(path['duration']) // 60  # 转换为分钟
                return distance, duration
            else:
                QMessageBox.warning(None, "提示", f"路线规划失败: {result.get('info', '未知错误')}")
                return None
        except Exception as e:
            QMessageBox.warning(None, "错误", f"请求发生错误: {str(e)}")
            return None

    def open_in_map(self, address, city=""):
        """在地图中打开地址"""
        location = self.address_to_location(address, city)
        if location:
            lon, lat = location
            url = f"https://uri.amap.com/marker?position={lon},{lat}&name={address}"
            webbrowser.open(url)

    def show_in_map(self, address, city=""):
        """在地图中显示地址"""
        location = self.address_to_location(address, city)
        return location

class GeocoderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('GoFun费用计算工具')
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
                min-height: 18px;
            }
            QLineEdit:focus {
                border-color: #409eff;
            }
            QPushButton {
                background-color: #409eff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QFrame {
                background-color: white;
                border-radius: 4px;
            }
            QTextBrowser {
                border: none;
                background-color: transparent;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        # 创建地理编码器实例
        self.geocoder = GeoEncoder()
        
        # 创建主窗口部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题标签
        title_label = QLabel('GoFun费用计算工具')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #303133; margin-bottom: 12px;")
        main_layout.addWidget(title_label)
        
        # 创建说明内容
        instructions_text = QLabel()
        instructions_text.setStyleSheet("""
            QLabel {
                background-color: #f5f7fa;
                border-left: 2px solid #409eff;
                padding: 8px;
                margin-bottom: 8px;
                color: #606266;
                font-size: 12px;
            }
        """)
        
        instructions = """
        <div style='line-height: 1.4;'>
        <p style='margin: 0 0 4px 0; color: #409eff; font-size: 12px;'>使用说明：</p>
        <ol style='margin: 0 0 0 -25px;'>
            <li>输入起点和终点地址</li>
            <li>可选择输入城市名称</li>
            <li>点击"查看地图"可查看位置是否准确</li>
            <li>点击"查询路线"获取费用</li>
        </ol>
        </div>
        """
        instructions_text.setText(instructions)
        main_layout.addWidget(instructions_text)
        
        # 创建输入框部分
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(10)
        
        # 城市输入
        city_layout = QHBoxLayout()
        city_label = QLabel('城市:')
        city_label.setFixedWidth(40)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText('请输入城市名称（可选）')
        city_layout.addWidget(city_label)
        city_layout.addWidget(self.city_input)
        input_layout.addLayout(city_layout)
        
        # 起点地址输入
        start_layout = QHBoxLayout()
        start_label = QLabel('起点:')
        start_label.setFixedWidth(40)
        self.start_input = AddressInput(self.geocoder, self.city_input)
        self.start_input.setPlaceholderText('请输入起点地址')
        start_map_btn = QPushButton('查看地图')
        start_map_btn.setFixedWidth(70)
        start_map_btn.clicked.connect(lambda: self.show_address_in_map(self.start_input))
        start_map_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_input)
        start_layout.addWidget(start_map_btn)
        input_layout.addLayout(start_layout)
        
        # 终点地址输入
        end_layout = QHBoxLayout()
        end_label = QLabel('终点:')
        end_label.setFixedWidth(40)
        self.end_input = AddressInput(self.geocoder, self.city_input)
        self.end_input.setPlaceholderText('请输入终点地址')
        end_map_btn = QPushButton('查看地图')
        end_map_btn.setFixedWidth(70)
        end_map_btn.clicked.connect(lambda: self.show_address_in_map(self.end_input))
        end_map_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_input)
        end_layout.addWidget(end_map_btn)
        input_layout.addLayout(end_layout)
        
        main_layout.addWidget(input_frame)
        
        # 查询按钮
        self.search_button = QPushButton('查询路线')
        self.search_button.setFixedHeight(32)
        self.search_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
            }
        """)
        self.search_button.clicked.connect(self.search_location)
        main_layout.addWidget(self.search_button)
        
        # 结果显示部分
        result_frame = QFrame()
        result_layout = QVBoxLayout(result_frame)
        result_layout.setSpacing(8)
        
        # 路线信息显示
        self.route_info = QLabel()
        self.route_info.setWordWrap(True)
        self.route_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.route_info.setStyleSheet("""
            QLabel {
                background-color: #f0f9eb;
                color: #67c23a;
                padding: 12px;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        result_layout.addWidget(self.route_info)
        
        main_layout.addWidget(result_frame)
        
        # 设置回车键触发搜索
        self.start_input.returnPressed.connect(lambda: self.end_input.setFocus())
        self.end_input.returnPressed.connect(self.search_location)
        self.city_input.returnPressed.connect(lambda: self.start_input.setFocus())
        
        # 设置窗口位置
        self.center_window()
        
    def center_window(self):
        # 获取屏幕几何信息
        screen = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        size = self.geometry()
        # 计算居中位置
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        # 移动窗口
        self.move(x, y)
        
    def search_location(self):
        """搜索路线信息"""
        start_address = self.start_input.text().strip()
        end_address = self.end_input.text().strip()
        city = self.city_input.text().strip()
        
        if not start_address or not end_address:
            QMessageBox.warning(self, "提示", "请输入起点和终点地址！")
            return
        
        # 获取起点经纬度
        start_location = self.geocoder.address_to_location(start_address, city)
        if not start_location:
            return
            
        # 获取终点经纬度
        end_location = self.geocoder.address_to_location(end_address, city)
        if not end_location:
            return
            
        # 获取路线规划信息
        route_info = self.geocoder.get_driving_route(start_location, end_location)
        if route_info:
            distance, duration = route_info
            self.route_info.setText(
                f"预计行驶距离：{distance:.1f}公里\n"
                f"预计行驶时间：{duration}分钟"
            )
            
            # 显示费用计算对话框
            dialog = FeeCalculatorDialog(distance, duration, self)
            dialog.exec()

    def show_address_in_map(self, input_field):
        """在地图对话框中显示地址"""
        address = input_field.text().strip()
        city = self.city_input.text().strip()
        if not address:
            QMessageBox.warning(self, "提示", "请先输入地址！")
            return
            
        location = self.geocoder.show_in_map(address, city)
        if location:
            dialog = MapDialog(self)
            dialog.load_map(location[0], location[1], address)
            dialog.exec()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = GeocoderWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
