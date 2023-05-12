#!/bin/env bash

SRC=$1
DST=$2

if (( $# < 2 )); then
	echo "Usage: $0 src dest"
	exit 1
fi

ls -- $SRC/* |  while read i; do 
	EXT=`echo $i | sed 's/^.*\.//'`; 
	MD=`md5sum -- "$i" | awk '{print $1}'`; 
	TARGET=$DST/$MD.$EXT; 
	echo $TARGET
	ln -- "$i" "$TARGET"; 
done

