#!/bin/bash

## BEFORE RUNNING THIS
# You need to run: ./objs/nginx_orig_printf -g 'daemon off;' -p . -c conf/nginx.conf > orig-del-output.log 2>&1
#       from /test/nginx directory
# Run all the tests you need to run to ensure the log contains all functions necessary for current functionality
# look at test_website.sh for some automated methods. You will still need to manually navigate the webiste though.
# This script runs on the orig-del-output.log


pushd /home/user/test/nginx-1.24.0/
## Parse the orig-del-output.log into a list of functions
python3 /home/user/passes/py_scripts/parse_llvm_runtime_log.py -input-file orig-del-output.log -output-file parsed_orig-del-output.txt

## parsed_orig-del-output.txt should now contain all traced functions. Overwrite ORIGINAL_FUNC_TRACE.txt with this file with cp
cp parsed_orig-del-output.txt ORIGINAL_FUNC_TRACE.txt

## Overwrite passes/orig_nginx_llvm.log with ORIGINAL_FUNC_TRACE.txt via cp
cp ORIGINAL_FUNC_TRACE.txt /home/user/passes/pass_files/orig_nginx_llvm.log

popd