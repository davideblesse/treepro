import click
import questionary
import os
import pyperclip
from .tree import (
    get_all_items,
    gather_selected_files,
    get_full_project_tree_text,
    get_full_project_tree_json,
    get_full_project_tree_yaml,
)

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
def treepro(directory, output, file_flag):
    """
    Recursively lists all files/folders (ignoring .gitignore) and outputs a structured summary.
    """
    # 1) Determine if the 'directory' argument is actually an output filename
    if file_flag:
        # if the string 'directory' actually exists as a folder, we use it as the directory:
        if os.path.isdir(directory):
            project_dir = directory
            output_file = file_flag
        else:
            # otherwise, treat it as a filename and use the current directory
            project_dir = "."
            output_file = directory
    else:
        # no -f: directory MUST exist
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

    selected = questionary.checkbox(
        "Select items (use space to toggle):",
        choices=choices
    ).ask()
    if not selected:
        echo_and_capture("No items selected.")
        return

    selected_files = gather_selected_files(items, selected)
    echo_and_capture("\nSELECTED FILES:")
    for p in sorted(selected_files):
        echo_and_capture(f"- {os.path.relpath(p, project_dir)}")
        
    # 4) content of the selected files
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
    
    # 5) copy to clipboard (include project structure + selected content)
    try:
        clipboard_text = "\n".join(output_lines) \
                       + "\n\nCONTENT OF SELECTED FILES:\n" \
                       + content
        pyperclip.copy(clipboard_text)
        echo_and_capture("\nContents of project structure + selected files copied to clipboard.")
    except pyperclip.PyperclipException as e:
        echo_and_capture(f"\nFailed to copy to clipboard: {e}")

        
    # 6) saving to file (if requested)
    if output_file:
        # if it is not an absolute path, we place it in the cwd
        if not os.path.isabs(output_file):
            output_file = os.path.join(os.getcwd(), output_file)
        full = "\n".join(output_lines) + "\n\nCONTENT OF SELECTED FILES:\n" + content
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full)
        echo_and_capture(f"\nContents of selected files saved to: {output_file}")


if __name__ == "__main__":
    treepro()
