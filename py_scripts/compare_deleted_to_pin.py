def read_function_names(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def compare_function_lists(file1_path, file2_path, output_file):
    deleted_log = set(read_function_names(file1_path))
    pin_log = set(read_function_names(file2_path))

    common_functions = deleted_log.intersection(pin_log)

    if common_functions:
        with open(output_file, 'a') as of:
            for function in common_functions:
                of.write(function + "\n")
    else:
        print("No common functions found.")
    
    return

if __name__ == "__main__":
    deleted_log = "/home/user/passes/deleted_functions.log"  # Replace with the actual path of your first file
    pin_log = "/home/user/passes/modified_nginx_pin2.log"  # Replace with the actual path of your second file
    output_file = "/home/user/passes/missed_runtime_funcs_test.log"

    compare_function_lists(deleted_log, pin_log, output_file)

    
