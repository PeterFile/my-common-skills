```text
███████╗██╗  ██╗██╗██╗     ██╗     ███████╗
██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝
███████╗█████╔╝ ██║██║     ██║     ███████╗
╚════██║██╔═██╗ ██║██║     ██║     ╚════██║
███████║██║  ██╗██║███████╗███████╗███████║
╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝
```

# my-common-skills

[中文](README.md) | [English](README.en.md)

按工作场景整理的常用 agent skills 集合。每个 skill 保留独立目录和原始辅助文件，入口文件是 `SKILL.md`。

## Quickstart

安装全部 skills：

```bash
npx skills add PeterFile/my-common-skills
```

只安装一个 skill：

```bash
npx skills add PeterFile/my-common-skills --skill task-pr-flow
```

## Skills

### [Agent 编排](agent-orchestration/)

| Skill                                                                                             | 一句话描述                                                       |
| ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| [`antigravity-cli`](agent-orchestration/antigravity-cli/)                                         | 调用 Antigravity CLI 做编码、审查、研究和验证。                  |
| [`autonomous-coding-agents`](agent-orchestration/autonomous-coding-agents/)                       | 把编码任务分派给 Codex、Claude Code、OpenCode 或 Hermes 子代理。 |
| [`codex-prompt-optimizer`](agent-orchestration/codex-prompt-optimizer/)                           | 把需求改写成更适合 Codex 执行的清晰任务提示。                    |
| [`dense-multi-agent-worktree-delivery`](agent-orchestration/dense-multi-agent-worktree-delivery/) | 用多个隔离 worktree 并行推进复杂软件交付。                       |
| [`kanban-operations`](agent-orchestration/kanban-operations/)                                     | 操作 Hermes Kanban，把任务拆分、路由、跟踪和收口。               |

### [软件开发](software-development/)

| Skill                                                                                  | 一句话描述                                                        |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [`codebase-design`](software-development/codebase-design/)                             | 分析模块边界，设计更深、更稳、更好测的代码接口。                  |
| [`commit-assistant`](software-development/commit-assistant/)                           | 整理 commit、PR 描述和发布说明。                                  |
| [`gh-address-comments`](software-development/gh-address-comments/)                     | 处理 GitHub PR review 或 issue 评论里的修改要求。                 |
| [`gh-fix-ci`](software-development/gh-fix-ci/)                                         | 排查 GitHub Actions CI 失败并制定修复。                           |
| [`github-workflows`](software-development/github-workflows/)                           | GitHub 全流程操作：仓库、分支、issue、PR、review、CI 和 release。 |
| [`grilling`](software-development/grilling/)                                           | 严格追问并压力测试计划、设计和技术方案。                          |
| [`improve-codebase-architecture`](software-development/improve-codebase-architecture/) | 扫描代码库，找出可深化模块和架构改进点。                          |
| [`living-documentation`](software-development/living-documentation/)                   | 代码行为变化后同步 .kiro/specs 需求和设计文档。                   |
| [`oss-issue-scout`](software-development/oss-issue-scout/)                             | 分析开源仓库，挑选更适合贡献的 issue。                            |
| [`pnpm`](software-development/pnpm/)                                                   | 处理 pnpm 工作区、依赖、catalog、patch 和 override。              |
| [`software-delivery-workflows`](software-development/software-delivery-workflows/)     | 软件交付总流程：规划、实现、调试、测试、评审和发布。              |
| [`task-pr-flow`](software-development/task-pr-flow/)                                   | 把功能拆成小任务、小分支和可合并的 PR 队列。                      |
| [`test-driven-development`](software-development/test-driven-development/)             | 按红绿重构流程先写失败测试，再实现功能或修 bug。                  |
| [`turborepo`](software-development/turborepo/)                                         | 处理 Turborepo monorepo、任务管线、缓存和 CI 优化。               |
| [`typescript-write`](software-development/typescript-write/)                           | 编写或重构 TypeScript/JavaScript，保持本地代码风格。              |

### [前端与动画](frontend-ui/)

| Skill                                                                     | 一句话描述                                                 |
| ------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [`cache-components`](frontend-ui/cache-components/)                       | 处理 Next.js Cache Components、缓存生命周期和局部预渲染。  |
| [`frontend-design`](frontend-ui/frontend-design/)                         | 设计和实现高质量前端页面、组件和应用界面。                 |
| [`gsap-core`](frontend-ui/gsap-core/)                                     | 使用 GSAP 基础动画：补间、缓动、透明度、位移和响应式动画。 |
| [`gsap-frameworks`](frontend-ui/gsap-frameworks/)                         | 在 Vue、Svelte、Nuxt、SvelteKit 等框架里正确接入 GSAP。    |
| [`gsap-performance`](frontend-ui/gsap-performance/)                       | 优化 GSAP 动画性能，减少卡顿、布局抖动和帧率问题。         |
| [`gsap-plugins`](frontend-ui/gsap-plugins/)                               | 使用 GSAP 插件：拖拽、Flip、SplitText、SVG、滚动平滑等。   |
| [`gsap-react`](frontend-ui/gsap-react/)                                   | 在 React/Next.js 中使用 GSAP，并处理 refs、清理和 SSR。    |
| [`gsap-scrolltrigger`](frontend-ui/gsap-scrolltrigger/)                   | 制作滚动触发动画、固定区块、scrub 和视差效果。             |
| [`gsap-timeline`](frontend-ui/gsap-timeline/)                             | 用时间线编排多步骤动画、标签、嵌套和播放控制。             |
| [`gsap-utils`](frontend-ui/gsap-utils/)                                   | 使用 GSAP 工具函数做范围映射、随机、吸附、数组包装等。     |
| [`ui-ux-pro-max`](frontend-ui/ui-ux-pro-max/)                             | 做 UI/UX 方案、界面改进、组件设计和视觉审查。              |
| [`vercel-react-best-practices`](frontend-ui/vercel-react-best-practices/) | 按 Vercel 工程实践优化 React/Next.js 性能。                |
| [`web-design-guidelines`](frontend-ui/web-design-guidelines/)             | 审查网页 UI、可访问性、布局和交互质量。                    |

### [文档与写作](docs-writing/)

| Skill                                                  | 一句话描述                                                       |
| ------------------------------------------------------ | ---------------------------------------------------------------- |
| [`doc-coauthoring`](docs-writing/doc-coauthoring/)     | 协作撰写文档、技术方案、规格和决策记录。                         |
| [`docs-write`](docs-writing/docs-write/)               | 按清晰、面向用户的风格写 Markdown/MDX 文档。                     |
| [`domain-modeling`](docs-writing/domain-modeling/)     | 梳理领域术语、核心概念和架构决策。                               |
| [`humanizer`](docs-writing/humanizer/)                 | 去掉 AI 味，让文字更像真人写作。                                 |
| [`obsidian-markdown`](docs-writing/obsidian-markdown/) | 编辑 Obsidian Markdown，包括双链、嵌入、callout 和 frontmatter。 |

### [设计与媒体](design-media/)

| Skill                                                                        | 一句话描述                                         |
| ---------------------------------------------------------------------------- | -------------------------------------------------- |
| [`audio-music-media-production`](design-media/audio-music-media-production/) | 生成或分析音乐、音频、频谱和相关媒体素材。         |
| [`baoyu-content-production`](design-media/baoyu-content-production/)         | 生成宝玉风格的中文知识图文、漫画和信息图。         |
| [`brand-guidelines`](design-media/brand-guidelines/)                         | 按 Anthropic 品牌规范处理颜色、字体和视觉风格。    |
| [`canvas-design`](design-media/canvas-design/)                               | 生成海报、静态视觉图、PNG/PDF 设计稿。             |
| [`comfyui`](design-media/comfyui/)                                           | 用 ComfyUI 生成或处理图片、视频和音频。            |
| [`creative-visual-production`](design-media/creative-visual-production/)     | 制作图表、原型、视觉参考、像素图、动画和设计规格。 |

### [生产力自动化](productivity-automation/)

| Skill                                                                                           | 一句话描述                                                             |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [`apple-automation`](productivity-automation/apple-automation/)                                 | 自动化 macOS 的 Notes、Reminders、Messages、Find My 等应用。           |
| [`communication-platform-workflows`](productivity-automation/communication-platform-workflows/) | 操作邮件、X/Twitter、元宝群聊等通信平台。                              |
| [`json-canvas`](productivity-automation/json-canvas/)                                           | 创建和编辑 JSON Canvas 图谱、节点和连线。                              |
| [`linear`](productivity-automation/linear/)                                                     | 读取、创建和更新 Linear issue、项目和团队工作流。                      |
| [`productivity-api-workflows`](productivity-automation/productivity-api-workflows/)             | 操作 Airtable、Google Workspace、Linear、Notion、PPT、PDF 等办公工具。 |
| [`project-canvas-os`](productivity-automation/project-canvas-os/)                               | 用项目文档和 Obsidian Canvas 管理项目状态和证据。                      |
| [`smart-home-operations`](productivity-automation/smart-home-operations/)                       | 控制智能家居设备、灯光、场景和本地 IoT 网关。                          |

### [研究与市场](research-market/)

| Skill                                                                                 | 一句话描述                                 |
| ------------------------------------------------------------------------------------- | ------------------------------------------ |
| [`market-sizing-analysis`](research-market/market-sizing-analysis/)                   | 计算 TAM、SAM、SOM 和市场机会规模。        |
| [`research-intelligence-workflows`](research-market/research-intelligence-workflows/) | 做资料搜集、论文检索、资讯监控和研究综述。 |

### [安全](security/)

| Skill                                                          | 一句话描述                                                |
| -------------------------------------------------------------- | --------------------------------------------------------- |
| [`security-best-practices`](security/security-best-practices/) | 做 Python、JavaScript/TypeScript、Go 的安全最佳实践审查。 |
| [`security-ownership-map`](security/security-ownership-map/)   | 基于 git 历史分析安全敏感代码归属和 bus factor。          |
| [`security-threat-model`](security/security-threat-model/)     | 为代码库建立威胁模型、资产、边界和缓解措施。              |

### [游戏开发](game-development/)

| Skill                                                    | 一句话描述                                         |
| -------------------------------------------------------- | -------------------------------------------------- |
| [`game-engine`](game-development/game-engine/)           | 构建网页游戏、Canvas/WebGL 渲染、碰撞和游戏循环。  |
| [`generate2dmap`](game-development/generate2dmap/)       | 生成 2D 游戏地图、战斗场景、tilemap 和碰撞区域。   |
| [`generate2dsprite`](game-development/generate2dsprite/) | 生成和处理 2D 精灵、角色、道具、特效和透明动画帧。 |

### [浏览器自动化](browser-automation/)

| Skill                                                                  | 一句话描述                                         |
| ---------------------------------------------------------------------- | -------------------------------------------------- |
| [`playwright`](browser-automation/playwright/)                         | 用真实浏览器做页面操作、截图、数据提取和 UI 验证。 |
| [`playwright-interactive`](browser-automation/playwright-interactive/) | 用持久浏览器会话快速调试网页或 Electron 界面。     |

### [部署运维](deployment-ops/)

| Skill                                            | 一句话描述                              |
| ------------------------------------------------ | --------------------------------------- |
| [`vercel-deploy`](deployment-ops/vercel-deploy/) | 部署应用到 Vercel，生成预览或线上部署。 |
