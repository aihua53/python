#!/bin/bash
grep -rn \"cpu\": cpu.log|awk -F"reportPerformance:" '{print $2}'>cpu_jason.loggrep