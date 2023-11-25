file1_path = '/home/user/test/nginx-1.24.0/no-del-running-func-list.txt'
file2_path = '/home/user/passes/py_scripts/orig_nginx_pin.log'

# Read function names from the first file
with open(file1_path, 'r') as file1:
    functions_file1 = set(line.strip() for line in file1)

# Read function names from the second file
with open(file2_path, 'r') as file2:
    functions_file2 = set(line.strip() for line in file2)

# Find functions that are unique to each file
unique_functions_file1 = functions_file1 - functions_file2
unique_functions_file2 = functions_file2 - functions_file1

# Print the differences to the terminal
print(file1_path + ":")
for function_name in sorted(unique_functions_file1):
    print(function_name)
print()
print(file2_path + ":")
for function_name in sorted(unique_functions_file2):
    print(function_name)
