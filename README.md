# 所有脚本支持 -help 参数获取用法,添加脚本需要身下面表添加说明
- 目录：以相对路径， 这是软连接的目录,所有工具必须参数化的灵活性

## 公共目录结构
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


### 目录布局
```text
~/Public/external_scripts/          # 脚本根（README 那节标题）
├── file/
│   ├── create_symlink.py
│   ├── remove_symlink.py
│   ├── sync_dir.py
│   └── hermes_paths.py          
├── profiles/
│   └── list_profiles.py
├── plugin/
│   ├── symlink_install_plugin.py
│   ├── copy_install_plugin.py
│   ├── clean_plugin.py
│   └── init_plugin.py
├── skills/
│   ├── symlink_install_skills.py
│   ├── copy_install_skills.py
│   ├── clean_skills.py
│   └── init_skills.py
├── doctor/                       # 新增
│   ├── check_deps.py
│   └── doctor.py
├── gc/                           # 新增
│   ├── scan.py
│   └── clean.py
└── bin/                           
    ├── symlink_install_bin.py
    ├── copy_install_bin.py
    ├── clean_bin.py
    └── init_bin.py
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
| bin/symlink_install_bin.py | 软链接方式安装可执行文件（源可为文件或目录） |
| bin/copy_install_bin.py    | 复制方式安装可执行文件（保留可执行位与符号链接） |
| bin/clean_bin.py           | 卸载可执行文件（直接删除，不触碰源目录） |
| bin/init_bin.py            | 在 bin 目录执行安装后初始化脚本 |
| doctor/check_deps.py | 检查 Python / hermes CLI / rsync / git 依赖 |
| doctor/doctor.py | 扩展环境体检：悬空链接、孤儿、可执行位、目录结构 |
| gc/scan.py | 扫描垃圾项（悬空链接 / 孤儿 / 结构异常），只读 |
| gc/clean.py | 清理悬空链接与孤儿（只删目标侧，invalid 仅报告） |
| file/hermes_paths.py | 共享路径与 profile 工具库（供 doctor/gc/manifest/batch 使用） |
