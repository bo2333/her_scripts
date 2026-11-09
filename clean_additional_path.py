import os
import sys
import argparse


self_des = "删除hermes 指定 agent的 技能|插件|脚本"
self_keywords = {
    "fuzzy": ['删', "删除"],
    "precise": ["删除技能", "删除插件", "删除脚本"]
}

# readme
def get_self_info(t):
    if t == 0:
        return self_des
    elif t == 1:
        return self_keywords



def delete_target_in_subagents(base_dir, rel_path, target_name, dry_run=True):
    """
    遍历 base_dir 下的所有子目录，删除指定相对路径下的目标文件或软链接。
    
    :param base_dir: 子agent主目录 (str)
    :param rel_path: 相对于子agent根目录的路径 (str)，例如 "workspace/logs"
    :param target_name: 要删除的文件名或软链接名 (str)，例如 "error.log"
    :param dry_run: 是否仅为模拟运行，不实际删除 (bool)
    """
    # 1. 验证主目录是否存在
    if not os.path.isdir(base_dir):
        print(f"错误: 主目录不存在或不是目录 -> {base_dir}")
        return

    # 标准化相对路径，去除首尾斜杠，防止拼接错误
    clean_rel_path = rel_path.strip('/')
    
    # 记录统计信息
    found_count = 0
    deleted_count = 0
    error_count = 0

    print(f"--- 开始扫描主目录: {base_dir} ---")
    print(f"   相对路径: {clean_rel_path}")
    print(f"   目标名称: {target_name}")
    print(f"   模式: {'[模拟运行] 不会实际删除' if dry_run else '[实际执行] 将永久删除'}")
    print("-" * 30)

    try:
        # 2. 遍历主目录下的所有条目
        for entry in os.listdir(base_dir):
            sub_agent_path = os.path.join(base_dir, entry)
            
            # 只处理目录（假设每个子目录是一个子agent）
            if not os.path.isdir(sub_agent_path):
                continue
            
            # 3. 拼接完整目标路径
            # 结构: base_dir / sub_agent / rel_path / target_name
            full_target_path = os.path.join(sub_agent_path, clean_rel_path, target_name)
            
            # 4. 检查路径是否存在
            # lexists 比 exists 更好，因为它能检测到指向无效目标的软链接
            if os.path.lexists(full_target_path):
                found_count += 1
                is_link = os.path.islink(full_target_path)
                link_info = " (软链接)" if is_link else " (文件)"
                
                print(f"发现: {full_target_path}{link_info}")
                
                if dry_run:
                    print(f"  -> [跳过] 模拟模式下不删除")
                    deleted_count += 1 # 计数为“待删除”
                else:
                    try:
                        # 5. 执行删除
                        # unlink 可以删除文件和软链接，且对于软链接只删链接本身
                        os.unlink(full_target_path)
                        print(f"  -> [成功] 已删除")
                        deleted_count += 1
                    except PermissionError:
                        print(f"  -> [失败] 权限不足")
                        error_count += 1
                    except Exception as e:
                        print(f"  -> [失败] {e}")
                        error_count += 1
            else:
                # 可选：打印未找到的情况，便于调试
                # print(f"未找到: {full_target_path}")
                pass

    except Exception as e:
        print(f"遍历过程中发生严重错误: {e}")
        return

    print("-" * 30)
    print(f"扫描结束。共发现: {found_count}, 成功处理: {deleted_count}, 错误: {error_count}")

if __name__ == "__main__":
    # 配置参数解析
    parser = argparse.ArgumentParser(description="批量删除 Hermes  子Agent目录下的指定文件/软链接")
    parser.add_argument("--base-dir", required=True, help="子agent的主目录路径")
    parser.add_argument("--rel-path", required=True, help="相对于子agent根目录的路径，如 'logs/temp'")
    parser.add_argument("--target", required=True, help="要删除的文件名或软链接名")
    parser.add_argument("--execute", action="store_true", help="加上此参数才真正执行删除，否则仅为模拟")
    
    args = parser.parse_args()

    # 默认 dry_run=True (安全模式)，除非用户指定 --execute
    is_dry_run = not args.execute
    
    delete_target_in_subagents(
        base_dir=args.base_dir,
        rel_path=args.rel_path,
        target_name=args.target,
        dry_run=is_dry_run
    )
