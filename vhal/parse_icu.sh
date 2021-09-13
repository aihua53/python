#!/bin/bash

awk '{print $5,$6,$7,$8,$9,$10,$11}' icu_log.log |grep M01|awk -F\' '{print $2,$4,$6,$8,$NF}'|awk -F, '{print $1,$2,$3}'|grep vehicle|sort -k 6 -r -n > sort_vhal.txt
cat sort_vhal.txt |awk '$(NF-1)>40{print $0}' > sort_vhal_threshhold.txt
cat sort_vhal_threshhold.txt|awk '{print $1}'|uniq -c|sort -r > threshhold_count.txt
