#!/usr/bin/env sh

cd ./dist/CellProfiler-Analyst.app/Contents/Resources
sudo rm -r Home/legal/
echo "do 1"
sudo codesign --timestamp -s "Apple Development: Beth Cimini (27YQ9U45D9)" Home/lib/server/classes.jsa
echo "done 1"
find . -type f | xargs -I file codesign --timestamp -f -s "Apple Development: Beth Cimini (27YQ9U45D9)" file
cd ../MacOS
find . -type f | xargs -I file sudo codesign --timestamp -f -s "Apple Development: Beth Cimini (27YQ9U45D9)" file
echo "do 2"
codesign --timestamp -f -s "Apple Development: Beth Cimini (27YQ9U45D9)" _elementtree.cpython-38-darwin.so
echo "done 2, doing 3"
codesign --entitlements entitlements.plist --timestamp -o runtime -s "Apple Development: Beth Cimini (27YQ9U45D9)" ./cpanalyst
echo "done 3"
cd ..
codesign --timestamp -s "Apple Development: Beth Cimini (27YQ9U45D9)" Info.plist


