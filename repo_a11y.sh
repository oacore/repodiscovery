#!/bin/bash

for filename in /Users/mc26486/workspace/KMI/repodiscovery/repo_pages/*.html; do
    echo "processing $filename"
    pa11y "$filename" --reporting csv > $filename"_a11yreport.csv" 
    sed -i -e 's/^/$filename/' $filename"_a11yreport.csv"
done
