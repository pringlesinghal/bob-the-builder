import os

def concatenate_py_files(root_dir, output_file, exclude_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith('.py') and filename != exclude_file:
                    relative_path = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                    outfile.write(f"# File: {relative_path}\n\n")
                    
                    with open(os.path.join(dirpath, filename), 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    
                    outfile.write("\n\n")

# Usage
root_directory = '.'  # Current directory, change this to your project's root directory if needed
output_file = 'all_code.txt'
script_filename = os.path.basename(__file__)  # Get the name of this script

concatenate_py_files(root_directory, output_file, script_filename)
print(f"All Python code (except this script) has been concatenated into {output_file}")
