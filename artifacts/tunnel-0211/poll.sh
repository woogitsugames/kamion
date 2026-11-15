#!/bin/bash
# poll.sh <tag> <lines>: wait (max 150 s) until chain-<tag>.status has more than <lines> lines
cd /c/Users/matma/Documents/Claude/kamion/.claude/worktrees/tunnel-0211
f=artifacts/tunnel-0211/chain-$1.status; n=0
until [ "$(wc -l < $f)" -gt "$2" ] || [ $n -ge 30 ]; do sleep 5; n=$((n+1)); done
date +%H:%M; cat $f
grep -o "^\[world [0-9.]*s\] [a-z_ ]*" artifacts/tunnel-0211/build_world-$1.log | tail -1
