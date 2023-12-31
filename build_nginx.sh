#!/bin/bash

function build_pass() {
    echo "======================"
    echo "Building Debloat Pass"
    echo "======================"
    mkdir -p build
    pushd build
    cmake ..
    make -j16
    popd
    echo "----------PASS BUILT----------"; echo; echo;
}

function print_spaces() {
    echo
    echo
    echo
}

## Changes options for server
function configure_nginx(){
    pushd ../test/nginx-1.24.0/
    
    ## Configure NGINX with wanted modules
    export RANLIB=llvm-ranlib
    # Disable opaque pointers for SVF usage
    ./configure --with-pcre --with-http_v2_module --with-http_addition_module --with-http_mp4_module --with-cc=clang --with-cc-opt="-g -flto -fPIC -fPIE -Wno-deprecated-declarations" --with-ld-opt="-flto -fPIC -fuse-ld=gold -Wl,-plugin-opt=save-temps"
    #./configure --with-cc=clang --with-cc-opt="-g -flto -fPIC -fPIE -Wno-deprecated-declarations" --with-ld-opt="-flto -fPIC -fuse-ld=gold -Wl,-plugin-opt=save-temps"
    make -j16
    ## LLVM File & Executable found in objs/

    ## Files in src folder
    #cp objs/nginx.0.0.preopt.bc ../../../out-of-tree-pass/debloat-pass/test/nginx.ll
    popd
}

## Runs pass on server IR
function debloat_nginx(){
    ## Run pass on nginx/objs/nginx.0.0.preopt.bc
    #opt -O3 ../test/nginx-1.24.0/objs/nginx.0.0.preopt.bc -o ../test/nginx-1.24.0/objs/nginx_O3.bc
    ## To run with debug messages: add -my-debug after --passes=..
    opt -O3 ../test/nginx-1.24.0/objs/nginx.0.0.preopt.bc -o ../test/nginx-1.24.0/objs/nginx.0.0.preopt.bc
    opt -load-pass-plugin build/DebloatPass/libDebloatPass.so --passes="debloat" ../test/nginx-1.24.0/objs/nginx.0.0.preopt.bc -o ../test/nginx-1.24.0/objs/nginx_pass.bc 2> nginx-pass.log
    
    #mkdir -p logs
    #mv nginx-pass.log logs/
    echo "----Pass ran on nginx----"
}

function create_exe() {
    pushd ../test/nginx-1.24.0/objs
    orig_file="nginx_pass.bc"
    orig_name=$(basename "${orig_file%???}")

   
    llc -filetype=obj -relocation-model=pic $orig_file
    # -lcrypt -lpcre2-8
    clang -g $orig_name.o -lcrypt -lpcre -lz -o nginx_pass -fPIC

    echo "----Executable Created----"

    popd
}


function test_orig_exe() {
    pushd ../../whole-prog-test/nginx-1.24.0
    objs/nginx -p .
    popd
}

function test_db_exe() {
    pushd ../../whole-prog-test/nginx-1.24.0
    objs/nginx_db -p .
    popd
}


build_pass
#configure_nginx
#time {
#    debloat_nginx
#}
#echo "--------- EXE ----------"
#time {
    #create_exe
#}

