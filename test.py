import os

def run_command(command: str):
    result = os.system(command)
    return result


print(run_command("ls"))