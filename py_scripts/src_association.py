#!/usr/bin/env python3
import os
import subprocess
from itertools import chain
import argparse

def generate_tags(folder_path):
    # Run ctags to generate a tags file
    subprocess.run(['ctags', '-R', folder_path])

def extract_functions_from_tags(tags_path):
    function_dict = {}

    with open(tags_path, 'r') as tags_file:
        lines = tags_file.readlines()

    for line in lines:
        # Split line by tabs or spaces
        items = line.split('\t')  # Assuming tabs are used as separators, change to ' ' if spaces are used

        if len(items) >= 2:
            function_name, file_path = items[:2]
            if file_path.endswith('.c'):
                if function_name not in function_dict:
                        function_dict[function_name] = []
                
                function_dict[function_name].append(file_path)

    return function_dict

def match_functions_with_list(function_dict, function_list):
    matched_functions = {}

    for func_name in function_list:
        if func_name in function_dict:
            matched_functions[func_name] = function_dict[func_name]

    return matched_functions

def read_function_list(file_path):
    with open(file_path, 'r') as file:
        # Read function names from each line
        function_list = [line.strip() for line in file.readlines()]

    return function_list

def flatten_list(lst):
    """Flatten a list of lists."""
    return [item for sublist in lst for item in sublist]


def main():
    #folder_path = '/home/user/test/nginx-1.24.0/src/'
    #pin_funcs_file = "/home/user/passes/pass_files/orig_nginx_pin.log"
    #llvm_runtime_funcs = "/home/user/test/nginx-1.24.0/ORIGINAL_FUNC_TRACE.txt"
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract and match functions from source files using ctags. It also outputs src_assoc_py_matched_funcs.txt'
                                     'which contains all extra functions not in the traces found in all the utilized c files from the source.')

    # Define command-line arguments
    parser.add_argument('-src-dir', dest='folder_path', required=True, help='Path to the source code directory.')
    parser.add_argument('-pin-trace', dest='pin_funcs_file', required=True, help='Path to the PIN trace file.')
    parser.add_argument('-llvm-trace', dest='llvm_runtime_funcs', required=True, help='Path to the LLVM runtime trace file.')

    # Parse the command-line arguments
    args = parser.parse_args()
    
    tags_path = '/home/user/passes/py_scripts/tags'

    # Generate tags file using ctags
    generate_tags(args.folder_path)

    # Extract functions from the tags file
    function_dict = extract_functions_from_tags(tags_path)
    #for f, path in function_dict.items():
        #print(f)
    
    # List of functions to match
    function_list_1 = read_function_list(args.pin_funcs_file)
    #print(function_list_1)
    function_list_2 = read_function_list(args.llvm_runtime_funcs)
    #print(function_list_2)
    
    # Match functions from the first file with their corresponding source files
    matched_functions_1 = match_functions_with_list(function_dict, function_list_1)

    # Match functions from the second file with their corresponding source files
    matched_functions_2 = match_functions_with_list(function_dict, function_list_2)

    # Flatten the lists of file paths from function_dict
    all_file_paths = flatten_list(function_dict.values())

    # Create a set of all unique file paths
    unique_files_all = set(all_file_paths)
    functions_by_file = {}
    unused_files = []
    
    # Print all functions associated with each unique file path
    print("All functions associated with each unique file path:")
    for file_path in unique_files_all:
        functions_for_file = [func for func, paths in chain(matched_functions_1.items(), matched_functions_2.items()) if file_path in paths]
        if functions_for_file:
            functions_by_file[file_path] = functions_for_file
            #print(f"{file_path}:\n\t{', '.join(functions_for_file)}")
        else:
            unused_files.append(file_path)

    # Files from the original function_dict that were not used
    #print("\nFiles from the original function_dict that were not used:")
    #for file_path in unused_files:
        #print(file_path)

    all_functions = []
    for file_path, functions_for_file in functions_by_file.items():
        for func, paths in function_dict.items():
            if file_path in paths:
                all_functions.append(func)
                #print(func)

    all_functions = set(all_functions)
    func1_set = set(matched_functions_1)
    func2_set = set(matched_functions_2)
    
    filtered_functions = all_functions - (func1_set.union(func2_set))
    
    with open('src_assoc_py_matched_funcs.txt', 'w') as enable_file:
        enable_file.write('\n'.join(filtered_functions))

if __name__ == "__main__":
    main()