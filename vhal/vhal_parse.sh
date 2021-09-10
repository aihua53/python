#!/bin/bash
#cpu
grep "vendor.ts.hardware.automotive.vehicle@2.0-service level:" vhal_analysis.log |awk '{print $2,$NF}'|sed 's/level://g'|awk -F. '{print $1,$2}'|awk '{print $3,$1}'|uniq -1|awk '{print $2,$1}'>vhal_cpu.txt

grep "chj_datacollector level:" vhal_analysis.log |awk '{print $2,$NF}'|sed 's/level://g'|awk -F. '{print $1,$2}'|awk '{print $3,$1}'|uniq -1|awk '{print $2,$1}'>datacollector_cpu.txt

#spi count
grep "current SPI" vhal_analysis.log|awk '{print $2,$17}'|awk -F= '{print $1,$2}'|awk '{print $1,$3}'|awk -F. '{print $1,$2}'|awk -F, '{print $1}'|awk '{print $1,$3}'>spi_count.txt

#spi size
grep "current SPI" vhal_analysis.log|awk '{print $2,$16}'|sed 's/size://g'|awk -F. '{print $1,$2}'|awk -F, '{print $1}'|awk '{print $1,$3}'>spi_size.txt

#eth count
grep "eth socket" vhal_analysis.log|awk '{print $2,$17}'|awk -F= '{print $1,$2}'|awk '{print $1,$3}'|awk -F. '{print $1,$2}'|awk -F, '{print $1}'|awk '{print $1,$3}'>eth_count.txt

#eth size
grep "eth socket" vhal_analysis.log|awk '{print $2,$16}'|sed 's/size://g'|awk -F. '{print $1,$2}'|awk -F, '{print $1}'|awk '{print $1,$3}'>eth_size.txt
