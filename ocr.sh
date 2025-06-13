#!/bin/bash

mkdir -p out
for f in out/*.png; do
  outf="$(echo "$f" | sed 's/\.png\|out\///g')"
  tesseract "$f" "out/${outf}"
  sed -i -z "s/\n\n/\x00/g; s/\n/ /g; s/\x00/\n\n/g" "out/${outf}.txt"
  echo "wrote out/${outf}.txt"
done  

