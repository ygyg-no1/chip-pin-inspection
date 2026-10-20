import os
import json
import cv2
import threading
import urllib.parse
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# 允许前端页面跨域调用（例如直接用 file:// 打开 web/frontend/index.html 时）
try:
    from flask_cors import CORS

    CORS(app)
except ImportError:  # 未安装 flask-cors 时不影响主流程
    pass

# 全局变量：任务队列与进度跟踪
task_queue = threading.Event()  # 任务队列
task_queue = []
task_progress = {}  # 任务进度跟踪
task_info = {}  # 任务详细信息（输出目录等）
processed_count = 0  # 已处理文件总数


class BaseTask:
    """任务基类"""

    def __init__(self, task_id):
        self.task_id = task_id
        self.progress = 0
        self.logs = []
        self.completed = False

    def add_log(self, content, log_type="info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append({
            "timestamp": timestamp,
            "content": content,
            "type": log_type
        })

    def update_progress(self, value):
        """更新进度"""
        self.progress = min(100, max(0, value))
        if self.task_id in task_progress:
            task_progress[self.task_id]["progress"] = self.progress


class AnnotationTask(BaseTask):
    """标注任务类"""

    def __init__(self, task_id, raw_img_dir, json_output_dir, appid, client_id, client_secret):
        super().__init__(task_id)
        self.raw_img_dir = raw_img_dir
        self.json_output_dir = json_output_dir
        self.appid = appid
        self.client_id = client_id
        self.client_secret = client_secret
        self.success_count = 0
        self.fail_count = 0

    def run(self):
        global processed_count
        try:
            self.add_log("标注模块启动，开始处理图像", "info")
            self.add_log(f"原始图像目录：{self.raw_img_dir}", "info")
            self.add_log(f"JSON输出目录：{self.json_output_dir}", "info")
            self.update_progress(5)

            # 验证目录权限与存在性
            try:
                if not os.path.exists(self.raw_img_dir):
                    raise Exception(f"原始图像目录不存在：{self.raw_img_dir}")
                if not os.path.exists(self.json_output_dir):
                    os.makedirs(self.json_output_dir)
                    self.add_log(f"JSON输出目录不存在，已自动创建", "success")
                os.listdir(self.raw_img_dir)
                os.listdir(self.json_output_dir)
            except PermissionError:
                self.add_log("无权限访问目录，请检查文件夹权限", "error")
                self.completed = True
                self.update_progress(100)
                return
            except Exception as e:
                self.add_log(f"目录访问错误：{str(e)}", "error")
                self.completed = True
                self.update_progress(100)
                return

            self.update_progress(15)

            # 筛选图像文件
            img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            img_files = [f for f in os.listdir(self.raw_img_dir)
                         if f.lower().endswith(img_exts)]

            if not img_files:
                self.add_log("原始图像目录中未发现有效图像文件", "error")
                self.completed = True
                self.update_progress(100)
                return

            total = len(img_files)
            self.add_log(f"发现 {total} 个有效图像文件，开始标注", "info")
            self.update_progress(20)

            # 模拟标注过程（实际应用中替换为百度AI接口调用）
            for i, img_file in enumerate(img_files):
                try:
                    img_path = os.path.join(self.raw_img_dir, img_file)
                    base_name = os.path.splitext(img_file)[0]
                    json_path = os.path.join(self.json_output_dir, f"{base_name}.json")

                    # 模拟标注结果（实际应从AI接口获取）
                    annotation_result = {
                        "image_name": img_file,
                        "results": [
                            {"location": {"left": 10 + i, "top": 20 + i, "width": 5, "height": 5}},
                            {"location": {"left": 30 + i, "top": 20 + i, "width": 5, "height": 5}}
                        ]
                    }

                    # 保存标注结果
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(annotation_result, f, ensure_ascii=False, indent=2)

                    self.success_count += 1
                    processed_count += 1
                    self.add_log(f"[{i + 1}/{total}] 标注成功：{img_file}", "success")

                except Exception as e:
                    self.fail_count += 1
                    self.add_log(f"[{i + 1}/{total}] 标注失败 {img_file}：{str(e)}", "error")

                # 更新进度
                progress = 20 + (i + 1) / total * 80
                self.update_progress(int(progress))

            # 更新任务进度信息
            task_progress[self.task_id] = {
                "progress": 100,
                "success": self.success_count,
                "fail": self.fail_count,
                "logs": self.logs,
                "completed": True,
                "processed_count": processed_count
            }

            self.add_log(f"\n标注任务完成 | 总处理：{total} 个 | 成功：{self.success_count} 个 | 失败：{self.fail_count} 个", "info")
            self.add_log(f"标注结果已保存至：{self.json_output_dir}", "success")

        except Exception as e:
            self.add_log(f"标注线程异常：{str(e)}", "error")
        finally:
            self.completed = True
            self.update_progress(100)


class DetectionTask(BaseTask):
    """检测任务类"""

    def __init__(self, task_id, raw_img_dir, json_dir, output_dir):
        super().__init__(task_id)
        self.raw_img_dir = raw_img_dir
        self.json_dir = json_dir
        self.output_dir = output_dir
        self.total = 0
        self.defect_count = 0
        self.defect_details = []

    def run(self):
        global processed_count
        try:
            self.add_log("检测模块启动，开始分析标注数据", "info")
            self.add_log(f"原始图像目录：{self.raw_img_dir}", "info")
            self.add_log(f"JSON标注目录：{self.json_dir}", "info")
            self.add_log(f"检测结果目录：{self.output_dir}", "info")
            self.update_progress(5)

            # 验证输入目录权限
            try:
                os.listdir(self.raw_img_dir)
                os.listdir(self.json_dir)
            except PermissionError:
                self.add_log(f"无权限访问目录，请检查文件夹权限", "error")
                self.completed = True
                self.update_progress(100)
                return
            except Exception as e:
                self.add_log(f"目录访问错误：{str(e)}", "error")
                self.completed = True
                self.update_progress(100)
                return

            # 验证目录存在性
            for path, name in [(self.raw_img_dir, "原始图像"), (self.json_dir, "JSON标注")]:
                if not os.path.exists(path):
                    self.add_log(f"{name}目录不存在，无法继续", "error")
                    self.completed = True
                    self.update_progress(100)
                    return

            # 创建输出目录
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                self.add_log(f"检测结果目录不存在，已自动创建：{self.output_dir}", "success")
            self.update_progress(20)

            # 筛选JSON文件
            json_files = [f for f in os.listdir(self.json_dir) if f.lower().endswith('.json')]
            if not json_files:
                self.add_log("JSON标注目录中未发现有效文件", "error")
                self.completed = True
                self.update_progress(100)
                return

            # 匹配对应的图像文件
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
                    self.add_log(f"JSON文件 {json_file} 无对应原始图像，跳过", "warning")
            self.update_progress(25)

            if not valid_jsons:
                self.add_log("无有效JSON-图像匹配对，检测无法继续", "error")
                self.completed = True
                self.update_progress(100)
                return

            self.total = len(valid_jsons)
            self.add_log(f"发现 {len(json_files)} 个JSON，其中 {self.total} 个匹配原始图像", "info")
            self.update_progress(30)

            # 处理检测逻辑
            defect_count = 0
            font = cv2.FONT_HERSHEY_SIMPLEX
            total = len(valid_jsons)

            for i, json_file in enumerate(valid_jsons):
                base_name = os.path.splitext(json_file)[0]
                json_path = os.path.join(self.json_dir, json_file)

                # 查找对应的图像文件
                img_path = None
                for ext in img_exts:
                    candidate = os.path.join(self.raw_img_dir, f"{base_name}{ext}")
                    if os.path.exists(candidate):
                        img_path = candidate
                        break

                try:
                    # 读取标注数据
                    with open(json_path, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                    pins = data.get("results", [])
                    pin_num = len(pins)
                    missing = 48 - pin_num  # 假设标准引脚数为48

                    # 记录每个芯片的缺失详情
                    self.defect_details.append({
                        "chip_name": base_name,
                        "missing_pins": missing
                    })

                    if missing > 0:
                        defect_count += 1
                        self.add_log(f"[{base_name}] 检测到引脚缺失：{missing} 个", "warning")
                    else:
                        self.add_log(f"[{base_name}] 引脚正常，无缺失", "success")

                    # 读取图像并处理
                    img = cv2.imread(img_path)
                    if img is None:
                        raise ValueError("图像读取失败，可能损坏")
                    img1 = img.copy()

                    # 处理引脚位置
                    xy = []
                    for item in pins:
                        location = item.get("location", {})
                        if location:
                            xy.append(location)

                    # 排序逻辑
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

                    # 引脚编号与标注
                    m = 0
                    for i_pin in range(len(pins)):
                        m += 1
                        if i_pin >= len(xy):
                            continue

                        x = xy[i_pin]["left"]
                        y = xy[i_pin]["top"]
                        h = xy[i_pin]["height"]
                        w = xy[i_pin]["width"]

                        cv2.putText(img1, str(m), (x, y), font, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
                        img1 = cv2.rectangle(img1, (x, y), (x + w, y + h), (255, 255, 0), 1)

                        # 检测缺失引脚
                        if i_pin < len(pins) - 1 and i_pin + 1 < len(xy):
                            if abs(x - xy[i_pin + 1]["left"]) > 100:
                                continue
                            if abs(x - xy[i_pin + 1]["left"]) > 30:
                                m += 2
                                self.add_log(f"[{base_name}] 检测到缺失第 {m - 1} 和 {m} 个引脚", "warning")
                            elif abs(x - xy[i_pin + 1]["left"]) > 20:
                                m += 1
                                self.add_log(f"[{base_name}] 检测到缺失第 {m} 个引脚", "warning")

                    # 保存结果
                    output_path = os.path.join(self.output_dir, f"{base_name}_detected.jpg")
                    cv2.imwrite(output_path, img1)
                    self.add_log(f"[{i + 1}/{total}] 检测结果已保存：{os.path.basename(output_path)}", "success")
                    processed_count += 1

                except Exception as e:
                    self.add_log(f"[{i + 1}/{total}] {json_file} 处理失败：{str(e)}", "error")

                # 更新进度
                progress = 30 + (i + 1) / total * 70
                self.update_progress(int(progress))

            self.defect_count = defect_count
            self.add_log(f"\n检测任务完成 | 总处理：{total} 个 | 有缺失：{defect_count} 个", "info")
            self.add_log(f"检测结果已保存至：{self.output_dir}", "success")

        except Exception as e:
            self.add_log(f"检测线程异常：{str(e)}", "error")
        finally:
            self.completed = True
            if self.task_id in task_info:
                task_info[self.task_id]["completed"] = True
            self.update_progress(100)
            # 更新任务进度信息
            task_progress[self.task_id] = {
                "progress": self.progress,
                "total": self.total,
                "defect_count": self.defect_count,
                "logs": self.logs,
                "completed": self.completed,
                "processed_count": processed_count,
                "defect_details": self.defect_details
            }


# 任务处理线程
def task_worker():
    while True:
        if task_queue:
            task = task_queue.pop(0)
            task.run()
        else:
            # 队列空时短暂休眠
            import time
            time.sleep(1)


# 启动任务处理线程
worker_thread = threading.Thread(target=task_worker, daemon=True)
worker_thread.start()


# API接口：检查JSON目录是否有文件
@app.route('/api/check-json', methods=['POST'])
def check_json_files():
    data = request.json
    json_dir = data.get('json_dir')

    if not json_dir:
        return jsonify({"code": 400, "message": "缺少JSON目录参数", "has_json": False})

    if not os.path.exists(json_dir):
        return jsonify({"code": 200, "has_json": False, "message": "目录不存在", "count": 0})

    if not os.path.isdir(json_dir):
        return jsonify({"code": 200, "has_json": False, "message": "路径不是目录", "count": 0})

    # 统计JSON文件数量
    json_files = [f for f in os.listdir(json_dir) if f.lower().endswith('.json')]
    return jsonify({
        "code": 200,
        "has_json": len(json_files) > 0,
        "count": len(json_files),
        "message": f"发现 {len(json_files)} 个JSON文件"
    })


# API接口：统计图像文件数量
@app.route('/api/count-images', methods=['POST'])
def count_images():
    data = request.json
    dir_path = data.get('dir')

    if not dir_path or not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return jsonify({"code": 400, "error": "目录不存在或无法访问", "count": 0})

    img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
    count = 0
    try:
        count = len([f for f in os.listdir(dir_path) if f.lower().endswith(img_exts)])
    except Exception as e:
        return jsonify({"code": 500, "error": str(e), "count": 0})

    return jsonify({"code": 200, "count": count})


# API接口：统计检测结果图像数量
@app.route('/api/count-detected-images', methods=['POST'])
def count_detected_images():
    data = request.json
    dir_path = data.get('dir')

    if not dir_path or not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return jsonify({"code": 400, "error": "目录不存在或无法访问", "count": 0})

    img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
    count = 0
    try:
        count = len([f for f in os.listdir(dir_path) if f.lower().endswith(img_exts) and '_detected' in f.lower()])
    except Exception as e:
        return jsonify({"code": 500, "error": str(e), "count": 0})

    return jsonify({"code": 200, "count": count})


# API接口：创建标注任务
@app.route('/api/annotate', methods=['POST'])
def create_annotation_task():
    data = request.json
    task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # 验证参数
    required_fields = ['raw_img_dir', 'json_output_dir', 'appid', 'client_id', 'client_secret']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"code": 400, "message": f"缺少参数：{field}"}), 400

    # 创建任务并加入队列
    task = AnnotationTask(
        task_id=task_id,
        raw_img_dir=data['raw_img_dir'],
        json_output_dir=data['json_output_dir'],
        appid=data['appid'],
        client_id=data['client_id'],
        client_secret=data['client_secret']
    )
    task_progress[task_id] = {
        "progress": 0,
        "success": 0,
        "fail": 0,
        "logs": [],
        "completed": False,
        "processed_count": processed_count
    }
    task_queue.append(task)

    return jsonify({
        "code": 200,
        "message": "标注任务已启动",
        "task_id": task_id,
        "success": 0,
        "fail": 0
    })


# API接口：创建检测任务
@app.route('/api/detect', methods=['POST'])
def create_detection_task():
    data = request.json
    task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # 验证参数
    required_fields = ['raw_img_dir', 'json_dir', 'output_dir']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"code": 400, "message": f"缺少参数：{field}"}), 400

    # 记录任务ID与检测结果目录的映射
    task_info[task_id] = {
        "output_dir": data['output_dir'],
        "completed": False
    }

    # 创建任务并加入队列
    task = DetectionTask(
        task_id=task_id,
        raw_img_dir=data['raw_img_dir'],
        json_dir=data['json_dir'],
        output_dir=data['output_dir']
    )
    task_progress[task_id] = {
        "progress": 0,
        "total": 0,
        "defect_count": 0,
        "logs": [],
        "completed": False,
        "processed_count": processed_count,
        "defect_details": []
    }
    task_queue.append(task)

    return jsonify({
        "code": 200,
        "message": "检测任务已启动",
        "task_id": task_id,
        "total": 0,
        "defect_count": 0
    })


# API接口：获取任务进度
@app.route('/api/progress/<task_id>', methods=['GET'])
def get_task_progress(task_id):
    progress = task_progress.get(task_id)
    if not progress:
        return jsonify({
            "code": 404,
            "message": "任务不存在"
        }), 404

    return jsonify({
        "code": 200,
        "data": progress
    })


# API接口：获取系统状态
@app.route('/api/status', methods=['GET'])
def get_system_status():
    return jsonify({
        "code": 200,
        "data": {
            "processed_count": processed_count,
            "queue_size": len(task_queue),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    })


# 检测结果图片列表接口
@app.route('/api/detection-images/<task_id>', methods=['GET'])
def get_detection_images(task_id):
    """获取指定检测任务生成的图片列表"""
    if task_id not in task_info:
        return jsonify({
            "code": 404,
            "message": f"任务ID不存在（{task_id}）"
        }), 404

    task_data = task_info[task_id]
    if not task_data["completed"]:
        return jsonify({
            "code": 400,
            "message": f"任务尚未完成（{task_id}）"
        }), 400

    output_dir = task_data["output_dir"]
    if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
        return jsonify({
            "code": 404,
            "message": f"检测结果目录不存在（路径：{output_dir}）"
        }), 404

    # 获取目录中的检测结果图片
    img_exts = ('.png', '.jpg', '.jpeg', '.bmp')
    images = []
    try:
        for f in os.listdir(output_dir):
            f_path = os.path.join(output_dir, f)
            if (f.lower().endswith(img_exts) and
                    '_detected' in f and
                    os.path.isfile(f_path)):
                # 编码文件名，支持特殊字符
                encoded_name = urllib.parse.quote_plus(f)
                images.append({
                    "name": f,
                    "path": f_path,
                    "url": f"/api/image/{task_id}/{encoded_name}"
                })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"读取目录失败：{str(e)}"
        }), 500

    return jsonify({
        "code": 200,
        "data": {
            "images": images,
            "count": len(images),
            "task_id": task_id,
            "output_dir": output_dir
        }
    })


# 单张图片接口
@app.route('/api/image/<task_id>/<path:filename>', methods=['GET'])
def get_image(task_id, filename):
    """返回指定的检测结果图片"""
    try:
        # 解码文件名
        filename = urllib.parse.unquote_plus(filename)
    except:
        return jsonify({"code": 400, "message": "文件名解析错误"}), 400

    if task_id not in task_info:
        return jsonify({"code": 404, "message": f"任务ID不存在（{task_id}）"}), 404

    output_dir = task_info[task_id]["output_dir"]
    image_path = os.path.join(output_dir, filename)

    if not os.path.exists(image_path) or not os.path.isfile(image_path):
        return jsonify({"code": 404, "message": f"图片不存在（路径：{image_path}）"}), 404

    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        mime = mimetypes.guess_type(image_path)[0] or 'image/jpeg'
        return Response(image_data, mimetype=mime)
    except Exception as e:
        return jsonify({"code": 500, "message": f"图片读取失败：{str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)