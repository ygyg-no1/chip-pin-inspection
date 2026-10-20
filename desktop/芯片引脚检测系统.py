import sys
import os
import json
import codecs
import base64
import cv2
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QProgressBar, QMessageBox,
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import (QPixmap, QFont, QColor, QIcon, QPainter, QPen)


# 样式配置
class ProStyle:
    PRIMARY = "#0A4DA2"
    PRIMARY_LIGHT = "#1E88E5"
    PRIMARY_DARK = "#073A7C"
    SUCCESS = "#2E7D32"
    WARNING = "#E65100"
    ERROR = "#C62828"
    INFO = "#0288D1"
    BG_MAIN = "#F5F7FA"
    BG_CARD = "#FFFFFF"
    BG_DARK = "#263238"
    TEXT_MAIN = "#263238"
    TEXT_SECOND = "#546E7A"
    TEXT_LIGHT = "#B0BEC5"
    BORDER = "#CFD8DC"
    RADIUS_LARGE = 12
    RADIUS_SMALL = 6
    SHADOW_CARD = "0 4px 12px rgba(0,0,0,0.05)"
    SHADOW_BTN = "0 2px 8px rgba(10,77,162,0.3)"
    SPACING_LARGE = 20
    SPACING_SMALL = 12
    MARGIN = 25
    FONT_TITLE = "Microsoft YaHei, Arial, sans-serif"
    FONT_CONTENT = "Microsoft YaHei, Arial, sans-serif"
    SIZE_TITLE = 18
    SIZE_SUBTITLE = 14
    SIZE_CONTENT = 12
    SIZE_SMALL = 10  # 其他小字体保持不变


# 自定义组件
class ProCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background-color: {ProStyle.BG_CARD};
            border-radius: {ProStyle.RADIUS_LARGE}px;
            border: 1px solid {ProStyle.BORDER};
            box-shadow: {ProStyle.SHADOW_CARD};
            padding: {ProStyle.SPACING_SMALL}px;
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(ProStyle.SPACING_SMALL)


class ProButton(QPushButton):
    def __init__(self, text, icon_text=None, parent=None):
        super().__init__(text, parent)
        self.icon_text = icon_text
        self._init_style()
        self._add_icon()

    def _init_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 {ProStyle.PRIMARY_LIGHT}, 
                                           stop:1 {ProStyle.PRIMARY});
                color: white;
                border: none;
                border-radius: {ProStyle.RADIUS_SMALL}px;
                height: 40px;
                font-family: {ProStyle.FONT_CONTENT};
                font-size: {ProStyle.SIZE_CONTENT}px;
                padding: 0 20px;
                transition: all 0.2s;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #42A5F5, 
                                           stop:1 {ProStyle.PRIMARY_LIGHT});
                box-shadow: {ProStyle.SHADOW_BTN};
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                transform: translateY(0);
            }}
            QPushButton:disabled {{
                background: {ProStyle.TEXT_LIGHT};
                color: {ProStyle.BG_CARD};
                box-shadow: none;
            }}
        """)
        self.setMinimumWidth(120)

    def _add_icon(self):
        if self.icon_text:
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor(Qt.white))
            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, self.icon_text)
            painter.end()
            self.setIcon(QIcon(pixmap))
            self.setIconSize(pixmap.size())
            self.setStyleSheet(self.styleSheet() + "text-indent: 8px;")

    def set_success_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #4CAF50, 
                                           stop:1 {ProStyle.SUCCESS});
                color: white;
                border: none;
                border-radius: {ProStyle.RADIUS_SMALL}px;
                height: 40px;
                font-family: {ProStyle.FONT_CONTENT};
                font-size: {ProStyle.SIZE_CONTENT}px;
                padding: 0 20px;
                transition: all 0.2s;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #66BB6A, 
                                           stop:1 #4CAF50);
                box-shadow: 0 2px 8px rgba(46,125,50,0.3);
                transform: translateY(-2px);
            }}
            QPushButton:pressed {{
                transform: translateY(0);
            }}
        """)
        if self.icon_text:
            self.setStyleSheet(self.styleSheet() + "text-indent: 8px;")


class ProProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QProgressBar {{
                height: 10px;
                border-radius: 5px;
                background-color: {ProStyle.BG_MAIN};
                border: 1px solid {ProStyle.BORDER};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 {ProStyle.PRIMARY_LIGHT}, 
                                           stop:1 {ProStyle.PRIMARY});
                border-radius: 4px;
            }}
        """)
        self.setValue(0)


class LogTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ProStyle.BG_DARK};
                color: {ProStyle.TEXT_LIGHT};
                border-radius: {ProStyle.RADIUS_SMALL}px;
                border: 1px solid {ProStyle.BORDER};
                padding: 12px;
                font-family: Consolas, Microsoft YaHei;
                font-size: 14px;  /* 日志字体从10px增大到14px */
                line-height: 1.6;
                read-only: true;
            }}
        """)

    def add_log(self, content, log_type="info"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "info": ProStyle.INFO,
            "success": ProStyle.SUCCESS,
            "warning": ProStyle.WARNING,
            "error": ProStyle.ERROR
        }
        type_label = log_type.upper().ljust(7)
        html = f"""
            <span style="color:{ProStyle.TEXT_LIGHT}">[{timestamp}]</span>
            <span style="color:{color_map.get(log_type, ProStyle.INFO)}">[{type_label}]</span>
            <span style="color:{ProStyle.TEXT_LIGHT}">{content}</span><br>
        """
        self.append(html)
        self.moveCursor(self.textCursor().End)


# 业务线程
class AnnotationThread(QThread):
    update_log = pyqtSignal(str, str)
    update_progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, raw_img_dir, json_output_dir, appid, client_id, client_secret):
        super().__init__()
        self.raw_img_dir = raw_img_dir
        self.json_output_dir = json_output_dir
        self.appid = appid
        self.client_id = client_id
        self.client_secret = client_secret

    def run(self):
        try:
            self.update_log.emit("标注模块启动，开始处理原始图像", "info")
            self.update_log.emit(f"原始图像目录：{self.raw_img_dir}", "info")
            self.update_log.emit(f"JSON输出目录：{self.json_output_dir}", "info")

            if not os.path.exists(self.raw_img_dir):
                self.update_log.emit("原始图像目录不存在，无法继续", "error")
                self.finished.emit()
                return
            if not os.path.isdir(self.raw_img_dir):
                self.update_log.emit("原始图像路径不是有效目录", "error")
                self.finished.emit()
                return

            if not os.path.exists(self.json_output_dir):
                os.makedirs(self.json_output_dir)
                self.update_log.emit("JSON输出目录不存在，已自动创建", "success")

            img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            raw_imgs = [f for f in os.listdir(self.raw_img_dir) if f.lower().endswith(img_exts)]
            if not raw_imgs:
                self.update_log.emit("原始图像目录中未发现有效图像文件", "error")
                self.finished.emit()
                return

            existing_jsons = [os.path.splitext(f)[0].lower() for f in os.listdir(self.json_output_dir) if
                              f.lower().endswith('.json')]
            to_annotate = [f for f in raw_imgs if os.path.splitext(f)[0].lower() not in existing_jsons]

            if not to_annotate:
                self.update_log.emit("所有图像已完成标注，无需重复处理", "success")
                self.finished.emit()
                return

            self.update_log.emit(f"发现 {len(raw_imgs)} 个图像，其中 {len(to_annotate)} 个需标注", "info")

            self.update_log.emit("正在获取百度AI接口访问令牌...", "info")
            access_token = self._get_token()
            if not access_token:
                self.update_log.emit("AI令牌获取失败，标注无法继续", "error")
                self.finished.emit()
                return

            success = 0
            fail = 0
            for i, img_name in enumerate(to_annotate):
                img_path = os.path.join(self.raw_img_dir, img_name)
                json_name = f"{os.path.splitext(img_name)[0]}.json"
                json_path = os.path.join(self.json_output_dir, json_name)

                try:
                    with open(img_path, 'rb') as f:
                        img_data = f.read()
                        if not img_data:
                            raise ValueError("图像文件为空")
                        img_base64 = base64.b64encode(img_data).decode('utf-8')

                    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/xinjianit?access_token={access_token}"
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, headers=headers, json={"image": img_base64}, timeout=60)
                    response.raise_for_status()
                    result = response.json()

                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    success += 1
                    self.update_log.emit(f"[{i + 1}/{len(to_annotate)}] {img_name} 标注成功", "success")
                except Exception as e:
                    fail += 1
                    self.update_log.emit(f"[{i + 1}/{len(to_annotate)}] {img_name} 标注失败：{str(e)}", "error")

                self.update_progress.emit(int((i + 1) / len(to_annotate) * 100))

            self.update_log.emit(f"\n标注任务完成 | 成功：{success} 个 | 失败：{fail} 个", "info")
            if success > 0:
                self.update_log.emit(f"JSON文件已保存至：{self.json_output_dir}", "success")
            self.finished.emit()

        except Exception as e:
            self.update_log.emit(f"标注线程异常：{str(e)}", "error")
            self.finished.emit()

    def _get_token(self):
        try:
            url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            self.update_log.emit(f"令牌获取错误：{str(e)}", "error")
            return None


class DetectionThread(QThread):
    update_log = pyqtSignal(str, str)
    update_progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, raw_img_dir, json_dir, output_dir):
        super().__init__()
        self.raw_img_dir = raw_img_dir
        self.json_dir = json_dir
        self.output_dir = output_dir

    def run(self):
        try:
            self.update_log.emit("检测模块启动，开始分析标注数据", "info")
            self.update_log.emit(f"原始图像目录：{self.raw_img_dir}", "info")
            self.update_log.emit(f"JSON标注目录：{self.json_dir}", "info")
            self.update_log.emit(f"检测结果目录：{self.output_dir}", "info")

            for path, name in [(self.raw_img_dir, "原始图像"), (self.json_dir, "JSON标注")]:
                if not os.path.exists(path):
                    self.update_log.emit(f"{name}目录不存在，无法继续", "error")
                    self.finished.emit()
                    return
                if not os.path.isdir(path):
                    self.update_log.emit(f"{name}路径不是有效目录", "error")
                    self.finished.emit()
                    return

            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                self.update_log.emit("检测结果目录不存在，已自动创建", "success")

            json_files = [f for f in os.listdir(self.json_dir) if f.lower().endswith('.json')]
            if not json_files:
                self.update_log.emit("JSON标注目录中未发现有效文件", "error")
                self.finished.emit()
                return

            valid_jsons = []
            img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            for json_file in json_files:
                base_name = os.path.splitext(json_file)[0]
                for ext in img_exts:
                    img_path = os.path.join(self.raw_img_dir, f"{base_name}{ext}")
                    if os.path.exists(img_path):
                        valid_jsons.append(json_file)
                        break
                else:
                    self.update_log.emit(f"JSON文件 {json_file} 无对应原始图像，跳过", "warning")

            if not valid_jsons:
                self.update_log.emit("无有效JSON-图像匹配对，检测无法继续", "error")
                self.finished.emit()
                return

            self.update_log.emit(f"发现 {len(json_files)} 个JSON，其中 {len(valid_jsons)} 个匹配原始图像", "info")

            defect_count = 0
            font = cv2.FONT_HERSHEY_SIMPLEX

            for i, json_file in enumerate(valid_jsons):
                base_name = os.path.splitext(json_file)[0]
                json_path = os.path.join(self.json_dir, json_file)

                img_path = None
                for ext in img_exts:
                    candidate = os.path.join(self.raw_img_dir, f"{base_name}{ext}")
                    if os.path.exists(candidate):
                        img_path = candidate
                        break

                try:
                    with codecs.open(json_path, 'r', 'utf-8-sig') as f:
                        data = json.load(f)
                    pins = data.get("results", [])
                    pin_num = len(pins)
                    missing = 48 - pin_num
                    if missing > 0:
                        defect_count += 1

                    self.update_log.emit(f"[{i + 1}/{len(valid_jsons)}] {json_file} | 引脚数：{pin_num} | 缺失：{missing}",
                                         "info")

                    img = cv2.imread(img_path)
                    if img is None:
                        raise ValueError("图像读取失败，可能损坏")
                    img1 = img.copy()  # 使用与参考代码相同的变量名

                    # 处理引脚位置 - 完全按照参考代码逻辑
                    xy = []
                    for item in pins:
                        # 确保只获取location中的数据，与参考代码一致
                        location = item.get("location", {})
                        if location:  # 只添加有位置信息的引脚
                            xy.append(location)

                    # 完全按照参考代码的排序逻辑
                    xy.sort(key=lambda x: (x['top']))
                    lt1 = []
                    lt2 = []
                    if len(xy) > 0:
                        begin = xy[0]['top']
                        end = xy[-1]['top']
                        for dic in xy:
                            if begin - 20 < dic.get('top', 0) < begin + 20:
                                lt1.append(dic)
                            if end - 20 < dic.get('top', 0) < end + 20:
                                lt2.append(dic)
                        lt1.sort(key=lambda x: (x['left']))
                        lt2.sort(key=lambda x: (x['left']))
                        xy = lt1 + lt2

                    # 引脚编号与标注 - 完全遵循参考代码逻辑
                    m = 0  # 编号计数器，与参考代码一致
                    for i_pin in range(len(pins)):  # 使用与参考代码相同的循环变量名
                        m += 1  # 先递增编号，再处理当前引脚

                        # 检查索引是否有效
                        if i_pin >= len(xy):
                            continue

                        # 获取引脚坐标，与参考代码完全一致
                        x = xy[i_pin]["left"]
                        y = xy[i_pin]["top"]
                        h = xy[i_pin]["height"]
                        w = xy[i_pin]["width"]

                        # 绘制编号和矩形框，与参考代码一致
                        cv2.putText(img1, str(m), (x, y), font, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
                        img1 = cv2.rectangle(img1, (x, y), (x + w, y + h), (255, 255, 0), 1)

                        # 检测缺失引脚 - 完全按照参考代码的逻辑
                        if i_pin < len(pins) - 1 and i_pin + 1 < len(xy):
                            # 跳过过大的差异（可能是上下排引脚的间隔）
                            if abs(x - xy[i_pin + 1]["left"]) > 100:
                                continue

                            # 判断缺失数量
                            if abs(x - xy[i_pin + 1]["left"]) > 30:
                                m += 2  # 缺失2个引脚
                                self.update_log.emit(f"[{base_name}] 检测到缺失第 {m - 1} 和 {m} 个引脚", "warning")
                            elif abs(x - xy[i_pin + 1]["left"]) > 20:
                                m += 1  # 缺失1个引脚
                                self.update_log.emit(f"[{base_name}] 检测到缺失第 {m} 个引脚", "warning")

                    # 保存结果
                    output_path = os.path.join(self.output_dir, f"{base_name}_detected.jpg")
                    cv2.imwrite(output_path, img1)
                    self.update_log.emit(f"[{i + 1}/{len(valid_jsons)}] 检测结果已保存：{os.path.basename(output_path)}",
                                         "success")

                except Exception as e:
                    self.update_log.emit(f"[{i + 1}/{len(valid_jsons)}] {json_file} 处理失败：{str(e)}", "error")

                self.update_progress.emit(int((i + 1) / len(valid_jsons) * 100))

            self.update_log.emit(f"\n检测任务完成 | 总处理：{len(valid_jsons)} 个 | 有缺失：{defect_count} 个", "info")
            self.update_log.emit(f"检测结果已保存至：{self.output_dir}", "success")
            self.finished.emit()

        except Exception as e:
            self.update_log.emit(f"检测线程异常：{str(e)}", "error")
            self.finished.emit()


# 主窗口
class ProChipDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("芯片引脚标注与检测系统 V1.0")
        self.setGeometry(100, 50, 1100, 800)
        self.setWindowIcon(self._create_window_icon())
        self._init_global_style()

        self.annotation_thread = None
        self.detection_thread = None

        # 初始化所有输入框控件（英文命名）
        self.raw_image_dir_edit = QLineEdit()
        self.json_output_dir_edit = QLineEdit()
        self.detection_result_dir_edit = QLineEdit()
        self.appid_input = QLineEdit()
        self.api_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()

        self._init_ui()

    def _init_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {ProStyle.BG_MAIN};
            }}
            QLabel {{
                font-family: {ProStyle.FONT_CONTENT};
            }}
            QLineEdit {{
                font-family: {ProStyle.FONT_CONTENT};
                font-size: {ProStyle.SIZE_CONTENT}px;
                color: {ProStyle.TEXT_MAIN};
                border: 1px solid {ProStyle.BORDER};
                border-radius: {ProStyle.RADIUS_SMALL}px;
                height: 38px;
                padding: 0 12px;
                background-color: {ProStyle.BG_CARD};
            }}
            QLineEdit:focus {{
                border-color: {ProStyle.PRIMARY_LIGHT};
                box-shadow: 0 0 0 2px rgba(30,136,229,0.15);
            }}
            QLineEdit::placeholder {{
                color: {ProStyle.TEXT_LIGHT};
            }}
        """)

    def _init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {ProStyle.BG_MAIN};")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(ProStyle.MARGIN, ProStyle.MARGIN, ProStyle.MARGIN, ProStyle.MARGIN)
        main_layout.setSpacing(ProStyle.SPACING_LARGE)

        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("芯片引脚标注与检测系统")
        title_label.setStyleSheet(f"""
            font-family: {ProStyle.FONT_TITLE};
            font-size: {ProStyle.SIZE_TITLE}px;
            font-weight: bold;
            color: {ProStyle.PRIMARY};
        """)

        status_layout = QVBoxLayout()
        self.status_label = QLabel("状态：就绪")
        self.status_label.setStyleSheet(f"color: {ProStyle.SUCCESS}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setStyleSheet(f"color: {ProStyle.TEXT_SECOND}; font-size: {ProStyle.SIZE_SMALL}px;")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.time_label)
        status_layout.setAlignment(Qt.AlignRight)

        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)

        title_layout.addWidget(title_label)
        title_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        title_layout.addLayout(status_layout)
        main_layout.addLayout(title_layout)

        # 路径配置卡片
        path_card = ProCard()
        path_card.layout.addWidget(self._create_section_title("路径配置"))

        path_form_layout = QVBoxLayout()
        path_form_layout.addLayout(self._create_path_input(
            label="原始图像目录",
            placeholder="选择存放待标注芯片图像的文件夹",
            edit_widget=self.raw_image_dir_edit,
            callback=self._select_raw_img_dir
        ))
        path_form_layout.addLayout(self._create_path_input(
            label="JSON输出目录",
            placeholder="选择存放标注结果的独立文件夹",
            edit_widget=self.json_output_dir_edit,
            callback=self._select_json_dir
        ))
        path_form_layout.addLayout(self._create_path_input(
            label="检测结果目录",
            placeholder="选择存放带标注的检测图像文件夹",
            edit_widget=self.detection_result_dir_edit,
            callback=self._select_output_dir
        ))

        path_card.layout.addLayout(path_form_layout)
        main_layout.addWidget(path_card)

        # API配置卡片
        api_card = ProCard()
        api_card.layout.addWidget(self._create_section_title("百度AI配置（仅标注需填写）"))

        api_form_layout = QHBoxLayout()
        api_form_layout.setSpacing(ProStyle.SPACING_SMALL)

        api_form_layout.addLayout(self._create_input(
            label="App ID",
            placeholder="输入百度AI App ID",
            edit_widget=self.appid_input
        ))
        api_form_layout.addLayout(self._create_input(
            label="API Key",
            placeholder="输入百度AI API Key",
            edit_widget=self.api_key_input
        ))
        api_form_layout.addLayout(self._create_input(
            label="Secret Key",
            placeholder="输入百度AI Secret Key",
            edit_widget=self.secret_key_input
        ))

        api_card.layout.addLayout(api_form_layout)
        main_layout.addWidget(api_card)

        # 操作控制卡片
        control_card = ProCard()
        control_card.layout.addWidget(self._create_section_title("操作控制"))

        control_layout = QHBoxLayout()

        main_btn_layout = QHBoxLayout()
        self.annotate_btn = ProButton("1. 生成标注JSON", "✏️")
        self.annotate_btn.clicked.connect(self._start_annotation)
        main_btn_layout.addWidget(self.annotate_btn)

        self.detect_btn = ProButton("2. 执行检测", "🔍")
        self.detect_btn.clicked.connect(self._start_detection)
        main_btn_layout.addWidget(self.detect_btn)

        aux_btn_layout = QHBoxLayout()
        self.test_btn = ProButton("测试路径", "✅")
        self.test_btn.set_success_style()
        self.test_btn.clicked.connect(self._test_paths)
        aux_btn_layout.addWidget(self.test_btn)

        self.clear_log_btn = ProButton("清空日志", "🗑️")
        self.clear_log_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ProStyle.TEXT_SECOND};
                color: white;
                border: none;
                border-radius: {ProStyle.RADIUS_SMALL}px;
                height: 40px;
                font-size: {ProStyle.SIZE_CONTENT}px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {ProStyle.TEXT_MAIN};
            }}
        """)
        self.clear_log_btn.clicked.connect(self._clear_log)
        aux_btn_layout.addWidget(self.clear_log_btn)

        control_layout.addLayout(main_btn_layout)
        control_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        control_layout.addLayout(aux_btn_layout)

        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("进度：0%")
        self.progress_label.setStyleSheet(f"color: {ProStyle.TEXT_SECOND}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.progress_bar = ProProgressBar()

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)

        control_card.layout.addLayout(control_layout)
        control_card.layout.addLayout(progress_layout)
        main_layout.addWidget(control_card)

        # 日志卡片
        log_card = ProCard()
        log_card.setStyleSheet(f"""
            background-color: {ProStyle.BG_DARK};
            border-radius: {ProStyle.RADIUS_LARGE}px;
            border: 1px solid {ProStyle.BORDER};
            box-shadow: {ProStyle.SHADOW_CARD};
            padding: {ProStyle.SPACING_SMALL}px;
        """)

        log_title = QLabel("运行日志")
        log_title.setStyleSheet(f"""
            font-family: {ProStyle.FONT_TITLE};
            font-size: {ProStyle.SIZE_SUBTITLE}px;
            font-weight: bold;
            color: {ProStyle.BG_CARD};
            margin-bottom: 8px;
        """)
        log_card.layout.addWidget(log_title)

        log_guide_layout = QHBoxLayout()
        guide_labels = [
            ("信息", ProStyle.INFO),
            ("成功", ProStyle.SUCCESS),
            ("警告", ProStyle.WARNING),
            ("错误", ProStyle.ERROR)
        ]
        for text, color in guide_labels:
            label = QLabel(text)
            label.setStyleSheet(f"""
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: {ProStyle.SIZE_SMALL}px;
                margin-right: 10px;
            """)
            log_guide_layout.addWidget(label)
        log_guide_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        log_card.layout.addLayout(log_guide_layout)

        self.log_text = LogTextEdit()
        log_card.layout.addWidget(self.log_text, 1)

        main_layout.addWidget(log_card, 1)

        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(f"""
            background-color: {ProStyle.BG_CARD};
            color: {ProStyle.TEXT_SECOND};
            font-size: {ProStyle.SIZE_SMALL}px;
            border-top: 1px solid {ProStyle.BORDER};
            padding: 4px 20px;
        """)
        self.status_bar.showMessage("© 2024 芯片检测系统 | 版本 V1.0.0")

    def _create_window_icon(self):
        pixmap = QPixmap(64, 64)
        color = QColor(ProStyle.PRIMARY)
        pixmap.fill(color)
        painter = QPainter(pixmap)

        painter.setPen(QColor(Qt.white))
        painter.setBrush(QColor(Qt.white))
        painter.drawRect(16, 20, 32, 24)

        for i in range(8):
            painter.drawRect(16 + i * 4, 16, 2, 4)
            painter.drawRect(16 + i * 4, 44, 2, 4)

        painter.end()
        return QIcon(pixmap)

    def _create_section_title(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-family: {ProStyle.FONT_TITLE};
            font-size: {ProStyle.SIZE_SUBTITLE}px;
            font-weight: bold;
            color: {ProStyle.TEXT_MAIN};
            margin-bottom: {ProStyle.SPACING_SMALL}px;
            padding-bottom: 4px;
            border-bottom: 1px solid {ProStyle.BORDER};
        """)
        return label

    def _create_path_input(self, label, placeholder, edit_widget, callback):
        layout = QHBoxLayout()

        label = QLabel(label)
        label.setStyleSheet(f"color: {ProStyle.TEXT_SECOND}; width: 100px;")

        edit_widget.setPlaceholderText(placeholder)
        edit_widget.setStyleSheet("flex: 1;")

        btn = QPushButton("浏览")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ProStyle.PRIMARY_LIGHT};
                color: white;
                border: none;
                border-radius: {ProStyle.RADIUS_SMALL}px;
                height: 38px;
                width: 80px;
                font-size: {ProStyle.SIZE_CONTENT}px;
            }}
            QPushButton:hover {{
                background-color: {ProStyle.PRIMARY};
            }}
        """)
        btn.clicked.connect(callback)

        layout.addWidget(label)
        layout.addWidget(edit_widget)
        layout.addWidget(btn)
        return layout

    def _create_input(self, label, placeholder, edit_widget):
        layout = QVBoxLayout()

        label = QLabel(label)
        label.setStyleSheet(f"color: {ProStyle.TEXT_SECOND}; margin-bottom: 4px;")

        edit_widget.setPlaceholderText(placeholder)

        layout.addWidget(label)
        layout.addWidget(edit_widget)
        return layout

    def _update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 路径选择回调
    def _select_raw_img_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择原始图像目录")
        if dir_path:
            self.raw_image_dir_edit.setText(os.path.abspath(dir_path))

    def _select_json_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择JSON输出目录")
        if dir_path:
            self.json_output_dir_edit.setText(os.path.abspath(dir_path))

    def _select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择检测结果目录")
        if dir_path:
            self.detection_result_dir_edit.setText(os.path.abspath(dir_path))

    # 业务逻辑
    def _start_annotation(self):
        raw_dir = self.raw_image_dir_edit.text()
        json_dir = self.json_output_dir_edit.text()
        appid = self.appid_input.text()
        api_key = self.api_key_input.text()
        secret_key = self.secret_key_input.text()

        missing = []
        if not raw_dir: missing.append("原始图像目录")
        if not json_dir: missing.append("JSON输出目录")
        if not appid: missing.append("App ID")
        if not api_key: missing.append("API Key")
        if not secret_key: missing.append("Secret Key")

        if missing:
            QMessageBox.warning(self, "参数缺失", f"请完善以下配置：{', '.join(missing)}")
            return

        self.annotate_btn.setEnabled(False)
        self.detect_btn.setEnabled(False)
        self.status_label.setText("状态：标注中...")
        self.status_label.setStyleSheet(f"color: {ProStyle.INFO}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.log_text.add_log("开始标注任务，请勿关闭程序", "info")

        self.annotation_thread = AnnotationThread(raw_dir, json_dir, appid, api_key, secret_key)
        self.annotation_thread.update_log.connect(self.log_text.add_log)
        self.annotation_thread.update_progress.connect(self._update_progress)
        self.annotation_thread.finished.connect(self._annotation_finished)
        self.annotation_thread.start()

    def _start_detection(self):
        raw_dir = self.raw_image_dir_edit.text()
        json_dir = self.json_output_dir_edit.text()
        output_dir = self.detection_result_dir_edit.text()

        missing = []
        if not raw_dir: missing.append("原始图像目录")
        if not json_dir: missing.append("JSON输出目录")
        if not output_dir: missing.append("检测结果目录")

        if missing:
            QMessageBox.warning(self, "参数缺失", f"请完善以下配置：{', '.join(missing)}")
            return

        if not [f for f in os.listdir(json_dir) if f.lower().endswith('.json')]:
            QMessageBox.warning(self, "无标注数据", "JSON输出目录中未发现标注文件，请先执行标注")
            return

        self.annotate_btn.setEnabled(False)
        self.detect_btn.setEnabled(False)
        self.status_label.setText("状态：检测中...")
        self.status_label.setStyleSheet(f"color: {ProStyle.INFO}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.log_text.add_log("开始检测任务，请勿关闭程序", "info")

        self.detection_thread = DetectionThread(raw_dir, json_dir, output_dir)
        self.detection_thread.update_log.connect(self.log_text.add_log)
        self.detection_thread.update_progress.connect(self._update_progress)
        self.detection_thread.finished.connect(self._detection_finished)
        self.detection_thread.start()

    def _test_paths(self):
        self.log_text.add_log("开始路径有效性测试", "info")
        success = True

        raw_dir = self.raw_image_dir_edit.text()
        if not raw_dir:
            self.log_text.add_log("原始图像目录未设置", "error")
            success = False
        elif not os.path.exists(raw_dir):
            self.log_text.add_log(f"原始图像目录不存在：{raw_dir}", "error")
            success = False
        elif not os.path.isdir(raw_dir):
            self.log_text.add_log(f"原始图像路径不是目录：{raw_dir}", "error")
            success = False
        else:
            img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            imgs = [f for f in os.listdir(raw_dir) if f.lower().endswith(img_exts)]
            if not imgs:
                self.log_text.add_log(f"原始图像目录无有效图像：{raw_dir}", "warning")
            else:
                self.log_text.add_log(f"原始图像目录正常，发现 {len(imgs)} 个图像", "success")

        json_dir = self.json_output_dir_edit.text()
        if not json_dir:
            self.log_text.add_log("JSON输出目录未设置", "error")
            success = False
        elif not os.path.exists(json_dir):
            self.log_text.add_log(f"JSON输出目录不存在（将自动创建）：{json_dir}", "warning")
        elif not os.path.isdir(json_dir):
            self.log_text.add_log(f"JSON输出路径不是目录：{json_dir}", "error")
            success = False
        else:
            self.log_text.add_log(f"JSON输出目录正常：{json_dir}", "success")

        output_dir = self.detection_result_dir_edit.text()
        if not output_dir:
            self.log_text.add_log("检测结果目录未设置", "error")
            success = False
        elif not os.path.exists(output_dir):
            self.log_text.add_log(f"检测结果目录不存在（将自动创建）：{output_dir}", "warning")
        elif not os.path.isdir(output_dir):
            self.log_text.add_log(f"检测结果路径不是目录：{output_dir}", "error")
            success = False
        else:
            self.log_text.add_log(f"检测结果目录正常：{output_dir}", "success")

        if not all([self.appid_input.text(), self.api_key_input.text(), self.secret_key_input.text()]):
            self.log_text.add_log("AI配置未完整填写（仅影响标注功能）", "warning")
        else:
            self.log_text.add_log("AI配置已完整填写", "success")

        if success:
            self.log_text.add_log("所有路径测试通过", "success")
            QMessageBox.information(self, "测试成功", "所有路径配置均有效！")
        else:
            self.log_text.add_log("部分路径测试失败，请查看日志", "error")
            QMessageBox.warning(self, "测试失败", "部分路径配置存在问题，请查看日志详情")

    def _clear_log(self):
        self.log_text.clear()
        self.log_text.add_log("日志已清空", "info")

    def _update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"进度：{value}%")

    def _annotation_finished(self):
        self.annotate_btn.setEnabled(True)
        self.detect_btn.setEnabled(True)
        self.status_label.setText("状态：就绪")
        self.status_label.setStyleSheet(f"color: {ProStyle.SUCCESS}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.progress_bar.setValue(0)
        self.progress_label.setText("进度：0%")

    def _detection_finished(self):
        self.annotate_btn.setEnabled(True)
        self.detect_btn.setEnabled(True)
        self.status_label.setText("状态：就绪")
        self.status_label.setStyleSheet(f"color: {ProStyle.SUCCESS}; font-size: {ProStyle.SIZE_SMALL}px;")
        self.progress_bar.setValue(0)
        self.progress_label.setText("进度：0%")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProChipDetectionApp()
    window.show()
    sys.exit(app.exec_())
