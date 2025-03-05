import click
import questionary
import os
from .tree import (
    get_all_items,
    gather_selected_files,
    get_full_project_tree_text,
    get_full_project_tree_json,
    get_full_project_tree_yaml,
)

@click.command()
@click.argument("directory", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output", "-o", 
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False), 
    default="text", 
    help="Output format: text (default), json, or yaml."
)
@click.option(
    "-f", "--file",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    flag_value="treepro.txt",
    help=("Save complete output to a file. Use -f alone to use the default filename "
          "'treepro.txt', or -f <filename.txt> to override the default.")
)
def treepro(directory, output, file):
    """
    Recursively lists all files/folders (ignoring .gitignore) and outputs a structured summary.
    
    The output consists of:
      - PROJECT STRUCTURE (in the chosen format)
      - A list of SELECTED FILES (via interactive selection)
      - CONTENT OF SELECTED FILES
    """
    # Local capture list so that each command run is independent.
    output_lines = []

    def echo_and_capture(message=""):
        """Prints a message to the console and saves it for later file output."""
        click.echo(message)
        output_lines.append(message)

    # [1] Generate the project structure output in the chosen format.
    if output == "json":
        project_structure_text = get_full_project_tree_json(directory)
    elif output == "yaml":
        project_structure_text = get_full_project_tree_yaml(directory)
    else:
        project_structure_text = get_full_project_tree_text(directory)
    
    echo_and_capture("PROJECT STRUCTURE :")
    echo_and_capture(project_structure_text)
    
    # [2] Interactive selection.
    items = get_all_items(directory)
    if not items:
        echo_and_capture("No files found (or all files are ignored).")
        return

    choices = []
    for num in sorted(items.keys()):
        item = items[num]
        indent = "    " * item["depth"]
        base_name = os.path.basename(item["path"])
        title = f"{num}: {indent}{base_name}" + ("/" if item["is_dir"] else "")
        choices.append(questionary.Choice(title=title, value=num))
    
    selected_numbers = questionary.checkbox(
        "Select items (use space to toggle selection):",
        choices=choices
    ).ask()

    if not selected_numbers:
        echo_and_capture("No items selected.")
        return

    # [3] Compute the selected files.
    selected_files = gather_selected_files(items, selected_numbers)

    echo_and_capture("\nSELECTED FILES:")
    for file_path in sorted(selected_files):
        rel_path = os.path.relpath(file_path, directory)
        echo_and_capture(f"- {rel_path}")

    echo_and_capture("\nCONTENT OF SELECTED FILES:")
    for file_path in sorted(selected_files):
        rel_path = os.path.relpath(file_path, directory)
        echo_and_capture(f"\n--- {rel_path} ---")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            echo_and_capture(content)
        except Exception as e:
            echo_and_capture(f"Error reading file {rel_path}: {e}")

    # [4] Write complete output to file if -f was provided.
    if file:
        # If the file path is relative, place it in the current working directory.
        if not os.path.isabs(file):
            file = os.path.join(os.getcwd(), file)
        with open(file, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        echo_and_capture(f"\nOutput also written to file: {file}")

if __name__ == "__main__":
    treepro()
