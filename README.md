# 智能芯片引脚检测系统

面向集成电路封装的**引脚检测、计数与缺失检查**工具：把芯片照片批量送入百度智能云「图像检测」自定义模型，得到每个引脚的位置框；本地再按排排序、逐颗编号、统计引脚数、按间距突变自动提示缺失引脚，最后输出 JSON 标注与带框编号的可视化结果图。

> 2025 年第七届全球校园人工智能算法精英大赛 · 算法主题赛（AI+集成电路）
> 团队编号：AIC-2025-53247201 ｜ 作品名称：智能芯片引脚检测系统
> 技术报告见 [`docs/技术报告.pdf`](docs/技术报告.pdf)（33 页）

## 功能

- **批量标注**：选择「原始图片目录」与「JSON 输出目录」，自动跳过已标注过的图片，断点续跑
- **引脚计数与编号**：按 `top` / `left` 排序后逐颗编号
- **缺失引脚检测**：按相邻引脚间距突变判断缺针，日志给出缺失序号
- **结果可视化**：输出带检测框与编号的结果图（OpenCV 绘制）
- **两种形态**：桌面版（PyQt5 单文件 GUI）+ 网页版（Flask 后端 + 单页前端，带任务进度轮询）

## 工作原理

1. **换 token**
   `POST https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=<API Key>&client_secret=<Secret Key>`
2. **逐图检测**
   `POST https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/xinjianit?access_token=<token>`，请求体 `{"image": "<图片 base64>"}`
3. **本地后处理**：解析响应里的 `results[].location`（引脚框），排序 → 编号 → 间距判断 → 绘图输出

> `xinjianit` 是百度智能云上的自定义检测模型名。**换成你自己训练的模型名**，否则调用会失败。

## 目录结构

```
desktop/芯片引脚检测系统.py     PyQt5 桌面版：GUI + 标注线程 + 检测线程
web/backend/app.py              Flask 后端：任务队列、进度跟踪、9 个 HTTP 接口
web/frontend/index.html         主界面（单页，默认调用 127.0.0.1:8000）
web/frontend/index_alt.html     备用界面（统一 API_BASE 常量，改后端地址只改一处）
samples/芯片照片/               9 张样例芯片照片（IC_1 / IC_2 / IC_4 …）
docs/技术报告.pdf               参赛技术报告
scripts/run_web.sh|.bat         一键启动网页版后端
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

- 桌面版需要 `PyQt5`；网页版需要 `flask` + `flask-cors`；两者共用 `opencv-python` / `numpy` / `requests`。

### 2. 桌面版

```bash
python desktop/芯片引脚检测系统.py
```

界面里依次：① 选择原始图片目录 → ② 选择 JSON 输出目录 → ③ 选择结果图输出目录 → ④ 填入百度云 **App ID / API Key / Secret Key** → ⑤「开始标注」→ 进度完成后「开始检测」。

### 3. 网页版

```bash
python web/backend/app.py        # 或 scripts/run_web.bat
```

浏览器打开 `web/frontend/index.html`（默认后端地址 `http://127.0.0.1:8000`）。

后端接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/check-json` | 检查 JSON 输出目录完整性 |
| POST | `/api/count-images` | 统计原始图片数量 |
| POST | `/api/count-detected-images` | 统计已检测图片数量 |
| POST | `/api/annotate` | 启动批量标注任务 |
| POST | `/api/detect` | 启动检测/可视化任务 |
| GET | `/api/progress/<task_id>` | 查询任务进度 |
| GET | `/api/status` | 服务状态 |
| GET | `/api/detection-images/<task_id>` | 列出检测结果图 |
| GET | `/api/image/<task_id>/<filename>` | 取单张结果图 |

> 后端换了地址/端口时，把前端里的 `http://127.0.0.1:8000` 批量替换成实际地址；`index_alt.html` 只需改一个 `API_BASE` 常量。

## 凭据与安全

- **代码中不含任何密钥**：桌面版由用户在界面输入，网页版随请求参数传入，运行时不写入磁盘。
- 使用前需在百度智能云开通「图像检测」并训练好引脚检测模型；`App ID` 为应用标识，换 token 实际用 `API Key` + `Secret Key`。
- 如果你的密钥曾经出现在截图、聊天记录或其他仓库中，请到控制台**重置密钥**。

## 说明与局限

- 检测效果取决于云端模型的训练质量与拍摄条件（光照、对焦、引脚反光、背景复杂度）。
- 缺失引脚判断是**间距启发式**：对上下两排交错排列的芯片需要按排分别处理，极端透视下可能误报。
- 仓库**不包含**打包后的 `exe`（110 MB）、演示视频（215 MB）、答辩 PPT 与报名佐证材料（体积大、含报名信息），需要时另行索取。
- 当前版本只处理图片，不支持视频流实时检测。

## 许可

本项目代码采用 MIT 许可，见 [`LICENSE`](LICENSE)。调用百度智能云 API 需遵守其服务条款与计费规则。
