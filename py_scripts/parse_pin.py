import os

def parse_file(file_path, target_image):
    result = []

    with open(file_path, 'r') as file:
        # Skip the header line
        next(file)

        for line in file:
            procedure, image, address, calls, instructions = line.split()

            if image == target_image:
                #print(line)
                result.append(procedure)

    return result

file_path = '/home/user/test/nginx-1.24.0/proccount.out'
target_image = 'nginx'

procedures = parse_file(file_path, target_image)

output_file = 'nginx_pin.log'
if os.path.exists(output_file):
    os.remove(output_file)
    
with open(output_file, 'a') as new_file:
    for procedure in procedures:
        print(procedure)
        new_file.write(procedure+'\n')
