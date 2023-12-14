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
function configure_thttpd(){
    pushd ../test/thttpd/
    
    ## Configure thttpd with wanted modules
    export RANLIB=llvm-ranlib
    # Disable opaque pointers for SVF usage
    ./configure CC=clang CFLAGS="-g -flto -fPIC -fPIE -Wno-deprecated-declarations" LDFLAGS="-flto -fPIC -fuse-ld=gold -Wl,-plugin-opt=save-temps"
    make -j16

    popd
}

## Runs pass on server IR
function debloat_thttpd(){
    ## Run pass on nginx/objs/nginx.0.0.preopt.bc

    ## To run with debug messages: add -my-debug after --passes=..
    opt -O3 ../test/thttpd/thttpd.0.0.preopt.bc -o ../test/thttpd/thttpd-pass.bc
    opt -load-pass-plugin build/DebloatPass/libDebloatPass.so --passes="debloat" ../test/thttpd/thttpd.0.0.preopt.bc -o ../test/thttpd/thttpd-pass.bc 2> thttpd-pass.log
    
    mkdir -p logs
    #mv nginx-pass.log logs/
    echo "----Pass ran thttpd----"
}

function create_exe() {
    pushd ../test/thttpd/
    orig_file="thttpd-pass.bc"
    orig_name=$(basename "${orig_file%???}")

   
    llc -filetype=obj -relocation-model=pic $orig_file
    # -lcrypt -lpcre2-8
    clang -g $orig_name.o -lcrypt -o thttpd_pass

    echo "----Executable Created----"

    popd
}


build_pass
#configure_thttpd
time {
    debloat_thttpd
} 
echo "---------"
time {
    create_exe
}
