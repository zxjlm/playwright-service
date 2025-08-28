# GitHub CI 工作流说明

## Release Docker 镜像自动构建

本项目配置了自动化的 Docker 镜像构建和发布工作流。当您在 GitHub 上发布新的 release 时，系统会自动构建 Docker 镜像并推送到 DockerHub。

### 工作流触发条件

- 当在 GitHub 上发布新的 release 时自动触发
- 支持语义化版本标签（如 v1.0.0, v2.1.3 等）

### 镜像标签规则

工作流会根据 release 标签自动生成以下镜像标签：

- `{version}` - 完整版本号（如 v1.0.0）
- `{major}.{minor}` - 主次版本号（如 1.0）
- `latest` - 最新版本标签

### 配置要求

在使用此工作流之前，您需要在 GitHub 仓库的 Settings > Secrets and variables > Actions 中配置以下密钥：

1. **DOCKERHUB_USERNAME**: 您的 DockerHub 用户名
2. **DOCKERHUB_TOKEN**: 您的 DockerHub 访问令牌

#### 如何获取 DockerHub 令牌：

1. 登录 [DockerHub](https://hub.docker.com/)
2. 进入 Account Settings > Security
3. 点击 "New Access Token"
4. 为令牌命名（如 "GitHub Actions"）
5. 复制生成的令牌

### 使用方法

1. 确保已配置上述密钥
2. 在 GitHub 上创建新的 release
3. 使用语义化版本标签（如 v1.0.0）
4. 发布 release
5. 工作流将自动运行并推送镜像到 DockerHub

### 镜像名称

镜像将使用以下格式推送到 DockerHub：
```
docker.io/{github-username}/{repository-name}:{tag}
```

例如：`docker.io/yourusername/playwright-service:v1.0.0`

### 注意事项

- 确保 Dockerfile 在项目根目录
- 工作流使用 GitHub Actions 缓存来加速构建
- 支持多架构构建（如果基础镜像支持）
- 构建日志会在 GitHub Actions 中显示
