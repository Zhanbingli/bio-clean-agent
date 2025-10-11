.PHONY: help install install-dev install-all clean test lint format web docs

help:  ## 显示帮助信息
	@echo "可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装基本依赖
	pip install -e .

install-api:  ## 安装包含 API 支持
	pip install -e .[api]

install-dev:  ## 安装开发依赖
	pip install -e .[dev]

install-all:  ## 安装所有依赖
	pip install -e .[all]

clean:  ## 清理临时文件和缓存
	@bash scripts/clean.sh

test:  ## 运行测试（需要先安装 dev 依赖）
	pytest tests/ -v

test-cov:  ## 运行测试并生成覆盖率报告
	pytest tests/ -v --cov=src/bio_clean_agent --cov-report=html --cov-report=term

lint:  ## 代码质量检查
	ruff check src/
	mypy src/

format:  ## 格式化代码
	black src/ examples/
	ruff check --fix src/

web:  ## 启动 Web 服务器
	python start_web.py

demo:  ## 运行示例程序
	python examples/intelligent_agent_demo.py

build:  ## 构建发布包
	python -m build

check-deps:  ## 检查依赖更新
	pip list --outdated

tree:  ## 显示项目结构
	tree -L 3 -I '.venv|.git|__pycache__|*.pyc|*.egg-info' .

size:  ## 显示项目大小
	@echo "项目大小统计："
	@du -sh . 2>/dev/null || echo "无法获取大小"
	@echo ""
	@echo "代码行数统计："
	@find src -name "*.py" | xargs wc -l | tail -1

init:  ## 初始化新环境
	python -m venv .venv
	@echo "虚拟环境已创建！"
	@echo "激活虚拟环境："
	@echo "  source .venv/bin/activate  (Linux/Mac)"
	@echo "  .venv\\Scripts\\activate  (Windows)"

upgrade-deps:  ## 升级所有依赖到最新版本
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -e .[all]

.DEFAULT_GOAL := help
