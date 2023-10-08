#Import libraries and utilities

import autogen
from autogen.retrieve_utils import TEXT_FORMATS
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.contrib.math_user_proxy_agent import MathUserProxyAgent
import weaviate 
import chromadb
import json
import os

autogen.ChatCompletion.start_logging()


config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

llm_config={
    "request_timeout": 5000,
    "seed": 42,
    "config_list": config_list,
    "temperature": 0,
}

gpt4_config = {
    "seed": 42,  # change the seed for different trials
    "temperature": 0,
    "config_list": config_list_gpt4,
    "request_timeout": 300,
}

### Multi-User Multi-Agent : Construct USERS

user_proxy = autogen.UserProxyAgent(
   name="User_Admin",
   system_message="A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin.",
   code_execution_config=False,
)
user_manager = autogen.UserProxyAgent(
    name="User_Manager",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=100,
    code_execution_config={"work_dir": "XXXXXX"},###REMEMBER TO CHANGE
    function_map={"ask_expert": ask_expert},     ###REMEMBER TO CHANGE
)

### ISSUE : HOW TO CREATE MULTIPLE USERS ON THE FLY?

### Multi-User Multi-Agent : Construct Agents

### CREATE AGENTS HERE :


#Example Student:
def ask_expert(message):
    assistant_for_expert = autogen.AssistantAgent(
        name="assistant_for_expert",
        llm_config={
            "temperature": 0,
            "config_list": config_list,
        },
    )
    expert = autogen.UserProxyAgent(
        name="expert",
        human_input_mode="ALWAYS",
        code_execution_config={"work_dir": "expert"},
    )

# Example Research:
engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=gpt4_config,
    system_message='''Engineer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
''',
)
scientist = autogen.AssistantAgent(
    name="Scientist",
    llm_config=gpt4_config,
    system_message="""Scientist. You follow an approved plan. You are able to categorize papers after seeing their abstracts printed. You don't write code."""
)
planner = autogen.AssistantAgent(
    name="Planner",
    system_message='''Planner. Suggest a plan. Revise the plan based on feedback from admin and critic, until admin approval.
The plan may involve an engineer who can write code and a scientist who doesn't write code.
Explain the plan first. Be clear which step is performed by an engineer, and which step is performed by a scientist.
''',
    llm_config=gpt4_config,
)
executor = autogen.UserProxyAgent(
    name="Executor",
    system_message="Executor. Execute the code written by the engineer and report the result.",
    human_input_mode="NEVER",
    code_execution_config={"last_n_messages": 3, "work_dir": "paper"},
)
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
    llm_config=gpt4_config,
)

### RetrieveAssistantAgent instance named "assistant"
assistant = RetrieveAssistantAgent(
    name="assistant", 
    system_message="You are a helpful assistant.",
    llm_config={
        "request_timeout": 600,
        "seed": 42,
        "config_list": config_list,
    },
)

# 2. create the RetrieveUserProxyAgent instance named "ragproxyagent"
# By default, the human_input_mode is "ALWAYS", which means the agent will ask for human input at every step. We set it to "NEVER" here.
# `docs_path` is the path to the docs directory. By default, it is set to "./docs". Here we generated the documentations from FLAML's docstrings.
# Navigate to the website folder and run `pydoc-markdown` and it will generate folder `reference` under `website/docs`.
# `task` indicates the kind of task we're working on. In this example, it's a `code` task.
# `chunk_token_size` is the chunk token size for the retrieve chat. By default, it is set to `max_tokens * 0.6`, here we set it to 2000.
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    retrieve_config={
        "task": "code",
        "docs_path": "../website/docs/reference",
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "embedding_model": "all-mpnet-base-v2",
    },
)

    assistant_for_student = autogen.AssistantAgent(
    name="assistant_for_student",
    system_message="You are a helpful assistant. Reply TERMINATE when the task is done.",
    llm_config={
        "request_timeout": 600,
        "seed": 42,
        # Excluding azure openai endpoints from the config list.
        # Change to `exclude="openai"` to exclude openai endpoints, or remove the `exclude` argument to include both.
        "config_list": autogen.config_list_openai_aoai(exclude="aoai"),
        "model": "gpt-4-0613",  # make sure the endpoint you use supports the model
        "temperature": 0,
        "functions": [
            {
                "name": "ask_expert",
                "description": "ask expert when you can't solve the problem satisfactorily.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "question to ask expert. Make sure the question include enough context, such as the code and the execution result. The expert does not know the conversation between you and the user, unless you share the conversation with the expert.",
                        },
                    },
                    "required": ["message"],
                },
            }
        ],
    }
)


### Initiate Chat

## Example Group Chat / Research :

#groupchat = autogen.GroupChat(agents=[user_proxy, engineer, scientist, planner, executor, critic], messages=[], max_round=50)
#manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)
### Example 
#user_proxy.initiate_chat(
#    manager,
#    message="""
#find papers on LLM applications from arxiv in the last week, create a markdown table of different domains.
#""",
#)

## Example Group Chat / Student :
    expert.initiate_chat(assistant_for_expert, message=message)
    expert.stop_reply_at_receive(assistant_for_expert)
    # expert.human_input_mode, expert.max_consecutive_auto_reply = "NEVER", 0
    # final message sent from the expert
    expert.send("summarize the solution and explain the answer in an easy-to-understand way", assistant_for_expert)
    # return the last message the expert received
#    return expert.last_message()["content"]
# Multi-User Multi-Agent :

# the assistant receives a message from the student, which contains the task description
student.initiate_chat(
    assistant_for_student,
    message="""Find $a + b + c$, given that $x+y \\neq -1$ and 
\\begin{align}
	ax + by + c & = x + 7,\\
	a + bx + cy & = 2x + 6y,\\
	ay + b + cx & = 4x + y.
\\end{align}.
""",
)
#RAG

# reset the assistant. Always reset the assistant before starting a new conversation.
assistant.reset()

# set `human_input_mode` to be `ALWAYS`, so the agent will ask for human input at every step.
ragproxyagent.human_input_mode = "ALWAYS"

qa_problem = "Who is the author of FLAML?"
ragproxyagent.initiate_chat(assistant, problem=qa_problem)

code_problem = "how to build a time series forecasting model for stock price using FLAML?"
ragproxyagent.initiate_chat(assistant, problem=code_problem)

corpus_file = "https://huggingface.co/datasets/thinkall/NaturalQuestionsQA/resolve/main/corpus.txt"

# Create a new collection for NaturalQuestions dataset
# `task` indicates the kind of task we're working on. In this example, it's a `qa` task.
ragproxyagent = RetrieveUserProxyAgent(
    name="ragproxyagent",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    retrieve_config={
        "task": "qa",
        "docs_path": corpus_file,
        "chunk_token_size": 2000,
        "model": config_list[0]["model"],
        "client": chromadb.PersistentClient(path="/tmp/chromadb"),
        "collection_name": "natural-questions",
        "chunk_mode": "one_line",
        "embedding_model": "all-MiniLM-L6-v2",
    },
)
import json

# queries_file = "https://huggingface.co/datasets/thinkall/NaturalQuestionsQA/resolve/main/queries.jsonl"
queries = """{"_id": "ce2342e1feb4e119cb273c05356b33309d38fa132a1cbeac2368a337e38419b8", "text": "what is non controlling interest on balance sheet", "metadata": {"answer": ["the portion of a subsidiary corporation 's stock that is not owned by the parent corporation"]}}
{"_id": "3a10ff0e520530c0aa33b2c7e8d989d78a8cd5d699201fc4b13d3845010994ee", "text": "how many episodes are in chicago fire season 4", "metadata": {"answer": ["23"]}}
{"_id": "fcdb6b11969d5d3b900806f52e3d435e615c333405a1ff8247183e8db6246040", "text": "what are bulls used for on a farm", "metadata": {"answer": ["breeding", "as work oxen", "slaughtered for meat"]}}
{"_id": "26c3b53ec44533bbdeeccffa32e094cfea0cc2a78c9f6a6c7a008ada1ad0792e", "text": "has been honoured with the wisden leading cricketer in the world award for 2016", "metadata": {"answer": ["Virat Kohli"]}}
{"_id": "0868d0964c719a52cbcfb116971b0152123dad908ac4e0a01bc138f16a907ab3", "text": "who carried the usa flag in opening ceremony", "metadata": {"answer": ["Erin Hamlin"]}}
"""
queries = [json.loads(line) for line in queries.split("\n") if line]
questions = [q["text"] for q in queries]
answers = [q["metadata"]["answer"] for q in queries]
print(questions)
print(answers)
for i in range(len(questions)):
    print(f"\n\n>>>>>>>>>>>>  Below are outputs of Case {i+1}  <<<<<<<<<<<<\n\n")

    # reset the assistant. Always reset the assistant before starting a new conversation.
    assistant.reset()
    
    qa_problem = questions[i]
    ragproxyagent.initiate_chat(assistant, problem=qa_problem, n_results=30)


### Math Agent

# 1. create an AssistantAgent instance named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant", 
    system_message="You are a helpful assistant.",
    llm_config={
        "request_timeout": 600,
        "seed": 42,
        "config_list": config_list,
    }
)

# 2. create the MathUserProxyAgent instance named "mathproxyagent"
# By default, the human_input_mode is "NEVER", which means the agent will not ask for human input.
mathproxyagent = MathUserProxyAgent(
    name="mathproxyagent", 
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
)
### Examples :

math_problem = "Find all positive integer values of $c$ such that the equation $x^2-7x+c=0$ only has roots that are real and rational. Express them in decreasing order, separated by commas."
mathproxyagent.initiate_chat(assistant, problem=math_problem)
# we set the prompt_type to "python", which is a simplied version of the default prompt.
math_problem = "Problem: If $725x + 727y = 1500$ and $729x+ 731y = 1508$, what is the value of $x - y$ ?"
mathproxyagent.initiate_chat(assistant, problem=math_problem, prompt_type="python")
# The wolfram alpha appid is required for this example (the assistant may choose to query Wolfram Alpha).
import os
if "WOLFRAM_ALPHA_APPID" not in os.environ:
    os.environ["WOLFRAM_ALPHA_APPID"] = open("wolfram.txt").read().strip()

# we set the prompt_type to "two_tools", which allows the assistant to select wolfram alpha when necessary.
math_problem = "Find all numbers $a$ for which the graph of $y=x^2+a$ and the graph of $y=ax$ intersect. Express your answer in interval notation."
mathproxyagent.initiate_chat(assistant, problem=math_problem, prompt_type="two_tools")
print(autogen.ChatCompletion.logged_history)

# The wolfram alpha appid is required for this example (the assistant may choose to query Wolfram Alpha).
import os
if "WOLFRAM_ALPHA_APPID" not in os.environ:
    os.environ["WOLFRAM_ALPHA_APPID"] = open("wolfram.txt").read().strip()

# we set the prompt_type to "two_tools", which allows the assistant to select wolfram alpha when necessary.
math_problem = "Find all numbers $a$ for which the graph of $y=x^2+a$ and the graph of $y=ax$ intersect. Express your answer in interval notation."
mathproxyagent.initiate_chat(assistant, problem=math_problem, prompt_type="two_tools")

### Single User Multi-Agent :
## Initialize Agents and Users:
# create an AssistantAgent instance named "assistant"
#assistant = autogen.AssistantAgent(
#    name="assistant",
#    llm_config=llm_config,
#)
#
### Single User 
# Example : create a UserProxyAgent instance named "user_proxy"
#user_proxy = autogen.UserProxyAgent(
#    name="user_proxy",
#    human_input_mode="TERMINATE",
#    max_consecutive_auto_reply=10,
#    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
#    code_execution_config={"work_dir": "web"},
#    llm_config=llm_config,
#    system_message="""Reply TERMINATE if the task has been solved at full satisfaction.
#Otherwise, reply CONTINUE, or the reason why the task is not solved yet."""
#)
# the assistant receives a message from the user, which contains the task description
#user_proxy.initiate_chat(
#    assistant,
#    message="""
#Who should read this paper: https://arxiv.org/abs/2308.08155
#""",
#)
# Chat about the Stock Market
#user_proxy.initiate_chat(
#    assistant,
#    message="""Show me the YTD gain of 10 largest technology companies as of today.""",
#)