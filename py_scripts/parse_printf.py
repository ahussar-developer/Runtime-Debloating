filename = "/home/user/passes/tmp.log"  # Replace with the actual path to your file

deleted_strings = []

with open(filename, 'r') as file:
    for line in file:
        if " DELETED" in line:
            # Extract the substring before " --"
            deleted_string = line.split("--")[0].strip()
            deleted_strings.append(deleted_string.strip())

# Print the extracted strings
for deleted_string in deleted_strings:
    print(deleted_string)
