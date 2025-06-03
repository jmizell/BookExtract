#!/bin/bash

for f in out/*.txt; do
  outf="$(echo "$f" | sed 's/\.txt\|out\///g')"
  kokoro -m am_michael -l a -i "$f" -o "out/${outf}.wav"
done

