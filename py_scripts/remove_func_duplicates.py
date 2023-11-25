input_file_path = '/home/user/passes/missed_runtime_funcs.log'
output_file_path = '/home/user/passes/unique_missed_runtime_funcs.log'

unique_function_names = set()

with open(input_file_path, 'r') as input_file:
    for line in input_file:
        function_name = line.strip()  # Remove leading and trailing whitespaces
        unique_function_names.add(function_name)

# Write the unique function names to the output file
with open(output_file_path, 'w') as output_file:
    for function_name in sorted(unique_function_names):
        output_file.write(f"{function_name}\n")
