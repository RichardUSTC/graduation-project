#!/bin/bash
function testDir(){
    for file in $1/*
    do
        if [ -f $file ]
        then
            echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            echo "Parsing $file ..."
            echo "python cparse.py $file 2>output"
            python cparse.py $file 2>output
            if [ $? -ne 0 ]
            then
                exit $?
            fi
        elif [ -d $file ]
        then
            testDir $file
        fi
    done
}

testDir testcase
