#!/bin/env bash

# Content Addressable Storage Ingestion

# src is a directory containing files (flat; no subdir support implemented yet)
# dst is a directory containing the results of prior runs (or empty for first run)

# files in src will be md5summed and a hard link generated in the dst using the
# md5 has as the name, preserving the extension

# e.g.
# src/filename.dat becomes <md5 of file contents>.dat

# messages from ln on stderr saying the file already exists means that the
# de-duplication of files with identical content is working as intended

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

