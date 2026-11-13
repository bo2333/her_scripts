# 所有脚本支持 -help 参数获取用法,添加脚本需要身下面表添加说明
- 目录：以相对路径， 这是软连接的目录,所有工具必须参数化的灵活性

| 路径| 说明|
|:---|:---|
| file/create_symlink.py | 创建或更新软链接 |
| file/remove_symlink.py| 判断指定位置是否为软链接，是则删除。|
| plugin/copy_install_plugin.py | 插件安装方式2，不能直接软链接的插件,方式1：file/create_symlink.py |
| plugin/clean_plugin.py| 删除（禁用并移除）hermes-agent 插件。|
| plugin/init_plugin.py| 执行插件的额外初始化脚本。|
| profiles/list_profiles.py| 列出 ~/.hermes/profiles 下所有 profile 名字，用于批量处理时获取|
