import os
import json
import pathspec
from rich.tree import Tree
from rich.console import Console
import yaml

def load_gitignore(base_dir):
    gitignore_path = os.path.join(base_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
        return spec
    return None

def collect_items(directory, base_dir, spec, depth=0, counter=None):
    if counter is None:
        counter = [1]
    items = {}
    try:
        entries = sorted(os.listdir(directory))
    except PermissionError:
        return items

    for entry in entries:
        # Skip files and directories starting with a dot
        if entry.startswith("."):
            continue
        
        full_path = os.path.join(directory, entry)
        rel_path = os.path.relpath(full_path, base_dir)
        check_path = rel_path + "/" if os.path.isdir(full_path) else rel_path
        if spec and (spec.match_file(rel_path) or spec.match_file(check_path)):
            continue

        num = counter[0]
        counter[0] += 1
        items[num] = {"path": full_path, "is_dir": os.path.isdir(full_path), "depth": depth}

        if os.path.isdir(full_path):
            child_items = collect_items(full_path, base_dir, spec, depth=depth+1, counter=counter)
            items.update(child_items)

    return items


def get_all_items(directory="."):
    spec = load_gitignore(directory)
    return collect_items(directory, directory, spec)

def gather_selected_files(items, selected_numbers):
    selected_files = set()
    for num in selected_numbers:
        item = items.get(num)
        if not item:
            continue
        if item["is_dir"]:
            parent_path = item["path"]
            for other in items.values():
                if not other["is_dir"] and other["path"].startswith(os.path.join(parent_path, "")):
                    selected_files.add(other["path"])
        else:
            selected_files.add(item["path"])
    return selected_files

def get_project_structure_tree(directory):
    spec = load_gitignore(directory)
    root = Tree(os.path.basename(os.path.abspath(directory)))  # Root directory name

    def add_nodes(parent_node, current_dir):
        try:
            entries = sorted(os.listdir(current_dir))
        except PermissionError:
            return
        
        for entry in entries:
            # Exclude hidden/system files and directories
            if entry.startswith(".") or entry in {"dist", "build", "__pycache__"}:
                continue

            full_path = os.path.join(current_dir, entry)
            rel_path = os.path.relpath(full_path, directory)
            check_path = rel_path + "/" if os.path.isdir(full_path) else rel_path
            if spec and (spec.match_file(rel_path) or spec.match_file(check_path)):
                continue

            if os.path.isdir(full_path):
                branch = parent_node.add(f"{entry}/")
                add_nodes(branch, full_path)
            else:
                parent_node.add(entry)

    add_nodes(root, directory)
    return root



def get_full_project_tree_text(directory):
    root = get_project_structure_tree(directory)
    console = Console(record=True)
    with console.capture() as capture:
        console.print(root)
    tree_text = capture.get()
    return tree_text

def get_project_tree_dict(directory, base_dir=None):
    if base_dir is None:
        base_dir = directory
    spec = load_gitignore(base_dir)
    tree = {
        "name": os.path.basename(os.path.abspath(directory)),  # Show the actual directory name
        "type": "directory",
        "children": []
    }
    try:
        entries = sorted(os.listdir(directory))
    except PermissionError:
        return tree

    for entry in entries:
        full_path = os.path.join(directory, entry)
        rel_path = os.path.relpath(full_path, base_dir)
        check_path = rel_path + "/" if os.path.isdir(full_path) else rel_path
        if spec and (spec.match_file(rel_path) or spec.match_file(check_path)):
            continue
        if os.path.isdir(full_path):
            tree["children"].append(get_project_tree_dict(full_path, base_dir))
        else:
            tree["children"].append({
                "name": entry,
                "type": "file"
            })
    return tree

def get_full_project_tree_json(directory):
    tree_dict = get_project_tree_dict(directory)
    return json.dumps(tree_dict, indent=2)

def get_full_project_tree_yaml(directory):
    tree_dict = get_project_tree_dict(directory)
    return yaml.dump(tree_dict, default_flow_style=False, sort_keys=False)

""" PROVA PULL REQUEST! """