---
created: 2026-07-02T17:22:53 (UTC +08:00)
tags: []
source: https://linux.do/t/topic/2296905
author: 
---

# 我是怎么用grill-me的，Matt pocock技能库使用经验分享。 - 开发调优 - LINUX DO

> ## Excerpt
> 这段时间用mattpocock/skills搞了几个给自己用的小玩意，分享一点经验。  啥最好用 grill-me/grill-with-docs 王者grill-me/grill-with-docs再次上线。这技能强就强在“达成共识”四个字，如果你的需求太宽泛，是真的会问到你神志不清的。我试过几次前面一些问题都还是会认真看，后面就摆烂直接开启Yes工程师模式了。  但王者也需要注意一些点，grill-with-docs会记录文档，很好的设计，但文档在完成任务之后应该删掉，因为可能会与后续的需求产生冲突。我在WinTProxy（自己搞的一个Win平台透明代理）的重构就遇到了与文档冲突的问题。我想用 ndisapi 取代 WinDivert，以支持在 WSL / Hyper-V 的 NAT 环境下进行数据包捕获和改写。但原有架构是基于三层的，多个 Worker 都在 IP 层处理报文（当时还写了 docs/adr 文档）。切换到 ndisapi 后就遭殃了，它工作在二层，而 NAT 流量会跨越虚拟网卡和物理网卡等多个接口，结果同一个数据包被重复捕获了好几次。  to-issues 这个技...

---
这段时间用 mattpocock/skills 搞了几个给自己用的小玩意，分享一点经验。

### [](https://linux.do/t/topic/2296905#p-18588878-h-1)啥最好用

#### [](https://linux.do/t/topic/2296905#p-18588878-grill-megrill-with-docs-2)grill-me/grill-with-docs

王者 grill-me/grill-with-docs 再次上线。这技能强就强在 “达成共识” 四个字，如果你的需求太宽泛，是真的会问到你神志不清的。我试过几次前面一些问题都还是会认真看，后面就摆烂直接开启 Yes 工程师模式了。  
但王者也需要注意一些点，grill-with-docs 会记录文档，很好的设计，但文档在完成任务之后应该删掉，因为可能会与后续的需求产生冲突。我在 WinTProxy（自己搞的一个 Win 平台透明代理）的重构就遇到了与文档冲突的问题。我想用 ndisapi 取代 WinDivert，以支持在 WSL / Hyper-V 的 NAT 环境下进行数据包捕获和改写。但原有架构是基于三层的，多个 Worker 都在 IP 层处理报文（当时还写了 docs/adr 文档）。切换到 ndisapi 后就遭殃了，它工作在二层，而 NAT 流量会跨越虚拟网卡和物理网卡等多个接口，结果同一个数据包被重复捕获了好几次。

#### [](https://linux.do/t/topic/2296905#p-18588878-to-issues-3)to-issues

这个技能的其中一个思想是很值得参考的，垂直切片。这要求任务划分是从端到端的划分，而不是层间划分。一个任务需要处理完一个需求从后端到前端的全部实现，有效反馈对于 AGENTS 来说是提效的一个重点。

#### [](https://linux.do/t/topic/2296905#p-18588878-diagnose-4)diagnose

很好用的 debug 技能，上面那个问题最后就是用它找的，当然也算是我懒，主要是 trace 级别日志太多了，也懒得看。不过这个技能本身规范了一整套流程，有点啰嗦的。后来我自己改了一套更个人化的技能库，对这个技能就是砍掉了后面的修改和测试，只报告原因就行了，把修改和测试交给 to-issues 和 tdd。

#### [](https://linux.do/t/topic/2296905#p-18588878-tdd-5)tdd

另一个王者，AGENTS 时代大概 tdd 是最合适的了，要是再配上 rust。什么叫做写完就结项？准确来说不是这个技能是王者，是测试驱动这种思想是王者。

### [](https://linux.do/t/topic/2296905#p-18588878-h-6)啥我不用

这里列几个我不用的技能，不过 mattpocock 的技能库里面的 engineering 基本都很有用就是了。顺带一提，我自己魔改就是 engineering 剔除了 triage，魔改了包括 zoom-out 在内的其他技能，然后加上了 handoff 做 session 交接。

#### [](https://linux.do/t/topic/2296905#p-18588878-issue-tracker-7)前置配置的 Issue tracker

并不是说不好用，只是我认为做本地的文档会方便一点。但 Matt pocock 原来设计就是维护 github 上的项目的，所以并没有什么毛病，也就开头配置时候多个选择而已。

#### [](https://linux.do/t/topic/2296905#p-18588878-triage-8)triage

这是搭配上面的 Issue tracker 用的，你如果是本地文档，你大概率不会用这个。因为你不可能先写个文档描述 issue，然后再丢目录里面去排序吧！真的有人这样做吗？

#### [](https://linux.do/t/topic/2296905#p-18588878-zoom-out-9)zoom-out

这玩意就一句话，直接写提示词都行，没有什么工作流程之类的，所以本质上只是方便一点。魔改的话可以让它做些数据流图啊之类的，更清晰一点。

### [](https://linux.do/t/topic/2296905#p-18588878-h-10)一般咋用

#### [](https://linux.do/t/topic/2296905#p-18588878-grill-with-docs-prototypeoptional-to-prd-to-issues-tdd-11)grill-with-docs → prototype(optional) → to-prd → to-issues → tdd

#### [](https://linux.do/t/topic/2296905#p-18588878-improve-codebase-architecture-prototypeoptional-to-prd-to-issues-tdd-12)improve-codebase-architecture → prototype(optional) → to-prd → to-issues → tdd

#### [](https://linux.do/t/topic/2296905#p-18588878-diagnose-tdd-13)diagnose → tdd

这里面的 prototype 一般要新开一个 session 去完成，前后用 handoff 交接。  
这个 to-prd → to-issues 很多时候是形影不离的，一开始我认为这两个就该合并，但后来实际开发中发现，有时候不会去写 prd 的，一个明确的需求就直接拆分任务了。这两个技能拆分是有道理的。

### [](https://linux.do/t/topic/2296905#p-18588878-h-14)为啥用这

superpowers、trellis 等这些其实都用过，有个共同的特点就是流程控制比较强，或者说比较重，穷鬼最喜欢省 token 了。

___

### [](https://linux.do/t/topic/2296905#p-18588878-h-15)示例

举一个简单的例子来走完 grill-with-docs → to-prd → to-issues → tdd 这一套流程。这里先说明一下，我用的不是原版的 matt pocock 的技能，我是在他的基础上自己修改了一套，主要是强化了文档的交接等，所以截图中的链路是这样的：clarify → spec → slice → tdd。

#### [](https://linux.do/t/topic/2296905#p-18588878-grill-with-docs-16)grill-with-docs

我自己做了一个简单的翻译小工具 TinyTrans，它现在的托盘菜单长这样。我认为它很丑，我想改掉。  

[![0](https://cdn3.ldstatic.com/original/4X/a/2/e/a2e63a7055e8a77cc57fd3542844cf61252b2e19.png)

0260×246 3.48 KB

](https://cdn3.ldstatic.com/original/4X/a/2/e/a2e63a7055e8a77cc57fd3542844cf61252b2e19.png "0")

于是，我直接来一句经典甲方语录。  
“I want to optimize the right-click menu; it looks very ugly right now. Clarify it.”

[![1](https://cdn3.ldstatic.com/original/4X/2/b/b/2bbecda0a57814fa90f6bbd14bf0b2989bdd2327.png)

11730×924 32.3 KB

](https://cdn3.ldstatic.com/original/4X/2/b/b/2bbecda0a57814fa90f6bbd14bf0b2989bdd2327.png "1")

然后，就开始拷问你了。这里因为是演示，所以我全程一路 Accept，全部同意了它的建议。

[![2](https://cdn3.ldstatic.com/original/4X/7/9/2/7921391f3bcf342c760afe3d53b53e7c47b36c8a.png)

21730×924 36.9 KB

](https://cdn3.ldstatic.com/original/4X/7/9/2/7921391f3bcf342c760afe3d53b53e7c47b36c8a.png "2")

然后它就问了几个问题。其实这个需求提得很变态，正常来说你稍微有点自己的想法，就会拷问得更多的。

[![3](https://cdn3.ldstatic.com/original/4X/6/e/2/6e2785bebc7973782a526f895ae27b73ee402cc6.png)

31730×924 30.2 KB

](https://cdn3.ldstatic.com/original/4X/6/e/2/6e2785bebc7973782a526f895ae27b73ee402cc6.png "3")

#### [](https://linux.do/t/topic/2296905#p-18588878-to-prd-17)to-prd

一旦拷问完成了，这意味着你和 LLM 就 “达成共识” 了，这是前文提到的很重要的一点，也是我认为的 grill 系列技能的核心。但这个时候，你跟 LLM 的共识是在当前对话形成的，这其实很有必要形成文档，所以接下来就是形成 prd。  
接下来的操作我就很傻瓜了，我全程跟着 LLM 的提示走。  
这里也说明了一下，我自己魔改了技能强化了下一步推荐，原版没有这么强的关联性，能力强的模型比如 GPT-5.5 是能做到，但我自己实测下来，D 老师的下一步推荐在原版上不是那么好使。  

[![4](https://cdn3.ldstatic.com/original/4X/0/c/1/0c1b5d1f9d3e7d9612917f488290e3d1fa7ff958.png)

41730×924 18.9 KB

](https://cdn3.ldstatic.com/original/4X/0/c/1/0c1b5d1f9d3e7d9612917f488290e3d1fa7ff958.png "4")

[![5](https://cdn3.ldstatic.com/original/4X/0/5/1/0512f46ccb4315c321290d5a0f891fe12e81b285.png)

51730×924 34.8 KB

](https://cdn3.ldstatic.com/original/4X/0/5/1/0512f46ccb4315c321290d5a0f891fe12e81b285.png "5")

然后，这里有的佬友就要问啦，哎呀，我这个 spec 或者 prd 要不要自己审查一遍啊？  
我建议你审！但是我不审，因为我懒。  
另外还有一个原因，还是那四个字 “达成共识”，本质上这个 spec 或 prd 就是你跟 LLM 对话的总结，我反正是达不到 LLM 的总结能力的。 ![:zany_face:](https://cdn.ldstatic.com/images/emoji/twitter/zany_face.png?v=15 ":zany_face:")

#### [](https://linux.do/t/topic/2296905#p-18588878-to-issues-18)to-issues

当你审查完了 prd，就要开始拆分任务或者原版中的 issue 了。  

[![6](https://cdn3.ldstatic.com/original/4X/7/2/0/7201c4d3726c83d817ec73720cd2d116be7380d3.png)

61730×924 33.2 KB

](https://cdn3.ldstatic.com/original/4X/7/2/0/7201c4d3726c83d817ec73720cd2d116be7380d3.png "6")

这里唯一需要注意的就是，你需要看一下是不是做了垂直切片。当然啊，这个事情还是具体问题具体分析。横向切片也不是完全不能接受的。

#### [](https://linux.do/t/topic/2296905#p-18588878-tdd-19)tdd

这里就没什么好说了，去干别的事，让 LLM 这个牛马跑就是了。它自己会 RED/GREEN 这种方式去鞭策自己的，过不了就自己打回重做了。狠狠地抽陀螺！ ![:zany_face:](https://cdn.ldstatic.com/images/emoji/twitter/zany_face.png?v=15 ":zany_face:")  

[![7](https://cdn3.ldstatic.com/original/4X/d/c/c/dcc59384075a557bac630100bd80e55997563e6e.png)

71730×924 36.8 KB

](https://cdn3.ldstatic.com/original/4X/d/c/c/dcc59384075a557bac630100bd80e55997563e6e.png "7")

[![8](https://cdn3.ldstatic.com/optimized/4X/a/f/5/af5594a0a3d0362c575ee0b9553cd391e0886651_2_690x368.png)

81730×924 60.3 KB

](https://cdn3.ldstatic.com/original/4X/a/f/5/af5594a0a3d0362c575ee0b9553cd391e0886651.png "8")

最后的成品是这样的。额，D 老师的品味一言难尽。 ![:zany_face:](https://cdn.ldstatic.com/images/emoji/twitter/zany_face.png?v=15 ":zany_face:")

[![9](https://cdn3.ldstatic.com/original/4X/4/2/0/420179ebee8bcf9afb32da88751d13bce68999a8.png)

9270×138 4 KB

](https://cdn3.ldstatic.com/original/4X/4/2/0/420179ebee8bcf9afb32da88751d13bce68999a8.png "9")

## [](https://linux.do/t/topic/2296905#p-18588878-h-20)写在最后

我认为现在的工作流构建什么的始终都是过渡产品。人总是懒惰的，等后续 LLM 的继续发展，这部分工作肯定是越来越少，希望这个过渡期短一点吧。
