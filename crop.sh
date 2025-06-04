#!/bin/bash

# capture area for 1920x1080 screen, half vertical window
w=822
h=947
x=1056
y=190

mkdir -p out
for f in images/*.png; do
  convert $f -crop ${w}x${h}+${x}+${y} out/$f
done  

