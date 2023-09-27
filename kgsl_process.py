# Python program to
# demonstrate readline()
import re

# writing to file
file2 = open('retire.csv', 'w')
  
# Using readline()
file1 = open('kgsl.txt', 'r')
count = 0
retire_count = 0
  
while True:
    count += 1
  
    # Get next line from file
    line = file1.readline()
    # if line is empty
    # end of file is reached
    if not line:
        break
  
    #process line
    if "adreno_cmdbatch_retired: ctx=4" in line:
        retire_count+=1
        start = re.findall(r'start=\d+', line)
        start = int(re.findall(r'\d+', start[0])[0])
        retire = re.findall(r'retire=\d+', line)
        retire = int(re.findall(r'\d+', retire[0])[0])
        duration = retire-start
        print("processing start:{}".format(start))
        print("processing retire:{}".format(retire))
        print("processing duration:{}".format(duration))
        file2.write("{}\t{}\t{}\n".format(start,retire,duration))

    #calculate gpu retire time

    #write to a excel

    print("processing Line{}".format(count))

print("processing sf retire Line{}".format(retire_count)) 
file1.close()
file2.close()
