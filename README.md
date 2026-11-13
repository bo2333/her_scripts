# 所有脚本支持 -help 参数获取用法,添加脚本需要身下面表添加说明
- 目录：以相对路径， 这是软连接的目录,所有工具必须参数化的灵活性

## 目录结构
```text
~/Public/                    # 根目录 
├── external_bin             # 可执行公共文件            
├── external_mcp             # mcp公共目录
├── external_plugins         # 插件公共目录
├── external_skills          # 技能公共目录 
├── external_scripts         # 脚本公共路径, 本脚本路径
```

## 对应 hermes-agent default目录
```text
~/.hermes/          # 根目录 
├── bin             # 可执行公共文件
├── plugins         # 插件公共目录
├── skills          # 技能公共目录 
├── scripts         # 脚本公共路径, 本脚本路径
```

## 对应 hermes-agent profiles目录
```text
~/.hermes/          # 根目录 
 └── profiles/
      ├── <profile>/
            ├── bin             # 可执行公共文件
            ├── plugins         # 插件公共目录
            ├── skills          # 技能公共目录 
            ├── scripts         # 脚本公共路径, 本脚本路径
```

### ~/Public/external_skills
| 路径| 说明|
|:---|:---|
| profiles/list_profiles.py| 列出 ~/.hermes/profiles 下所有 profile 名字，用于批量处理时获取|
| file/create_symlink.py | 创建或更新软链接 |
| file/remove_symlink.py| 判断指定位置是否为软链接，是则删除。|
| plugin/symlink_install_plugin.py| 软连接方式导入插件|
| plugin/copy_install_plugin.py | 插件安装方式2，不能直接软链接的插件,方式1：plugin/symlink_install_plugin.py |
| plugin/clean_plugin.py| 删除（禁用并移除）hermes-agent 插件。|
| plugin/init_plugin.py| 执行插件的额外初始化脚本。|
| skills/symlink_install_skills.py| 软连接方式导入技能|
| skills/copy_install_skills.py | 技能安装方式2，不能直接软链接的技能,方式1：skills/symlink_install_skills.py |
| skills/clean_skills.py| 删除（禁用并移除）hermes-agent 技能。|
| skills/init_skills.py| 执行技能的额外初始化脚本。|
