set pagination off
set disable-randomization off
break show_memory
run
print sizeof(char)
print sizeof(int)
print sizeof(long)
print *x
x/4xb x
x/3dw numbers
continue
quit
