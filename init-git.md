### 建立密钥
```
mkdir -p ~/.ssh
cp  ~/Public/id_ed25519 ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519
```




### 一次性部署
```shell
# 1. 允许向"已 checkout 的主副本"push，并自动更新工作树
cd ~/Public/external_scripts
git config receive.denyCurrentBranch updateInstead

# 2. 部署 post-receive hook
mkdir -p .git/hooks
cp file/hooks/post-receive .git/hooks/post-receive
```

### 设置文件属性
```
cd ~/Public/external_scripts
chmod +x .git/hooks/post-receive

# 3. 给 sync_push.sh 加执行位（如果 clone 没带过来）
chmod +x file/sync_push.sh
```

### 设置全局名字
```shell
git config --global user.name  "hermes1"
git config --global user.email "root@hermes1.local"

# 验证
git config --global --list | grep user
# user.name=hermes1
# user.email=root@hermes1.local

git log -1 --format='%an <%ae>'
# hermes1 <root@hermes1.local>
```

### clone
```shell
git clone ~/Public/external_scripts ~/.hermes/scripts
cd ~/.hermes/scripts
chmod +x file/sync_push.sh

# 提交
git push origin main

# 拉取
git pull origin main
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

### 切 remote 到 SSH
```
cd ~/Public/external_scripts
git remote set-url origin git@github.com:bo2333/hermes_scripts.git
git remote -v          # 确认是 git@github.com:...
git push origin main   # 静默完成，不再提示密码
```

