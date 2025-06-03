#!/bin/bash

# Set the total number of iterations
declare -i points=250

for i in $(seq -f "%03g" 0 $((points - 1))); do
  # Take a screenshot with zero-padded filename (using X11 tool)
  import -window root images/page$i.png
  # Move mouse to the next button
  xdotool mousemove 1865 650
  # Perform the click (1 = left click in xdotool)
  xdotool click 1
  # Move mouse out of view
  xdotool mousemove 0 0
  
  sleep 0.5s
done  

