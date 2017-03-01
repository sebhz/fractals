#!/bin/bash

cd png_tile
for f in ../png/*; do convert $f -resize 128x128 `basename $f`; done
cd ..
cd png_thumb
for f in ../png/*; do convert $f -resize 600x600 `basename $f`; done
cd ..
