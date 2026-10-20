#!/usr/bin/env bash
# 启动网页版后端（Flask，默认 http://127.0.0.1:8000）
set -e
cd "$(dirname "$0")/../web/backend"
python app.py
