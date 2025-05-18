import click
import questionary
import os
import pyperclip
import yaml
from .tree import (
    get_all_items,
    gather_selected_files,
    get_full_project_tree_text,
    get_full_project_tree_json,
    get_full_project_tree_yaml,
)

# Configuration storage
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "treepro")
CONFIG_FILE = os.path.join(CONFIG_DIR, "configs.yaml")

def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_configs():
    ensure_config_dir()
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("configs", {})

def save_configs(configs):
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump({"configs": configs}, f)

@click.command()
@click.argument(
    "directory",
    default=".",
    # allow directory to be a file name, in this case, we will use the current directory
    type=click.Path(exists=False, file_okay=False)
)
@click.option(
    "--output", "-o",
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
    default="text",
    help="Output format: text (default), json, or yaml."
)
@click.option(
    "-f", "--file",
    "file_flag",
    # it is a flag that, if invoked without an argument, defaults to "treepro.txt"
    flag_value="treepro.txt",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help=(
        "Save complete output to a file. "
        "Use `-f` to write in `treepro.txt`, or `-f <filename>` to specify a different name."
    )
)
@click.option(
    "-c", "--config",
    "config_name",
    help="Usa una configurazione salvata per la selezione."
)
@click.option(
    "--edit-config",
    is_flag=True,
    help="Dopo il caricamento di --config, riapre l'interattivo per modificarla."
)
@click.option(
    "--save-config",
    "save_config_name",
    help="Salva la selezione corrente in un nuovo profilo."
)
def treepro(directory, output, file_flag, config_name, edit_config, save_config_name):
    """
    Recursively lists all files/folders (ignoring .gitignore) and outputs a structured summary.
    """
    # 1) Determine if the 'directory' argument is actually an output filename
    if file_flag:
        if os.path.isdir(directory):
            project_dir = directory
            output_file = file_flag
        else:
            project_dir = "."
            output_file = directory
    else:
        if not os.path.isdir(directory):
            raise click.ClickException(f"Directory '{directory}' does not exist.")
        project_dir = directory
        output_file = None

    # buffer to later save/display on screen
    output_lines = []
    def echo_and_capture(msg=""):
        click.echo(msg)
        output_lines.append(msg)

    # 2) project structure
    if output == "json":
        project_text = get_full_project_tree_json(project_dir)
    elif output == "yaml":
        project_text = get_full_project_tree_yaml(project_dir)
    else:
        project_text = get_full_project_tree_text(project_dir)

    echo_and_capture("PROJECT STRUCTURE :")
    echo_and_capture(project_text)
    
    # Load existing configurations
    configs = load_configs()
    preset = []
    if config_name:
        if config_name not in configs:
            raise click.ClickException(f"Configurazione '{config_name}' non trovata.")
        preset = configs[config_name].get("items", [])

    # 3) interactive selection
    items = get_all_items(project_dir)
    if not items:
        echo_and_capture("No files found (or all files are ignored).")
        return

    choices = []
    for num in sorted(items.keys()):
        item = items[num]
        indent = "    " * item["depth"]
        name = os.path.basename(item["path"])
        title = f"{num}: {indent}{name}" + ("/" if item["is_dir"] else "")
        choices.append(questionary.Choice(title=title, value=num))

    # Decide whether to use preset or open interactive checkbox
    if config_name and not edit_config:
        selected = preset
        echo_and_capture(f"Using configuration '{config_name}': {selected}")
    else:
        # Only pass default if preset is not empty
        if preset:
            selected = questionary.checkbox(
                "Select items (use space to toggle):",
                choices=choices,
                default=preset
            ).ask()
        else:
            selected = questionary.checkbox(
                "Select items (use space to toggle):",
                choices=choices
            ).ask()

    if not selected:
        echo_and_capture("No items selected.")
        return

    # Save new configuration or update existing one
    if save_config_name:
        configs[save_config_name] = {"items": selected}
        save_configs(configs)
        echo_and_capture(f"Configurazione '{save_config_name}' salvata.")
    if config_name and edit_config:
        configs[config_name] = {"items": selected}
        save_configs(configs)
        echo_and_capture(f"Configurazione '{config_name}' aggiornata.")

    # 4) gather and display selected files
    selected_files = gather_selected_files(items, selected)
    echo_and_capture("\nSELECTED FILES:")
    for p in sorted(selected_files):
        echo_and_capture(f"- {os.path.relpath(p, project_dir)}")
        
    # 5) content of the selected files
    parts = []
    for p in sorted(selected_files):
        rel = os.path.relpath(p, project_dir)
        parts.append(f"\n--- {rel} ---\n")
        try:
            with open(p, "r", encoding="utf-8") as f:
                parts.append(f.read())
        except Exception as e:
            parts.append(f"Error reading {rel}: {e}")

    content = "\n".join(parts)
    
    # 6) copy to clipboard (include project structure + selected content)
    try:
        clipboard_text = "\n".join(output_lines) \
                       + "\n\nCONTENT OF SELECTED FILES:\n" \
                       + content
        pyperclip.copy(clipboard_text)
        echo_and_capture("\nContents of project structure + selected files copied to clipboard.")
    except pyperclip.PyperclipException as e:
        echo_and_capture(f"\nFailed to copy to clipboard: {e}")

        
    # 7) saving to file (if requested)
    if output_file:
        if not os.path.isabs(output_file):
            output_file = os.path.join(os.getcwd(), output_file)
        full = "\n".join(output_lines) + "\n\nCONTENT OF SELECTED FILES:\n" + content
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full)
        echo_and_capture(f"\nContents of selected files saved to: {output_file}")


if __name__ == "__main__":
    treepro()
