---
created: 2026-07-13T11:58:53 (UTC +08:00)
tags: []
source: https://linux.do/t/topic/2571606
author: 
---

# 从 vibe coding 到 spec coding：我用 Trellis 的实践总结 - 开发调优 - LINUX DO

> ## Excerpt
> Where possible begins.

---
> 本篇是基于我在公司技术分享会的总结来梳理的哈，首先说一点，这个是我个人使用 Trellis 的理解和实践总结，如有不对的地方，还请各位大佬指正。非常感谢。

我现在用 ai 写代码很多时候都是一把梭的，也就是说我只需要给 ai 一个要求指令，剩下的就交给 ai 了，现在模型能力确实越来越强，有时候我甚至可以不用 superpowers 这种工作流插件都可以做到很规范。所以这种 vibe coding 的写法已经很广泛了，只要可以满足我们要求就可以。

但是这样做的问题就是项目长期积累下来基本上都是屎山级别的，后期越来越难以维护，就算是交给 ai 也是会导致漏洞百出，毕竟 ai 也不记得当时为什么这么写了，只能继续往屎山上堆新屎。

所以我觉得不管我们用的是 claude code、cursor 还是 codex，不管模型是 fable 5 还是 gpt-5.6，只是单纯的 vibe 的话，写出来的代码感觉基本都差不多。一个人写还能凑合，团队用基本是灾难了。

这就是为什么我越来越觉得作为开发的角度来讲，ai 编码不能长期停留在临时对话式开发。

而 trellis，是我用下来觉得值得在个人开发和团队协作里用的手脚架，它能帮我们逐渐习惯 spec coding。

所以这篇文章我想聊的不算是 trellis 安装使用教程吧，其实还是想讲一下这个：

> 建议我们写代码需要从 vibe coding 转向 spec coding，以及 trellis 到底是怎么帮我们做这件事的。

___

## [](https://linux.do/t/topic/2571606#p-20251843-ai-1)为啥 ai 写代码需要工程结构

也许会有人会觉得，我既然都用 ai 写代码了，那我为什么还要管什么规范任务上下文这些的？直接把需求丢给 ai，让它一路写到底不就行了吗？

其实这个想法我是能理解的，而且在很多场景下确实是没问题的。

但是我觉得这里要有个前提：

> 任务短且风险低。

就好比我们去写一个油猴脚本或者是做自己的个人项目，其实只要能跑起来，就没必要搞的太复杂了。这个时候 vibe 反而是最舒服的方式，快且直接，非常不错的。

甚至就算后面出了 bug 或者要加新的功能，我们也可以继续让 ai 来改。哪里报错就修哪里，需要加功能就继续让它加。

> 但最麻烦的地方，我觉得在于它每次改的时候，其实更多是在解决眼前这个局部问题。

虽然它能看到当前的报错，也能知道我们这次的需求，也能顺着现有代码补一段逻辑。但它不一定都知道这些比如：

> Example
> 
> -   这个模块原本为什么这样拆呢？
> -   这段逻辑是不是已经在别的地方实现过了？
> -   当前这样改法会不会绕开原来的架构约束呢？
> -   这次需求应该影响哪些测试和文档，是否有全面的边界规则？
> -   为了跑通临时加的兼容，会不会变成后面的历史包袱？

所以本质问题并不是 vibe coding 不能迭代。

但是如果一个项目长期都靠这种方式一直去堆代码的话，每一次修改都可能只是局部最优解法。单次看是没什么问题，但是几轮之后呢？ 代码里的会有大量的重复逻辑特殊判断，而且风格漂移，隐藏 bug 也会越来越多。

所以我觉得 ai 结合厉害的模型写代码确实省心，但是它缺少一个稳定的项目工程环境。

就比如我们平时用 ai 写代码的时候，其实很容易有一种错觉：

> 只要我把需求描述得足够清楚，ai 就应该能把事情做好。

但实际做项目的时候，很多问题并不是这一句话清楚就够了，而是 ai 不知道这个项目长期以来是怎么规划的。

就比如我们常见的这些情况:

> Example
> 
> -   项目的长期规范放在哪个地方呢？
> -   当前任务到底做到哪一步了？
> -   这次改动应该读哪些上下文？
> -   哪些历史决策不能随便推翻？
> -   做完以后哪些经验应该沉淀下来？
> -   下次开新会话，ai 怎么接着之前的任务继续做？

这些东西如果都靠我们每次都在对话里补充，也能搞，但长期下来就会很累。我觉得这不是我们想要的流程。

每次开新任务，都像重新带一个刚进项目的新同事一样。虽然它很厉害，写代码也快，但项目里的规矩，历史包袱，设计架构边界，测试习惯等，都得重新再讲一遍。

就像我们现在用的 ai coding 工具，比如 claude code、codex、cursor 这些，其实本质上都是 agent 工具，有个比较好理解的拆法是这样的：

> Agent = Model + Harness。

model 是模型本体，主要负责理解、推理、生成代码等 而 harness 则是模型之外那一整套让 ai 真正能按流程干活的一个工程规范。就好比我们项目规范要放哪里，任务状态要怎么管，上下文要怎么投喂，以及经验要怎么沉淀，工具要怎么调用，边界是在哪里等等。

而这些工具，模型只是其中一部分，真正让它能在项目里稳定工作的，其实还是 harness 那一层。

但这里还有个问题就是虽然模型很强，但是我们在实际使用中还是会遇到各种局限。比如会话失忆、规则文件失控、跨工具配置不通用等问题。

[![](https://cdn3.ldstatic.com/optimized/4X/d/a/1/da1bd18563d7e4141ce5ad6fbb1772120a71fac7_2_690x385.jpeg)

1920×1072 465 KB

](https://cdn3.ldstatic.com/original/4X/d/a/1/da1bd18563d7e4141ce5ad6fbb1772120a71fac7.jpeg)

___

## [](https://linux.do/t/topic/2571606#p-20251843-prompt-rules-skill-2)Prompt / Rules / Skill 解决了什么问题，不足的地方在哪里

有时候我们在使用过程中会发现让 ai 写代码功能的时候，实际结果跟我们想要的差别很大。

虽然现在随着强模型的一个一个发布，基本上我们只需要简单的描述引导，就可以很好的达到我们的想要的结果。但是使用久了其实还是会感觉到一些问题的。

比如它不知道项目规范是什么，也不知道架构约束在哪里，更不知道哪些代码不能动。基本上都是基于我们的提示词然后按照自己的理解写出来的，虽然能跑起来，但是不符合我们的要求。

所以我们就需要用一些技能插件来辅助 ai 更好的遵循规范化写代码。比如我们可以通过维护 CLAUDE.md 和 AGENTS.md 来声明项目规则等，又比如我们再通过写 rules 文件、用 skill、再加 hook 来给 ai 套上一层约束。但是单用某几个的时候其实还是有一些局限性。

### [](https://linux.do/t/topic/2571606#p-20251843-prompt-3)首先是 prompt 的局限

我们现在写代码基本上都是直接给 ai 输出我们的想要的需求，然后过程中再通过不断的描述矫正自己的需求和问题来让 ai 逐步去修正解决。

但问题是我们新开会话的话，之前说的东西就都没了，基本上又要再次重新大概说一遍情况，或者让 ai 基于我们上个会话写的代码 diff 下，其实是比较浪费 token 的，而且就算 ai 查看后也不一定了解我们之前想要的规范 需求 流程等。

所以 prompt 只适合临时一次性的需求，但是不持久，不稳定也难以复用。

### [](https://linux.do/t/topic/2571606#p-20251843-agentsmd-claudemd-rules-4)关于 AGENTS.md/ CLAUDE.md/rules 的价值和局限

基本上我们现在写代码都会开始维护 rule 文件了。

比如 cursor 用 `.cursorrules`，claude code 用 `CLAUDE.md`，还有些工具用 `AGENTS.md`。

这些文件可以把项目规范写进去，来告诉 ai 构建命令是什么、测试命令是什么、编码风格是什么、哪些事情不能做等要求。

而且这些规则是持久的，写一次就一直生效。ai 每次写代码前会先读这些规范，对减少低级错误很有帮助。

但是问题不在于文件，在于工具切换。

就像 `.cursorrules`、`CLAUDE.md` 这类文件更偏平台专属。比如我之前写的系列文章， 通过在 claude code 里面配置 AGENTS.md/ CLAUDE.md 以及在 .claude 下面配置项目级别的 rules，hook，和 skill 等。

如果团队工具统一还好一点，如果不限制的话就会导致有人用 claude code，有人用 cursor，有人用其他工具，每个人都得配一遍，而且还不好提交到仓库统一管理。

虽然 `AGENTS.md` 是开放标准，更通用一些，但它本身主要还是静态项目说明，不负责 task、journal、workflow-state 这些运行时状态。

特别是前几天 claude code 的漏洞导致很多公司都要求员工禁止使用 claude code 写代码，这就导致了我之前在 claude code 配置的项目级约束就废掉了。也不能快速更新到其他的 agent 工具。

而且 rule 规则也有问题的，随着项目发展，rules 文件会越写越长。新规范要加进去，旧规范又不敢删，最后变得越来越臃肿。就算靠人工维护 也是比较麻烦。

文件太长以后，ai 就容易出现上下文过载，忽略掉关键细节。而且 ai 是否每次都读、是否读对、是否真正遵守，也不一定的。

另外，rules 更像是静态规则，不是天然知道当前任务状态的。任务里的临时判断和经验，不一定能自然沉淀回规则。

### [](https://linux.do/t/topic/2571606#p-20251843-skill-5)skill 的价值和局限

我们现在开发基本上或多或少都会用到一些 skill 进行辅助开发。

skill 的好处就是可以把某类操作方法固化下来。比如需求澄清、debug、review、写测试、发布前检查这些工作流都可以做成 skill。

它比 rules 更灵活，是一套工作流程，也可以训练 ai 的行为模式。

> 但是随着模型越来越强，一些通用的 skill 的 效果就越来越低。

很强的模型其实本来就知道一些通用的流程规范，其实在用一些通用型 skill 的意义没有那么大了。

但是呢，项目型、领域型、团队型 skill 却不一样。它固化的是项目约定、团队流程、领域知识和收尾标准。这个解决的不是模型智商问题，而是上下文和一致性的问题。

不过项目级 skill 也有个致命问题就是每个平台的 skill 格式都不一样。

就比如我在 claude code 里面配置的项目级 skill 如果我转到 codex，就要重新调整适配一遍，而且每个工具的 skill 调用方式也不一样。

### [](https://linux.do/t/topic/2571606#p-20251843-h-6)本质问题原因

所以单独的 prompt、rules、skill 都有价值，prompt 解决临时需求，rules 解决通用规范，skill 解决固化流程。但它们分别解决局部问题。通常情况下我们都是结合这些一起协作使用，以此来更好的辅助 ai 写工程化代码规范。

但是尽管如此，还是有几个问题是不好解决的，比如：

**第一个问题是会话失忆。**

我们经常性需要新开会话继续沟通，但是每次新开一个窗口会话，ai 就会忘记之前的进度和背景，要么我们需要沟通的同时去维护一个 plan.md 跟进进度，要么就是我们重新总结一下上一个会话的内容和总结，然后再让新的会话继续执行。

所以 prompt、rules、skill 其实都没有解决这个问题。它们更多是在解决 ai 怎么写代码，而不是让 ai 怎么持续记住项目上下文。

**第二个问题是绑定具体工具。**

这个是我感受最深的痛点，特别是团队协作方面，只要换个 agent 所有项目级的规范配置就要重新弄，而且如果团队里用不同工具就没法统一。这不是某个工具的问题，而是现在这些配置本身就是工具专属的。

**第三个问题是缺少项目级闭环。**

没有任务资产，也没有跨会话记忆，更没有规范演进机制。这些配置更多是在解决单次对话里 ai 怎么写代码，而不是整个项目我们怎么去用 ai 持续演进。

[![](https://cdn3.ldstatic.com/optimized/4X/5/f/8/5f85ac49f7b922753481bb2e29d2f7a11b0b6c82_2_690x385.jpeg)

1920×1072 510 KB

](https://cdn3.ldstatic.com/original/4X/5/f/8/5f85ac49f7b922753481bb2e29d2f7a11b0b6c82.jpeg)

所以我们需要一个更加完整的方案。

___

## [](https://linux.do/t/topic/2571606#p-20251843-trellis-spec-coding-7)为什么我觉得 Trellis 比较适合作为 spec coding 实践

我们上面说了 prompt、rules、skill 这些技能插件都有价值，但它们有三个共同的问题就是会话失忆、绑定工具和缺少闭环。

那有没有一个方案能同时解决这三个问题？或者换句话说，有没有一个工具能真正实践 spec coding 的思想？

trellis 就是这样的一个 harness 工程实践。

它不仅仅是单纯的 prompt 包，也不算是单纯的 skill 集合。而是一个项目级的 ai 工作台。

### [](https://linux.do/t/topic/2571606#p-20251843-trellis-8)trellis 的核心理念

trellis 的核心理念不是让我们每次都重新解释项目，其实是要把项目规范、任务记录和工作记忆都沉淀到 `.trellis/` 里。

之后无论新开会话，换什么工具甚至做什么任务，ai 都可以从项目结构里读到我们需要的上下文。项目继续迭代时，新的稳定经验再通过 update-spec 之类的流程写回 spec，让这套项目知识持续更新。

### [](https://linux.do/t/topic/2571606#p-20251843-h-9)第一个优势：显著缓解会话失忆

我们上面说第一个问题是 prompt、rules、skill 都没解决会话失忆问题。每次开新会话，ai 就忘了之前的进度。

而 trellis 则可以通过 task、workspace、journal、启动上下文来恢复项目知识。比如上次做到哪里了、遇到了什么问题、下一步要做什么，都会记在 journal 里。新的会话启动时，ai 就可以从 `.trellis/` 文件重新加载项目知识。

虽然不算是说这样 ai 就有了持续记忆，但是项目知识可以被持久化到文件系统里面，每次启动可以重新读取。

在支持启动上下文或 hook 的平台上，下次开新的会话，ai 可以读取 journal 和活跃任务信息，更容易接着上次的思路继续做。 减少了重复去读取梳理记忆的时间和成本。

### [](https://linux.do/t/topic/2571606#p-20251843-h-10)第二个优势：跨平台共享核心，团队可以用不同工具

第二个问题是 `.cursorrules` 只能在 cursor 用，`CLAUDE.md` 只能在 claude code 用。换个工具就得重新配。

而 trellis 的 `.trellis/` 核心是跨平台的。其中 spec /task/workflow 更偏团队共享事实源，workspace /journal 是按 developer 隔离的工作 记忆。虽然每个工具需要单独配置适配层（比如 `trellis init --claude` 或 `--cursor`），但核心规范、任务都是同一套。

即使团队成员用不同的 agent 工具开发，但是可以共享同一套 `.trellis/` 事实源。如果有人解决了一个 ai 开发过程中比较容易踩的坑，只需要把这段经验写进.trellis/spec/ 并提交代码库。其他人拉取代码后，无论他们用 claude code、cursor 还是其他工具，ai 都能读取到这条新规范。

### [](https://linux.do/t/topic/2571606#p-20251843-h-11)第三个优势：形成完整的项目级闭环

然后最后一个问题就是 prompt、rules、skill 更多是在解决 ai 怎么 更加规范的去写代码，而不是项目怎么去用 ai 持续演进。

而 trellis 就把 spec、task、workflow、journal 组织成完整闭环，比如：

> Example
> 
> -   spec 管长期规范
> -   task 管当前任务
> -   workflow 管当前阶段
> -   journal 管工作记忆
> -   任务收尾的时候，ai 会引导我们判断哪些经验值得长期复用，再把稳定规则写回 spec 里面

而且它不会把所有规范一次性塞给 ai 的，而是按需注入，比如当前任务需要什么规范，就读什么规范。避免了规则文件失控导致的上下文过载。

> 其实 trellis 的价值就是把这些问题从只靠用户不断提醒，去变成项目结构里本来就有的工程。

> 当然，trellis 也不是完美方案。它需要前期投入、需要维护习惯、也有学习成本的。如果我们的项目已经到了 vibe coding 撑不住的阶段，需要一个更稳定的 ai 协作方式的话，trellis 就是目前比较完整的一个尝试。

[![](https://cdn3.ldstatic.com/optimized/4X/4/a/b/4abc1582e55b2a76b52310aeaba083190749e060_2_690x385.jpeg)

1920×1072 496 KB

](https://cdn3.ldstatic.com/original/4X/4/a/b/4abc1582e55b2a76b52310aeaba083190749e060.jpeg)

___

## [](https://linux.do/t/topic/2571606#p-20251843-trellis-12)Trellis 机制拆解

这一节我们简单了解下 trellis 的实现原理。

spec coding 的核心， 就是把项目规范、任务进度、工作记忆、经验沉淀，从临时对话搬到项目结构。

而 trellis 它不只是靠某一个文件解决问题，它是靠几块机制一起转起来的：规范、任务、工作流、上下文、记忆，以及最后的经验反哺。

首先我们先看下官方文档用 claude code 跑完 **`trellis init`** 后的目录。其他平台会写到各自的子目录，但 **`.trellis/`** 核心一致。

[![](https://cdn3.ldstatic.com/optimized/4X/9/3/e/93ea62e9eb4b0a8bb70e61c5b338f2e9d30c43fa_2_425x500.png)

1442×1694 300 KB

](https://cdn3.ldstatic.com/original/4X/9/3/e/93ea62e9eb4b0a8bb70e61c5b338f2e9d30c43fa.png)

[![](https://cdn3.ldstatic.com/optimized/4X/b/b/1/bb13ceb89f99274cfcc91782d011ee74580a3c8d_2_520x500.png)

1436×1380 122 KB

](https://cdn3.ldstatic.com/original/4X/b/b/1/bb13ceb89f99274cfcc91782d011ee74580a3c8d.png)

[![](https://cdn3.ldstatic.com/optimized/4X/0/e/5/0e54331fa3977278bd3d74d6179fe6e5b2277811_2_690x263.png)

1448×554 74.7 KB

](https://cdn3.ldstatic.com/original/4X/0/e/5/0e54331fa3977278bd3d74d6179fe6e5b2277811.png)

接下来我们来梳理下 trellis 在我们开发过程中是怎么工作的。

### [](https://linux.do/t/topic/2571606#p-20251843-h-13)第一步：新的会话先恢复项目上下文

我们一般 vibe coding 的时候最常见的问题，就是新开一个会话以后，ai 基本回到空白状态。

我们需要重新说一遍这个项目是什么、上次做到哪里、哪些规则要注意、当前任务有没有开始。

而 trellis 在会话启动时会做一件事，就是先给 ai 一份紧凑的项目上下文。

这些上下文内容会来自这些地方：  

[![](https://cdn3.ldstatic.com/optimized/4X/c/c/f/ccf62208ae9867c4b9d4af1b5bd9181d8ce8d87b_2_690x330.png)

1376×660 64.3 KB

](https://cdn3.ldstatic.com/original/4X/c/c/f/ccf62208ae9867c4b9d4af1b5bd9181d8ce8d87b.png)

这样 ai 进入项目时，至少不会像面对一个完全陌生的仓库。它能看到上次做了什么、现在有没有活跃任务、当前开发者是谁、接下来大概应该往哪里走。

所以这就是 trellis 缓解会话失忆的第一步。它没有让模型拥有真正的长期记忆。它做的是把需要记住的东西放回项目文件里。新会话启动时，再把这些文件读回来。

但是有一点需要注意，不同平台的启动入口是不完全一样的。

> 有 sessionstart hook、plugin 或 extension 的平台，打开终端后通常会自动注入这份紧凑上下文，所以我们直接描述任务就行。怀疑上下文 没加载时，可以新开一个会话，或者让 ai 读一次 `trellis-start` skill。这类平台通常没有用户可见的 `/trellis:start`，因为启动路径已经负责 orient 了。

**但是如果我们使用 codex 进行开发的时候还不太一样。**

> 因为它主要靠仓库根目录的 `AGENTS.md` 做 prelude， 再通过 `UserPromptSubmit` hook 注入 workflow-state 的，新版本 codex cli 里 hooks 可能已经默认开启了。但如果 / 菜单里看不到 trellis 的 command /skill，或者 workflow 指引没有自动注入，我们可以通过检查～/.codex/config.toml 里是否开启了 features.hooks = true。 并通过 /hooks 审批 trellis 安装的 hook。即便 hook 没跑起来，trellis 仍然可以通过 AGENTS.md fallback 让 ai 读取 trellis-start，只是体验会弱一些。

___

### [](https://linux.do/t/topic/2571606#p-20251843-prompt-14)第二步：每一轮 prompt 都带着当前状态

如果只在会话启动时恢复一次还是不够的。因为 ai coding 经常都是多轮对话，我们确认需求、补充边界、让它继续实现、让它检查、让它收尾。

这样的话如果 ai 不知道当前处于哪个阶段，就很容易跳步骤。需求还没确认就开始写代码，代码写完以后又忘了检查，检查完以后也不沉淀经验。

所以 trellis 是用 workflow-state 来解决这个问题的。

在支持 hook 的平台上，每条用户 prompt 进来时，trellis 都会给 ai 注入当前任务状态。常见 live 状态主要有这些：

[![](https://cdn3.ldstatic.com/optimized/4X/8/c/4/8c47f61a471e7b3519ab3d96f28e40660b402e1d_2_690x276.png)

1410×566 71.7 KB

](https://cdn3.ldstatic.com/original/4X/8/c/4/8c47f61a471e7b3519ab3d96f28e40660b402e1d.png)

所以这点是很重要的。因为 trellis 除了告诉 ai 项目规则，还会告诉 ai 当前走到了哪一步。有了这个状态，ai 每一轮都更容易判断现在应该继续澄清需求，还是开始实现，还是进入检查，还是做收尾。

___

### [](https://linux.do/t/topic/2571606#p-20251843-turn-task-15)第三步：先判断当前 turn 要不要建 task

很多人一听 spec coding，就会担心所有事情都要建任务、写 prd、走流程。 就好比我们现在用 superpowers skill 进行开发的时候很多人其实都觉得太重了，不管什么都要全部走一遍，既浪费时间又浪费成本。甚至都想卸载了。

而 trellis 的实际思路却没有像 superpowers 这么重。

当我们发起一个需求时，trellis 会先判断当前 turn 的性质。

如果只是问一个技术问题，比如某个库怎么用、某个报错什么意思，它可以直接回答，不需要建 task。

比如我们只是改一个很小的 bug，当前对话就能说清楚，也可以走 inline。最多提醒我们要不要创建 task，我们说不用，就直接处理。

只有当任务涉及多文件、多模块、需要设计、需要复盘，trellis 才会建议创建 task。

这也是我觉得它比起 superpowers 最好的地方。它不会把所有事情都流程化，而是根据任务复杂度决定要不要进入完整任务流程。

这一步对应的就是 `tasks/`。一旦创建 task，trellis 会在里面生成一个任务目录，后面的规划、设计、实现清单、调研记录都会落到这个目录里面。

___

### [](https://linux.do/t/topic/2571606#p-20251843-planning-16)第四步：planning 把临时需求变成任务资产

但我们需求进入 planning 以后，trellis 做的事情就比较像把一句临时需求，整理成可以持续推进的任务资产。

我们在一般 vibe 的时候可能会直接说 帮我做一个登录功能。 然后 ai 直接开始写，短期看起来很快。但很多关键问题会被跳过，比如登录失败要怎么处理、token 怎么设置过期的、是否支持第三方登录、老用户数据怎么兼容等等。

而 trellis 在 planning 阶段就会把这些东西先问清楚，再写进 task 目录。产出基本上就是这些：

[![](https://cdn3.ldstatic.com/optimized/4X/9/b/b/9bb32f68cc317b2598798f745509b59441bed87f_2_690x478.png)

1372×952 112 KB

](https://cdn3.ldstatic.com/original/4X/9/b/b/9bb32f68cc317b2598798f745509b59441bed87f.png)

这样的话， 比如我们今天做到一半，明天换一个会话继续，ai 就不需要从聊天记录里猜。它可以直接读 `prd.md`、`design.md`、`implement.md`，知道这个任务当初是怎么定义的。

___

### [](https://linux.do/t/topic/2571606#p-20251843-execute-task-artifact-spec-17)第五步：execute 按 task artifact 和 spec 做事

在 planning 完成后，任务就会进入 `in_progress` 了。这时 ai 就开始实现，但它不会只根据我们最后一句 prompt 写代码。它会综合这些上下文顺序：

[![](https://cdn3.ldstatic.com/optimized/4X/8/3/9/8397ed3840dc5a61e5d57ec6968293f07d39150a_2_690x388.png)

1382×778 88.6 KB

](https://cdn3.ldstatic.com/original/4X/8/3/9/8397ed3840dc5a61e5d57ec6968293f07d39150a.png)

这就是 trellis 和普通 rules 文件的区别。

普通 rules 文件更多是在告诉 ai 项目里有哪些长期规则。trellis 还会告诉 ai 当前任务要做什么、为什么这么做、哪些上下文必须读、现在执行到哪一步了。

所以 execute 阶段的核心，是让 ai 按任务资产和项目规范一起推进。

这里的 `spec/` 也不会一次性全塞给 ai。默认模板主要是 `backend/`、`frontend/`、`guides/`，ai 会按任务需要选择相关规范。这样比一个超长 rules 文件更容易维护，也更不容易上下文过载。

___

### [](https://linux.do/t/topic/2571606#p-20251843-check-18)第六步：check 会对照规范复核

很多 ai 编码流程里的检查，其实最后会变成一句比如跑一下 lint 和 test。虽然也有用，但是还是不够。因为有些问题测试抓不到。比如接口错误格式不符合项目约定、权限校验漏了、目录结构不符合团队习惯、某个模块依赖方向反了。

而 trellis 的 check 阶段会更接近一次小型 code review。 它会看当前 diff，也会读 `check.jsonl` 里声明的 spec /research，然后对照规范检查代码。

所以在我看来 trellis-check 的价值，不止是多跑几条命令。它会把检查标准从临时感觉，变成任务和规范里明确写下来的东西。

___

### [](https://linux.do/t/topic/2571606#p-20251843-update-spec-19)第七步：update-spec 只沉淀稳定经验

trellis 在任务做完以后，还有一个很关键的动作就是判断有没有经验值得沉淀。

这一步对应的是 `trellis-update-spec`。

不过这里容易有个误解，好像 ai 做完任务后，会把所有经验都自动写回 spec？

其实实际不应该这样的。spec 如果什么都收的话，最后就会变成垃圾桶。越写越长，越写越乱，ai 反而更难抓住重点。

更合理的做法是任务收尾时，让 ai 引导我们判断哪些经验值得长期复用。比如这些规则：

> Example
> 
> -   某类接口必须统一返回错误格式
> -   某个模块不能直接依赖另一个模块
> -   某类数据库 migration 必须带回滚说明
> -   某个坑已经踩过，以后应该写进规范避免重复踩

像上面的这些就是非常适合写入到 spec 里面的。

但如果是比如某个功能的登录接口改成 `/api/v2/login`，像这类信息更适合留在 task。

所以 update-spec 的重点其实是在于筛选，避免把 spec 变成堆积材料。

___

### [](https://linux.do/t/topic/2571606#p-20251843-finish-work-journal-20)第八步：finish-work 做归档和 journal

最后还有一个我觉得容易搞混的地方就是 `/trellis:finish-work` 不负责帮我们提交业务代码。

按照官方的流程说明，work commit 要先完成。也就是功能代码该 commit 的先 commit 掉。然后再去执行 /trellis:finish-work。

也就是说只有工作 commit 已经存在后，才应该运行 **`/trellis:finish-work`**。

如果功能代码还没 commit，它会拒绝执行。更准确一点说，它会忽略 `.trellis/workspace/`、`.trellis/tasks/` 这类 trellis 自己要处理的路径，但其他功能代码还有未提交改动时，会要求我们先处理业务改动。

这样做的目的也很清楚，就是业务代码的提交归业务代码，trellis 的归档和 journal 归 trellis。

journal 记录的是这次任务做了什么、提交了什么、遇到什么问题、下一步是什么。它放在 `workspace/` 里，按开发者隔离。

比如同事 A 和同事 B 各自有自己的 journal，不会互相覆盖，也不会抢同一个当前任务上下文。但 journal 进 git 后，团队仍然可以回看。如果有新人加入项目，也可以通过这些记录了解项目是怎么一步步做起来的。

___

### [](https://linux.do/t/topic/2571606#p-20251843-h-21)最后把这些流程串联起来理解

我们把上面这些步骤串起来，trellis 的机制就比较清楚了：

> Todo
> 
> 1.  新会话启动时，先恢复项目上下文
> 2.  每轮 prompt 注入 workflow-state
> 3.  判断当前 turn 是否需要创建 task
> 4.  planning 阶段把需求整理成 task artifact
> 5.  execute 阶段按 task artifact + spec 实现
> 6.  check 阶段按任务和规范复核
> 7.  update-spec 阶段筛选稳定经验
> 8.  work commit 先完成
> 9.  finish-work 归档 task，写 journal

这样来看的话，trellis 机制的重点其实已经从 ai 会不会写代码，转到 ai 写代码时有没有稳定的项目上下文、任务状态、检查标准和收尾机制了。

也就是说，vibe coding 更像一段对话往前冲。而 trellis 则是把这段对话变成一个有状态、有材料、有检查、有沉淀的任务流程。

[![](https://cdn3.ldstatic.com/optimized/4X/d/6/0/d60c229f9810141d26541e283c7ed7dd6acd3412_2_690x385.jpeg)

1920×1072 513 KB

](https://cdn3.ldstatic.com/original/4X/d/6/0/d60c229f9810141d26541e283c7ed7dd6acd3412.jpeg)

这里如果还有想要了解到可以看下官方文档说明 ：[How It Works - Trellis Doc](https://docs.trytrellis.app/zh/start/how-it-works)

___

## [](https://linux.do/t/topic/2571606#p-20251843-harness-22)和其他 Harness 思路的区别

讲完 trellis 的机制后，我们来再说说和其他主流 harness 方案的区别，其实没有谁更好，而是设计取向不同。我们可以把现有方案大概分成几类：

### [](https://linux.do/t/topic/2571606#p-20251843-h-23)**流程强化型**

代表是 superpowers，以及一些偏流程约束的 skills /rules。

这类核心特点是强调 ai 做事方法。比如先澄清需求、先写计划、先做 tdd、再 review。它解决的问题更像是：agent 应该按什么工程纪律做事。

它的价值其实很明显，特别适合把一个原始想法梳理成可执行计划，也适合让 ai 不要上来就乱写。

但是最大的问题就是重，我想这一点很多人深有体会。小任务如果也反复追问、反复 review，体验就会很啰嗦。更关键的是，如果没有项目级 task /spec/journal 这些资产，流程跑完以后，经验还是可能散在聊天记录里，下次还要重新提醒。

___

### [](https://linux.do/t/topic/2571606#p-20251843-h-24)规范管理型

代表是 openspec 这类 spec-first 思路。

这种核心特点是强调先对齐，再实现。每次变更会围绕 proposal、spec、design、tasks 这类结构化材料推进。

这类方案对复杂需求和长期系统很有帮助。它能把隐性的团队约定显式化，让 ai 在编码前先读规范，也更容易让输出贴近团队既有风格。

但是它的问题在于，规范写出来以后，ai 是否每次都读、是否读对、是否真的遵守，还需要额外机制兜住。任务状态怎么追踪、工作记忆怎么保留、不同平台怎么适配，也不一定是它的重点。

___

### [](https://linux.do/t/topic/2571606#p-20251843-agent-25)多 agent 编排型

代表是 oh-my-claudecode 这类多 agent 编排方案。

这种方案核心特点是把 planner、executor、reviewer、debugger 这些角色拆开，让不同 agent 分工处理复杂任务。

这类方案适合比较复杂的任务，尤其是需要规划、执行、评审、调试分开的场景。它的问题也很明显，简单来总结就是编排层会变重，agent、skills、hooks 一多，排查成本就上来了。简单任务用这类方案，容易变成过度编排。

___

### [](https://linux.do/t/topic/2571606#p-20251843-h-26)项目闭环型

代表就是 trellis。

它的核心特点是把 spec、task、workflow-state、jsonl、journal、finish /update-spec 串成一套项目级闭环。

它关注的重点，不只是某个命令好不好用，也不只是 ai 这次能不能把代码写出来。它更关心项目能不能形成一套 ai 可读取、可追溯、可持续演进的事实源。

所以我们看 trellis 其实 更像是在做全链路落地的，规范怎么沉淀，任务怎么追踪，会话怎么接续，经验怎么回流，不同工具怎么尽量共享同一套项目上下文等等。

### [](https://linux.do/t/topic/2571606#p-20251843-h-27)快速对比

[![](https://cdn3.ldstatic.com/optimized/4X/1/8/f/18f6b3bb665871b456ff9d615ae689e0607a9789_2_690x385.jpeg)

1376×768 284 KB

](https://cdn3.ldstatic.com/original/4X/1/8/f/18f6b3bb665871b456ff9d615ae689e0607a9789.jpeg)

如果我们想快速约束 ai 行为，skill /rules 可能更轻。

如果我们重点在规范先行，openspec 可能更对口。

如果我们想增强某个特定平台的体验，oh-my-claudecode 可能更直接。

如果我们想要项目级闭环，让规范、任务、记忆、经验都沉淀到项目里，trellis 是目前比较完整的尝试。

其实不同工具版本会变化，重点是理解设计取向差异，选适合自己项目的。

最后图片总结如下：

[![](https://cdn3.ldstatic.com/optimized/4X/1/1/8/11826308e9a6a2cca7488c3f295d5dc934157355_2_690x376.jpeg)

1408×768 279 KB

](https://cdn3.ldstatic.com/original/4X/1/1/8/11826308e9a6a2cca7488c3f295d5dc934157355.jpeg)

___

## [](https://linux.do/t/topic/2571606#p-20251843-h-28)对个人开发者的价值

其实很多人觉得，spec coding 的问题主要是团队协作时才会遇到。个人开发者只有自己一个人，应该不需要这么复杂的结构吧？

但是感觉个人项目做久了，也会遇到类似问题的。

这里举几个我平常遇到的问题。

**会话失忆**

我个人 vibe 的项目如果停几个月再回来，上次做到哪里、为什么这样设计，基本上全忘了。得重新翻代码、翻聊天记录，甚至干脆重新开始。

**工具切换**

本来我比较喜欢使用 claude code 进行开发的，但是前段时间说有漏洞，再加上最近没有 claude 模型可以用了，所以我也会用 codex 开发，甚至也会用到 cursor，但是每次换工具，我都要把之前在 `.cursorrules` 里配的规范，重新写成 `CLAUDE.md`。这点其实我觉得可以通过 AGENTS.md 来维护，但是 claude code 项目级别的 rules skill 就不行了。

**多项目混乱**

比如我是同时维护多个项目的，比如一个 go 后端的 api 服务，一个 react 前端的管理后台，一个 hugo 静态博客。

因为我个人是比较喜欢走 spec coding 的，而每个项目的规范还不一样，如果我在同一个 agent 工具里面多项目来回切换时，如果规范都散在会话里，ai 就很容易被上一段上下文或者通用习惯带偏。

**给自己挖坑**

这个才是我觉得最重要的问题，我让 ai 按当时的想法快速写代码，然后 3 个月后回来看，不知道为什么这样写。当时可能有很多权衡和取舍，但这些都只存在聊天记录里，而且很多我都进行了记忆压缩，就很难追朔。

所以综合这些情况来看，spec coding 对个人开发者的价值，其实不在于多一套流程。它解决的是这些真实会遇到的问题。就像我上面分析的 trellis 的机制就很不错。

spec coding 让我们在做任务时顺手留下必要文档。目的不是把个人项目写成大公司流程，重点是给未来的自己留一条能接上的线。哪怕我们几个月后回来继续搞，至少还能知道当时为什么这样拆、哪些问题已经查过、哪些经验值得继续复用。

虽然说我觉得个人开发者也需要工程结构，但通常不需要复杂的协作流程。

[![](https://cdn3.ldstatic.com/optimized/4X/d/0/8/d083bcc907ba56ce838fb0fe5d82021b09a9caef_2_690x385.jpeg)

1376×768 292 KB

](https://cdn3.ldstatic.com/original/4X/d/0/8/d083bcc907ba56ce838fb0fe5d82021b09a9caef.jpeg)

当然，如果是团队协作，spec coding 的价值会更明显。

___

## [](https://linux.do/t/topic/2571606#p-20251843-h-29)对团队的价值

如果是团队协作的话，spec coding 的价值其实会更加明显。

### [](https://linux.do/t/topic/2571606#p-20251843-h-30)团队成员可以用不同工具开发

这是 spec coding 对团队最直接的价值。之前因为项目规则规范的存在，不得不要求所有成员统一 agent 工具开发。但是并不是所有人每个 agent 工具都会 都适合自己的。如果有的同事不会用，还要增加时间学习成本。

而 trellis 就做到了核心跨平台，适配层各自独立。

比如同事 a 用 cursor，同事 b 用 claude code，新人 c 用 codex。三个人共享同一套 `.trellis/`，但各自用自己习惯的工具。

___

### [](https://linux.do/t/topic/2571606#p-20251843-git-31)哪些需要进 git，哪些不需要

我们在使用 trellis 进行团队协作时，哪些东西应该进 git，哪些不应该？

比如我个人建议需要进入 git 的有这些：

> Success
> 
> -   `.trellis/spec/`：团队规范，和代码一样走 pr review
> -   `.trellis/tasks/`：任务目录（prd、design、research），是项目资产
> -   `.trellis/workspace/{name}/`：各开发者的 journal，`/trellis:finish-work` 会追加 journal

个人觉得不需要进入 git 共享的比如这些：

> Failure
> 
> -   `.trellis/.developer`：记录当前开发者名，gitignored
> -   `.trellis/.runtime/`：会话运行时状态，gitignored

这样来安排的话，spec 和 task 进 git，意味着规范改动要像代码一样走 review。重要的 api 设计规范、测试约定、架构约束，都应该让团队看得到、讨论得起来。

而且每个开发者有自己的 workspace，journal 记录各自的工作过程。它不是统一规范，但能让团队看到一些真实的开发轨迹，新人接手时也更容易理解项目是怎么演进过来的。

而 `.trellis/.developer` 和 `.trellis/.runtime/` 才是 gitignored 的部分，这些是会话级别的临时状态，不需要进入版本控制。

任务目录应该进 git，因为它承载需求、设计、实施计划和调研记录。但任务目录也可能冲突，所以团队里最好通过 `--assignee` 明确负责人，避免两个人同时改同一个任务。

而且新人加入更容易快速上手。交接什么的都比较方便快捷。

比较重要的是 trellis 可以把经验沉淀被放进任务收尾流程里。

但是有一点，团队协作时，规范不是一成不变的。

项目做了大的变更，spec 要更新。引入新的测试框架，spec 要更新。但规范改动不能随意。重要的 spec 改动要走 pr review，需要团队讨论。

官方文档的思路也很明确：重要 spec 改动应该在 review 里讨论，spec 库要当成团队代码来维护。

这样规范演进是可控的、可追溯的。不会出现某个人私自改了规范，其他人不知道的情况。

[![](https://cdn3.ldstatic.com/optimized/4X/4/1/c/41caf8856082be393b63aaf82ed6287d40bc6093_2_690x385.jpeg)

1376×768 286 KB

](https://cdn3.ldstatic.com/original/4X/4/1/c/41caf8856082be393b63aaf82ed6287d40bc6093.jpeg)

___

## [](https://linux.do/t/topic/2571606#p-20251843-trellis-32)trellis 的适用边界和成本

虽然我个人觉得 trellis 是非常好的一个 harness 工程手脚架，但是却并不是每个人都需要使用的。也不是每个项目都必须使用的。

这里我举几个开发中的例子来看：

**一次性脚本**

比如我们是要写一个类似于油猴脚本这样的，其实就不需要 trellis。

我们直接 vibe 就可以的，不需要过度复杂化。

**没有长期维护价值的项目**

如果我们需要开发一个项目，用来变现，其实求快才是比较重要的。感觉直接让 ai inline 做就行。 至于建任务、写 PRD、沉淀经验这些，反而是负担。

**团队不愿意维护 spec**

如果团队人员比较少，而且只想安装个工具，期望它自动变规范，那 trellis 也不适合。

毕竟 trellis 不是魔法。它提供的是工程结构，却不会免维护的自动化的。spec 需要人写、需要人更新、需要人清理。

如果团队人员比较少，比如就两三个人，其实没必要使用 trellis 的，强行上 trellis 只会留下一堆空模板或过时规范，反而更乱。

### [](https://linux.do/t/topic/2571606#p-20251843-h-33)还有就是使用成本

毕竟 trellis 不是零成本的。需要学习上手的。

**第一，前期要理解 `.trellis/`。**

`spec/`、`tasks/`、`workspace/`、`workflow.md`、`.runtime/` 分别管什么，至少要大概知道。不然 ai 在做什么，我们自己也看不懂。

**第二，要习惯 plan /execute/finish。**

vibe coding 是说完需求马上开写。但是 trellis 会更强调先澄清、再实现、再检查、再收尾。

这个流程更稳，但也更慢。小任务上面用重流程，体验肯定不好。

**第三，spec 需要维护。**

如果技术栈变了、架构变了、团队约定变了，spec 就要跟着更新。过时的 spec 会误导 ai。

**第四，task 粒度要控制。**

task 太大，ai 容易迷失。task 太小，又会变成流程负担。

个人感觉一个比较舒服的粒度是这个任务确实值得复盘，确实涉及多个文件或多个决策，确实希望以后能接着看。

**第五，不同平台体验会有差异。**

trellis 官方支持的平台很多，但不同平台的 hook、command、sub-agent 能力不一样。能接入是一回事，体验是否完整又是另一回事。

这点不用去背平台列表，只要知道在用之前最好看一下自己常用工具的支持方式。

### [](https://linux.do/t/topic/2571606#p-20251843-h-34)**我的判断**

如果是短任务、小脚本、或者自己的小项目，直接 vibe 就行。

如果项目会长期维护、业务规则很多、团队多人协作、经常换 ai 工具、希望经验进入 repo，那 trellis 就很不错。

我个人更倾向于把 trellis 用在长期项目上，而不是把它用在每一个临时需求或者小项目上。

spec coding 的重点在于沉淀长期有复用价值的项目事实，不在于把每件事都流程化。

[![](https://cdn3.ldstatic.com/optimized/4X/6/9/a/69a76f280e82fdd767de6f1b7f0e72108ce128f0_2_690x385.jpeg)

1376×768 308 KB

](https://cdn3.ldstatic.com/original/4X/6/9/a/69a76f280e82fdd767de6f1b7f0e72108ce128f0.jpeg)

___

## [](https://linux.do/t/topic/2571606#p-20251843-h-35)实践建议：常见流程和命令

这里我只简单过一下我们在使用 trellis 的常用命令和姿势。

### [](https://linux.do/t/topic/2571606#p-20251843-h-36)**第一次初始化**

我们先安装 cli，然后在项目里初始化：

```css
npm install -g @mindfoldhq/trellis@latest
cd your-project
trellis init -u your-name
```

如果是已经初始化过的项目，新人一般也是跑 `trellis init -u your-name`，给自己这台设备设置开发者身份。

初始化后不要急着直接做功能。先把 bootstrap 任务跑完，让 ai 从真实代码里提取第一版 spec。否则 `.trellis/spec/` 里大多还是空模板，后面读了也没什么价值。

### [](https://linux.do/t/topic/2571606#p-20251843-codex-hook-37)**codex 需要额外开 hook**

这里有一点我需要专门说一下，如果我们是用 codex 进行开发的话， 需要在 `~/.codex/config.toml` 里开启 hook：

```ini
[features]
hooks = true
```

然后在 tui 里跑一次 `/hooks`，审批 trellis 安装的 `UserPromptSubmit` hook。

如果 不开的话，`/` 菜单里可能看不到 trellis 的命令，workflow-state 也不会自动注入。虽然还有 fallback，但体验会差很多。

其他平台按官方安装文档走就行，不同工具的接入方式会有差异。

### [](https://linux.do/t/topic/2571606#p-20251843-h-38)**日常使用：直接描述任务**

平时开发不需要先想我要不要建 task。我们直接在窗口说我们的需求就行。至于是否需要创建 task 这个判断交给 trellis 和 ai 就好。我们只需要在它问是否创建 task 时确认一下。

### [](https://linux.do/t/topic/2571606#p-20251843-h-39)**常用命令就三个**

**`/trellis:start`**

少数平台需要手动启动上下文时用。很多有 sessionstart hook 的平台，打开终端时已经自动 orient 了，所以平时不一定用得到。

**`/trellis:continue`**

这个最常用。当前任务规划完、实现完、检查完，都可以用它推进下一步。大概可以理解成：我确认了，继续往后走。

**`/trellis:finish-work`**

这个是任务收尾时用。 注意，功能代码要先 commit。`/trellis:finish-work` 不负责提交业务代码，它主要做归档 task 和写 journal。如果功能代码还有未提交改动，它会拒绝执行，提醒我们先处理业务代码。

trellis 是 skill-first 的，很多能力会根据上下文自动触发。其他的命令可以通过官方文档进行了解。这里我不再过多讲述：[真实业务场景 - Trellis Doc](https://docs.trytrellis.app/zh/start/real-world-scenarios)

___

## [](https://linux.do/t/topic/2571606#p-20251843-h-40)最后说一下

不可否认，vibe coding 当然有价值。写脚本、做自己的项目，它就是快。

但项目一旦要长期维护，问题就开始变得复杂且必要，比如规范要怎么保存，任务要怎么接续，经验要怎么沉淀，新会话怎么不从零开始等等问题。

这时候我就很建议上 trellis 了，不过是否需要在自己的项目里面上 trellis 可以根据自己的习惯和判断来哈。只不过我个人是比较习惯 spec coding 的开发模式的。

也可以看下我之前分享的这篇：[grill-me、Trellis、Superpowers 到底该用哪个？](https://linux.do/t/topic/2151853)

其他大佬的总结和分享：

[公司 Trellis 技术分享，有需要的佬可以复用](https://linux.do/t/topic/2017019)

[我是怎么用 Codex 嗨大了的？](https://linux.do/t/topic/2100914)

官方参考 / 学习文档：[Trellis - Trellis Doc](https://docs.trytrellis.app/zh)
