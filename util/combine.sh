#!/bin/env bash

if [[ ! -d combined ]]; then
	echo no existing combined dir found
	exit 1;
fi

rm -rf combined
mkdir combined
ls mp4 | while read i; do ln mp4/$i combined/$i; done
ls img | while read i; do ln img/$i combined/$i.mp4; done

