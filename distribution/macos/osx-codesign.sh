#!/usr/bin/env sh

cd ./dist/CellProfiler-Analyst.app/Contents/Resources
sudo rm -r Home/legal/
find . -type f | xargs -I file codesign --timestamp -f -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" file
cd ../Frameworks
sudo rm -r Home/legal/
find . -type f | xargs -I file codesign --timestamp -f -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" file
cd ../MacOS
find . -type f | xargs -I file sudo codesign --timestamp -f -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" file
codesign --timestamp -f -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" _elementtree.cpython-38-darwin.so
codesign --entitlements entitlements.plist --timestamp -o runtime -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" ./cpanalyst
cd ..
codesign --timestamp -s "Developer ID Application: Beth Cimini (27YQ9U45D9)" Info.plist


