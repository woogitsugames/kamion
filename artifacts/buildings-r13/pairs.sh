# before/after pairs (960 px) of the review cameras: pairs/<cam>_<cfg>.jpg (top = base, bottom = round)
r=${1:-r2}
mkdir -p pairs
for cfg in High-overcast Low-overcast High-clear; do
  for c in r10_block_1 r10_block_2 r10_block_3 r10_block_4 r10_block_5 r10_house_1 r10_house_2 r10_fence_2; do
    [ -f $r/$cfg/1280/$c.jpg ] && magick base/$cfg/1280/$c.jpg $r/$cfg/1280/$c.jpg -resize 960x -append -quality 88 pairs/${c}_${cfg}.jpg
  done
done
mkdir -p $r/extra/960
for f in $r/extra/*.png; do [ -f "$f" ] && magick "$f" -resize 960x -quality 88 $r/extra/960/$(basename "${f%.png}").jpg; done
ls pairs | wc -l
