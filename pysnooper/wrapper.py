# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import sys
import os
import subprocess

#TODO: Pass the arguments to the file_snoop 

# Define the snoop code to be prepended to the original code
snoop_code = """import pysnooper
pysnooper.snoop().__enter__()
"""

def assertions():
    assert len(sys.argv) >1, "Usage: python <script> <file path> <file arguments>"
    
def read_file(file_path) -> str:
    try:
        with open(file_path) as f:
            file_text = f.read()
        return file_text
    except IOError:
        print(f"Error: Reading {file_path}")
        sys.exit(1)

def write_file(file_path, text):
    try:
        with open(file_path, 'w') as f:
            f.write(text)
    except IOError:
        print(f"Error: Writing {file_path}")
        sys.exit(1)
        
def remove_file(file_path):
    try:
        os.remove(file_path)
    except IOError:
        print(f"Error: Removing {file_path}")
        sys.exit(1)
    
def run_code(file_path): 
    try:
            subprocess.run(["python3", file_path])
    except IOError:
        print(f"Error: Reading {file_path}")
        sys.exit(1)

    
def snoop_wrapper():
    file_path = sys.argv[2]
    temp_file_path = file_path[:-3] + "_snoop.py"
    #Write the snoop code to a temp file
    original_code = read_file(file_path)
    new_code = snoop_code + original_code
    write_file(temp_file_path, new_code)
    
    #Run the temp file
    run_code(temp_file_path)
    
    #Remove the temp file
    remove_file(temp_file_path)
