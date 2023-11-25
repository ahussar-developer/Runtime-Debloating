#!/usr/bin/env python3
import argparse


def compare_files(file1_path, file2_path, unique_only=False, common_only=False, output_file=None):
    # Read function names from the first file
    # Read function names from the first file
    with open(file1_path, 'r') as file1:
        functions_file1 = set(line.strip() for line in file1)

    # Read function names from the second file
    with open(file2_path, 'r') as file2:
        functions_file2 = set(line.strip() for line in file2)

    if not unique_only and not common_only:
        print("Error: Either -unique or -common must be specified.")
        return
    
    if unique_only:
        # Find functions that are unique to each file
        unique_functions_file1 = functions_file1 - functions_file2
        unique_functions_file2 = functions_file2 - functions_file1

        if not output_file:
            # Print the differences to the terminal
            print(file1_path + ":")
            for function_name in sorted(unique_functions_file1):
                print(function_name)
            print()
            print(file2_path + ":")
            for function_name in sorted(unique_functions_file2):
                print(function_name)
        else:
            # Write the unique functions from file2 to the output file
            with open(output_file, 'w') as output:
                for function_name in sorted(unique_functions_file2):
                    output.write(f"{function_name}\n")
                    
    if common_only:
        # Find functions that are common to both files
        common_functions = functions_file1.intersection(functions_file2)

        # Print the common functions to the terminal
        print("Common Functions:")
        for function_name in sorted(common_functions):
            print(function_name)

def main():
    #file1_path = '/home/user/test/nginx-1.24.0/ORIGINAL_FUNC_TRACE.txt'
    #file2_path = '/home/user/test/nginx-1.24.0/parsed_orig-del-output.txt'
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Compare function names between two files.\nOutput to STDOUT.')

    # Define command-line arguments
    parser.add_argument('-file1', metavar='file1', required=True, type=str, help='Path to the first file.')
    parser.add_argument('-file2', metavar='file2', required=True, type=str, help='Path to the second file.')
    parser.add_argument('-unique', action='store_true', help='Print functions unique to each file.')
    parser.add_argument('-common', action='store_true', help='Print functions common to both files.')
    parser.add_argument('-output', metavar='output', type=str, help='Path to the output file for functions unique to file2.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the function to compare files with the provided arguments
    compare_files(args.file1, args.file2, args.unique, args.common, args.output)

if __name__ == "__main__":
    main()