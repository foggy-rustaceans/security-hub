import os
import time
from multiprocessing import Process

def run_program(cmd):
    # Function that processes will run
    os.system(cmd)

# Creating command to run
commands = ['python app.py']*100

# Amount of times your programs will run
runs = 1

desired_time = 60 # 1 minute
start_time = time.time()

for run in range(runs):
    # Initiating Processes with desired arguments
    running_programs = []
    for command in commands:
        running_programs.append(Process(target=run_program, args=(command,)))
        running_programs[-1].daemon = True

    # Start our processes simultaneously
    for program in running_programs:
        program.start()

    # Wait untill all programs are done or time has passed
    while any(program.is_alive() for program in running_programs) and time.time() - start_time < desired_time:
        time.sleep(1)