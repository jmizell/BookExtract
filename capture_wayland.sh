#!/bin/bash

# Set the total number of iterations
declare -i points=5

# capture area
w=760
h=880
x=1060
y=210

for i in $(seq -f "%03g" 0 $((points - 1))); do

  # Take a screenshot with zero-padded filename
  gnome-screenshot -f page$i.png
  # Crop the screenshot to the specified region
  convert page$i.png -crop ${w}x${h}+${x}+${y} page$i.png
  echo "Saved screenshot as page$i.png"
  
  tesseract page$i.png page$i
  sed -i -z "s/\n\n/\x00/g; s/\n/ /g; s/\x00/\n\n/g" page$i.txt
  echo "OCR screenshot as page$i.txt"

  # Move mouse to the next botton
  sudo ydotool mousemove 935, 325 >/dev/null 2>&1
  # Perform the click
  sudo ydotool click 0xC0 >/dev/null 2>&1
  # Move mouse out of view
  sudo ydotool mousemove 0, 0 >/dev/null 2>&1
  #sleep 1s
done  

cat page*.txt > book.txt
rm page*.txt

