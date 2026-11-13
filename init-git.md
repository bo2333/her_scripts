### 一次性部署
```shell
# 1. 允许向"已 checkout 的主副本"push，并自动更新工作树
cd ~/Public/external_scripts
git config receive.denyCurrentBranch updateInstead

# 2. 部署 post-receive hook
mkdir -p .git/hooks
cp file/hooks/post-receive .git/hooks/post-receive
chmod +x .git/hooks/post-receive

# 3. 给 sync_push.sh 加执行位（如果 clone 没带过来）
chmod +x file/sync_push.sh
```


### 验证：
```shell
# 方式 1：在环境里改完后手动补推
cd ~/.hermes/scripts
# ... 改东西 ...
git add -A && git commit -m "fix: xxx"
file/sync_push.sh ~/.hermes/scripts

# 方式 2：直接 push，由 hook 自动补推
cd ~/.hermes/scripts
git push origin main
# 主副本会打印 "[OK] post-receive: 已补推 GitHub (main)" 或 WARN
```