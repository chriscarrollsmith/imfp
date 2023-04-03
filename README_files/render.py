import os
import re
import nbconvert
import nbformat

def remove_scoped_styles(markdown_content):
    style_pattern = re.compile(r'<style scoped>.*?</style>', re.DOTALL)
    return style_pattern.sub('', markdown_content)

def replace_png_links(markdown_content):
    png_pattern = re.compile(r'!\[png\]\(.*?\.png\)', re.DOTALL)
    return png_pattern.sub('![png](README_files/plot.png)', markdown_content)

def convert_notebook_to_markdown(input_file, output_file):
    # Read the notebook
    with open(input_file, 'r', encoding='utf-8') as f:
        nb_content = f.read()

    # Parse the notebook content
    notebook = nbformat.reads(nb_content, as_version=4)

    # Convert the notebook to Markdown using the nbconvert module
    markdown_exporter = nbconvert.MarkdownExporter()
    markdown_output, _ = markdown_exporter.from_notebook_node(notebook)

    # Remove scoped styles
    markdown_output = remove_scoped_styles(markdown_output)

    # Replace .png links
    markdown_output = replace_png_links(markdown_output)

    # Write the result to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_output)

if __name__ == "__main__":
    script_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_path)
    
    input_file = os.path.join(project_root, "README.ipynb")
    output_file = os.path.join(project_root, "README.md")

    convert_notebook_to_markdown(input_file, output_file)
    print(f"Notebook {input_file} converted to Markdown {output_file}")