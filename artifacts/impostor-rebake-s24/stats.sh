#!/usr/bin/env bash
# impostor-rebake-s24: draws / triangles before|after per camera from the visual-qa stats.txt
cd "$(dirname "$0")"
B=$1; A=$2
for s in knyszyn-w-High-clear dk65-07-High-clear; do
  for f in "$B/$s/stats.txt"; do
    grep -E "^[a-z0-9_-]+: objects=" "$f" | while read -r line; do
      cam=${line%%:*}
      b=$(grep -E "^  $cam instanced" "$B/$s/stats.txt" | sed -E 's/.*draws ([0-9]+).*trianglesExact ([0-9]+).*/\1 \2/')
      a=$(grep -E "^  $cam instanced" "$A/$s/stats.txt" | sed -E 's/.*draws ([0-9]+).*trianglesExact ([0-9]+).*/\1 \2/')
      bo=$(grep -E "^$cam: objects" "$B/$s/stats.txt" | sed -E 's/.*drawsEst=([0-9]+).*trisExact=([0-9]+).*/\1 \2/')
      ao=$(grep -E "^$cam: objects" "$A/$s/stats.txt" | sed -E 's/.*drawsEst=([0-9]+).*trisExact=([0-9]+).*/\1 \2/')
      echo -e "$s\t$cam\tinst(draws tris) $b -> $a\tobj(draws tris) $bo -> $ao"
    done
  done
done
