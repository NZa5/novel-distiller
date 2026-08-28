# 贡献指南

感谢你考虑为 Novel Distiller 做出贡献！

## 开发环境设置

1. Fork 本仓库
2. 克隆你的 Fork

```bash
git clone https://github.com/your-username/novel-distiller.git
cd novel-distiller
```

3. 安装开发依赖

```bash
pip install -e ".[dev]"
```

4. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

## 开发流程

### 代码风格

使用 Black 和 isort 格式化代码：

```bash
black novel_distiller tests examples
isort novel_distiller tests examples
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码检查

```bash
flake8 novel_distiller
```

## 提交 Pull Request

1. 确保所有测试通过
2. 更新相关文档
3. 提交 PR 并描述你的更改
4. 等待审核

## 报告 Bug

使用 GitHub Issues 报告 Bug，请包含：

- 操作系统和 Python 版本
- 复现步骤
- 期望行为和实际行为
- 错误信息和日志

## 功能建议

欢迎提交功能建议！请在 Issue 中说明：

- 功能描述
- 使用场景
- 预期实现方式

## 代码审查标准

- 代码清晰易读
- 有适当的注释
- 有单元测试
- 符合项目代码风格

感谢你的贡献！
