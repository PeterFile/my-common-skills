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

A collection of reusable agent skills organized by work domain. Each skill keeps its own directory and supporting files, with `SKILL.md` as the entry point.

## Quickstart

Install all skills:

```bash
npx skills add PeterFile/my-common-skills
```

Install one skill:

```bash
npx skills add PeterFile/my-common-skills --skill task-pr-flow
```

## Skills

### [Agent Orchestration](agent-orchestration/)

| Skill                                                                                             | One-line description                                                        |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [`antigravity-cli`](agent-orchestration/antigravity-cli/)                                         | Delegate coding, review, research, and validation work to Antigravity CLI.  |
| [`autonomous-coding-agents`](agent-orchestration/autonomous-coding-agents/)                       | Delegate coding tasks to Codex, Claude Code, OpenCode, or Hermes subagents. |
| [`codex-prompt-optimizer`](agent-orchestration/codex-prompt-optimizer/)                           | Rewrite requests into clear, scoped prompts that Codex can execute well.    |
| [`dense-multi-agent-worktree-delivery`](agent-orchestration/dense-multi-agent-worktree-delivery/) | Run complex software delivery across multiple isolated worktrees.           |
| [`kanban-operations`](agent-orchestration/kanban-operations/)                                     | Operate Hermes Kanban workflows for task routing, tracking, and closeout.   |

### [Software Development](software-development/)

| Skill                                                                                  | One-line description                                                                    |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [`codebase-design`](software-development/codebase-design/)                             | Design deeper, more stable, and more testable module interfaces.                        |
| [`commit-assistant`](software-development/commit-assistant/)                           | Prepare commits, pull request descriptions, and release notes.                          |
| [`gh-address-comments`](software-development/gh-address-comments/)                     | Address GitHub pull request review comments and issue feedback.                         |
| [`gh-fix-ci`](software-development/gh-fix-ci/)                                         | Investigate GitHub Actions failures and plan fixes.                                     |
| [`github-workflows`](software-development/github-workflows/)                           | Handle GitHub repositories, branches, issues, pull requests, reviews, CI, and releases. |
| [`grilling`](software-development/grilling/)                                           | Stress-test plans, designs, and technical proposals with direct questioning.            |
| [`improve-codebase-architecture`](software-development/improve-codebase-architecture/) | Scan a codebase for module and architecture improvements.                               |
| [`living-documentation`](software-development/living-documentation/)                   | Keep `.kiro/specs` requirements and design docs in sync with code behavior.             |
| [`oss-issue-scout`](software-development/oss-issue-scout/)                             | Analyze open-source repositories and find suitable contribution issues.                 |
| [`pnpm`](software-development/pnpm/)                                                   | Work with pnpm workspaces, dependencies, catalogs, patches, and overrides.              |
| [`software-delivery-workflows`](software-development/software-delivery-workflows/)     | Plan, implement, debug, test, review, and ship software changes.                        |
| [`task-pr-flow`](software-development/task-pr-flow/)                                   | Split features into small tasks, short branches, and mergeable pull request sequences.  |
| [`test-driven-development`](software-development/test-driven-development/)             | Follow red-green-refactor by writing failing tests before implementation.               |
| [`turborepo`](software-development/turborepo/)                                         | Manage Turborepo monorepos, task pipelines, caching, and CI.                            |
| [`typescript-write`](software-development/typescript-write/)                           | Write or refactor TypeScript and JavaScript while matching local code style.            |

### [Frontend and Animation](frontend-ui/)

| Skill                                                                     | One-line description                                                                        |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [`cache-components`](frontend-ui/cache-components/)                       | Work with Next.js Cache Components, cache lifetimes, and partial prerendering.              |
| [`frontend-design`](frontend-ui/frontend-design/)                         | Design and build polished frontend pages, components, and application UI.                   |
| [`gsap-core`](frontend-ui/gsap-core/)                                     | Build core GSAP animations with tweens, easing, opacity, movement, and responsive behavior. |
| [`gsap-frameworks`](frontend-ui/gsap-frameworks/)                         | Use GSAP correctly in Vue, Svelte, Nuxt, SvelteKit, and related frameworks.                 |
| [`gsap-performance`](frontend-ui/gsap-performance/)                       | Optimize GSAP animations for smoother frames and less layout jank.                          |
| [`gsap-plugins`](frontend-ui/gsap-plugins/)                               | Use GSAP plugins for dragging, Flip, SplitText, SVG work, smooth scrolling, and more.       |
| [`gsap-react`](frontend-ui/gsap-react/)                                   | Use GSAP in React and Next.js with refs, cleanup, and SSR constraints.                      |
| [`gsap-scrolltrigger`](frontend-ui/gsap-scrolltrigger/)                   | Build scroll-triggered animations, pinned sections, scrub effects, and parallax.            |
| [`gsap-timeline`](frontend-ui/gsap-timeline/)                             | Sequence multi-step animations with timelines, labels, nesting, and playback control.       |
| [`gsap-utils`](frontend-ui/gsap-utils/)                                   | Use GSAP utility helpers for mapping, clamping, snapping, randomness, and wrapping.         |
| [`ui-ux-pro-max`](frontend-ui/ui-ux-pro-max/)                             | Plan, improve, review, and refine UI and UX across common product interfaces.               |
| [`vercel-react-best-practices`](frontend-ui/vercel-react-best-practices/) | Optimize React and Next.js performance using Vercel engineering practices.                  |
| [`web-design-guidelines`](frontend-ui/web-design-guidelines/)             | Review web UI quality, accessibility, layout, and interaction details.                      |

### [Documentation and Writing](docs-writing/)

| Skill                                                  | One-line description                                                                |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| [`doc-coauthoring`](docs-writing/doc-coauthoring/)     | Co-author documentation, technical proposals, specifications, and decision records. |
| [`docs-write`](docs-writing/docs-write/)               | Write clear, reader-focused Markdown and MDX documentation.                         |
| [`domain-modeling`](docs-writing/domain-modeling/)     | Clarify domain terms, core concepts, and architectural decisions.                   |
| [`humanizer`](docs-writing/humanizer/)                 | Remove AI-sounding phrasing and make writing feel more natural.                     |
| [`obsidian-markdown`](docs-writing/obsidian-markdown/) | Edit Obsidian Markdown with wikilinks, embeds, callouts, and frontmatter.           |

### [Design and Media](design-media/)

| Skill                                                                        | One-line description                                                              |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| [`audio-music-media-production`](design-media/audio-music-media-production/) | Generate or analyze music, audio, spectrograms, and related media assets.         |
| [`baoyu-content-production`](design-media/baoyu-content-production/)         | Create Baoyu-style Chinese knowledge visuals, comics, and infographics.           |
| [`brand-guidelines`](design-media/brand-guidelines/)                         | Apply Anthropic brand colors, typography, and visual style.                       |
| [`canvas-design`](design-media/canvas-design/)                               | Create posters, static visuals, and PNG or PDF design artifacts.                  |
| [`comfyui`](design-media/comfyui/)                                           | Generate or process images, video, and audio with ComfyUI.                        |
| [`creative-visual-production`](design-media/creative-visual-production/)     | Create diagrams, prototypes, references, pixel art, animations, and design specs. |

### [Productivity Automation](productivity-automation/)

| Skill                                                                                           | One-line description                                                                     |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| [`apple-automation`](productivity-automation/apple-automation/)                                 | Automate macOS apps such as Notes, Reminders, Messages, and Find My.                     |
| [`communication-platform-workflows`](productivity-automation/communication-platform-workflows/) | Operate email, X/Twitter, Yuanbao groups, and other communication platforms.             |
| [`json-canvas`](productivity-automation/json-canvas/)                                           | Create and edit JSON Canvas maps, nodes, and edges.                                      |
| [`linear`](productivity-automation/linear/)                                                     | Read, create, and update Linear issues, projects, and team workflows.                    |
| [`productivity-api-workflows`](productivity-automation/productivity-api-workflows/)             | Operate Airtable, Google Workspace, Linear, Notion, PowerPoint, PDFs, and related tools. |
| [`project-canvas-os`](productivity-automation/project-canvas-os/)                               | Manage project state and evidence with project documents and Obsidian Canvas.            |
| [`smart-home-operations`](productivity-automation/smart-home-operations/)                       | Control smart-home devices, lights, scenes, and local IoT bridges.                       |

### [Research and Market Analysis](research-market/)

| Skill                                                                                 | One-line description                                                     |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [`market-sizing-analysis`](research-market/market-sizing-analysis/)                   | Calculate TAM, SAM, SOM, and market opportunity size.                    |
| [`research-intelligence-workflows`](research-market/research-intelligence-workflows/) | Gather sources, search papers, monitor updates, and synthesize research. |

### [Security](security/)

| Skill                                                          | One-line description                                                             |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| [`security-best-practices`](security/security-best-practices/) | Review Python, JavaScript, TypeScript, and Go code for security best practices.  |
| [`security-ownership-map`](security/security-ownership-map/)   | Analyze sensitive code ownership and bus factor from git history.                |
| [`security-threat-model`](security/security-threat-model/)     | Build threat models with assets, trust boundaries, abuse paths, and mitigations. |

### [Game Development](game-development/)

| Skill                                                    | One-line description                                                                           |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| [`game-engine`](game-development/game-engine/)           | Build web games with Canvas or WebGL rendering, collisions, controls, and game loops.          |
| [`generate2dmap`](game-development/generate2dmap/)       | Generate 2D game maps, battle scenes, tilemaps, and collision areas.                           |
| [`generate2dsprite`](game-development/generate2dsprite/) | Generate and process 2D sprites, characters, props, effects, and transparent animation frames. |

### [Browser Automation](browser-automation/)

| Skill                                                                  | One-line description                                                               |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [`playwright`](browser-automation/playwright/)                         | Use a real browser for page actions, screenshots, extraction, and UI verification. |
| [`playwright-interactive`](browser-automation/playwright-interactive/) | Debug web pages and Electron interfaces with a persistent browser session.         |

### [Deployment Operations](deployment-ops/)

| Skill                                            | One-line description                                                        |
| ------------------------------------------------ | --------------------------------------------------------------------------- |
| [`vercel-deploy`](deployment-ops/vercel-deploy/) | Deploy applications to Vercel and create preview or production deployments. |
