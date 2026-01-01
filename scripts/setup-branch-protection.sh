#!/bin/bash
# 设置 main 分支保护规则的脚本
# 需要安装 GitHub CLI (gh) 并已登录

set -e

BRANCH="main"
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "🔒 正在为 $REPO 的 $BRANCH 分支设置保护规则..."
echo ""

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ 错误: 请先使用 'gh auth login' 登录 GitHub"
    exit 1
fi

# 设置分支保护规则
gh api repos/$REPO/branches/$BRANCH/protection \
  --method PUT \
  --field required_status_checks=null \
  --field enforce_admins=false \
  --field required_pull_request_reviews[required_approving_review_count]=1 \
  --field required_pull_request_reviews[dismiss_stale_reviews]=true \
  --field required_pull_request_reviews[require_code_owner_reviews]=false \
  --field required_pull_request_reviews[require_last_push_approval]=false \
  --field restrictions=null \
  --field required_linear_history=false \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field block_creations=false \
  --field required_conversation_resolution=true \
  --field lock_branch=false \
  --field allow_fork_syncing=false

echo "✅ 成功为 $BRANCH 分支设置了保护规则！"
echo ""
echo "📋 已启用的保护规则:"
echo "   ✓ 必须通过 Pull Request 合并"
echo "   ✓ 需要至少 1 个代码审查批准"
echo "   ✓ 禁止强制推送 (force push)"
echo "   ✓ 禁止删除分支"
echo "   ✓ 需要解决所有对话才能合并"
echo ""
echo "💡 提示: 现在 main 分支只能通过 Pull Request 进行更新"
