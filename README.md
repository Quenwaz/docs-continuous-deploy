# docs-continuous-deploy

该仓库定义为文档持续发布平台。该文档库是基于markdown的， 得益于[docsify](https://github.com/docsifyjs/docsify)提供的前端框架， 使得后端只需专注于markdown文档的编写， 无需关心Web端如何渲染。

核心脚本为**server.py**， 该脚本完成三件事:
- 提供webhook钩子， 拉取指定git仓库的markdown
- 将拉取的markdown目录结构， 动态构建前端所需的侧边栏`_sidebar.md`
- 提供静态文件服务， 结合基础的权限管理

其中`wiki`目录用于存储markdown文件

