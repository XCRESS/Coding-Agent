from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import subprocess

load_dotenv()

client = OpenAI()

def run_command(cmd: str):
    if os.name == 'nt':
        result = subprocess.run(['cmd', '/c', cmd], capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def write_file(filepath: str, content: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

available_tools = {
    "run_command": run_command,
    "write_file": write_file
}

SYSTEM_PROMPT = f"""
    You are an helpfull AI Assistant who is specialized in resolving user query.
    You work on start, plan, action, observe mode.

    For the given user query and available tools, plan the step by step execution, based on the planning,
    select the relevant tool from the available tool. and based on the tool selection you perform an action to call the tool.

    Wait for the observation and based on the observation from the tool call resolve the user query.

    Rules:
    - Follow the Output JSON Format.
    - Always perform one step at a time and wait for next input
    - Carefully analyse the user query

    Output JSON Format:
    {{
        "step": "string",
        "content": "string",
        "function": "The name of function if the step is action",
        "input": "The input parameter for the function",
    }}

    Available Tools:
    - "run_command": Takes linux command as a string and executes the command and returns the output after executing it.
    - "write_file": Takes filepath and content as parameters to write content to a file.

    Example:
    User Query: Create a file with content
    Output: {{ "step": "plan", "content": "The user wants to create a file with some content" }}
    Output: {{ "step": "plan", "content": "I should use the write_file tool to create the file" }}
    Output: {{ "step": "action", "function": "write_file", "input": {{"filepath": "test.txt", "content": "Hello World"}} }}
    Output: {{ "step": "observe", "output": "File written successfully" }}
    Output: {{ "step": "output", "content": "File has been created with the specified content" }}
"""

messages = [
  { "role": "system", "content": SYSTEM_PROMPT }
]

while True:
    query = input("> ")
    messages.append({ "role": "user", "content": query })
    if query == "exit":
        break

    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )

        messages.append({ "role": "assistant", "content": response.choices[0].message.content })
        parsed_response = json.loads(response.choices[0].message.content)

        if parsed_response.get("step") == "plan":
            print(f"🧠: {parsed_response.get('content')}")
            continue

        if parsed_response.get("step") == "action":
            tool_name = parsed_response.get("function")
            tool_input = parsed_response.get("input")

            print(f"🛠️: Calling Tool:{tool_name} with input {tool_input}")

            if tool_name in available_tools:
                if tool_name == "write_file":
                    output = available_tools[tool_name](tool_input["filepath"], tool_input["content"])
                else:
                    output = available_tools[tool_name](tool_input)
                messages.append({ "role": "user", "content": json.dumps({ "step": "observe", "output": output }) })
                continue
        
        if parsed_response.get("step") == "output":
            print(f"🤖: {parsed_response.get('content')}")
            break