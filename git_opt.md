### 拉取远端
```shell
cd ~/Public/external_scripts
git pull origin main
```

### 远端
```shell
cd ~/Public/external_scripts
chmod +x file/sync_push.sh

# 提交
git push origin main

# 拉取
git pull origin main
```


### 各环境
```
# 拉取
cd ~/.hermes/scripts
git pull origin main      # 本地路径，本来就不需要认证

# 提交
git push origin main


# 不涉及认证，但同样会遇到 merge 冲突卡住的问题。同样配置：
cd ~/.hermes/scripts
git config pull.ff only
git config core.editor true
```
