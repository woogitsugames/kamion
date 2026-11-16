# sheet.sh <tag> : per tier-lighting 2x3 sheet (960 wide tiles 640)
t=$1
for d in $t/*/; do n=$(basename $d); ls $(ls $d/*.png | grep -v envcube) >/dev/null 2>&1 || continue
 magick montage $(ls $d/*.png | grep -v envcube) -tile 3x -geometry 640x296+2+2 -background black $t/sheet-$n.jpg; done
