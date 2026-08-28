# 上传到 GitHub 的步骤

## 📋 准备工作

你的本地仓库位于：`E:/skill/novel-distiller`。

目标仓库：<https://github.com/NZa5/novel-distiller>

## 🚀 上传步骤

### 1. 创建 GitHub 仓库

如果目标仓库尚未创建，可以使用 GitHub CLI：

```bash
cd /e/skill/novel-distiller
gh auth status
gh repo create NZa5/novel-distiller --public --source=. --remote=origin
```

如果仓库已经存在，直接添加远程地址：

```bash
cd /e/skill/novel-distiller
git remote add origin https://github.com/NZa5/novel-distiller.git
```

如果 `origin` 已存在，先检查它指向的地址：

```bash
git remote -v
```

### 2. 推送代码

确认远程地址无误后推送当前分支：

```bash
git remote -v
git push -u origin HEAD
```

如果远程仓库要求使用 `main` 作为默认分支，可先执行：

```bash
git branch -M main
git push -u origin main
```

认证请通过 `gh auth login` 或 Git 的凭据管理器完成。不要把访问令牌、密码或其他凭据写进远程 URL、命令行历史或文档；需要排查认证状态时使用：

```bash
gh auth status
git remote -v
```

### 3. 验证上传

访问仓库页面：<https://github.com/NZa5/novel-distiller>

你应该能看到：
- ✅ README.md 显示在首页
- ✅ MIT License
- ✅ Python 项目标识

## 📝 后续配置（可选）

### 1. 设置仓库主题标签

在 GitHub 仓库页面点击 **⚙️ Settings** > **Topics**，添加：

```text
python, nlp, novel, ai, langchain, llm, text-analysis, skill, chinese
```

### 2. 添加项目描述

在仓库页面点击 **About** 旁边的 **⚙️**，填写：
- **Description**: `📚 小说蒸馏 Skill - 从小说中提取和分析核心信息的 AI 工具`
- **Website**: 留空或填写文档地址
- **Topics**: (已在上面添加)

### 3. 启用 GitHub Actions（可选）

如果要添加 CI/CD，创建 `.github/workflows/tests.yml`。

### 4. 更新 README 中的链接

仓库相关链接应统一指向：

```text
https://github.com/NZa5/novel-distiller
```

## 🎉 完成！

代码推送后即可在 GitHub 上查看项目。

### 项目内容

- **默认 Skill**：由 `SKILL.md` 和 `references/` 中的 Markdown 文档组成，无需 API Key、Python 或网络服务。
- **可选 Python 工具**：位于 `novel_distiller/`，适用于明确需要本地 CLI 的用户，并有单独的依赖和配置要求。
- **示例与测试**：分别位于 `examples/` 和 `tests/`。

### 下一步

1. **使用默认 Skill**：阅读 [README.md](README.md)、[INSTALL.md](INSTALL.md) 和 [QUICKSTART.md](QUICKSTART.md)。
2. **使用可选 Python 工具**：
   ```bash
   cd /e/skill/novel-distiller
   pip install -e .
   cp .env.example .env
   # 仅使用可选的 LLM 工具时，按需配置 .env
   python examples/basic_usage.py
   ```
3. **分享项目**：在仓库页面或社区分享项目链接，并持续收集反馈。

## 🆘 常见问题

### Q: 推送时提示认证失败？

A: 先确认 GitHub CLI 的登录状态：

```bash
gh auth status
gh auth login
```

也可以检查 Git 远程地址；其中不应包含访问令牌或密码：

```bash
git remote -v
```

### Q: 想修改提交历史？

A: 在推送前可以使用：

```bash
git commit --amend  # 修改最后一次提交
git rebase -i HEAD~3  # 交互式修改最近 3 次提交
```

### Q: 如何添加合作者？

A: Settings > Collaborators > Add people。

---

**仓库地址**：<https://github.com/NZa5/novel-distiller> 🎊
