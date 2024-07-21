__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import random
import streamlit as st
from crewai import Crew, Process, Agent, Task
from langchain_core.callbacks import BaseCallbackHandler
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from crewai_tools import WebsiteSearchTool

# Sidebar for API key input
st.sidebar.title("Configuration")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize LLM only if the API key is provided
if openai_api_key:
    llm = ChatOpenAI(openai_api_key=openai_api_key,
                     model="gpt-4o-mini",
                     temperature=0,
                     max_tokens=None)

# List of avatars
avatar_urls = [
    "https://cdn-icons-png.flaticon.com/128/4150/4150773.png",
    "https://cdn-icons-png.flaticon.com/128/4150/4150647.png",
    "https://cdn-icons-png.flaticon.com/128/4150/4150659.png",
    "https://cdn-icons-png.flaticon.com/128/4150/4150664.png",
    "https://cdn-icons-png.flaticon.com/128/4150/4150843.png"
]


# Randomly assign avatars to agents
random.shuffle(avatar_urls)

# class MyCustomHandler(BaseCallbackHandler):

#     def __init__(self, agent_name: str) -> None:
#         self.agent_name = agent_name

#     def on_chain_start(
#         self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
#     ) -> None:
#         st.session_state.messages.append({"role": "assistant", "content": inputs['input']})
#         st.chat_message("assistant").write(inputs['input'])

#     def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
#         st.session_state.messages.append({"role": self.agent_name, "content": outputs['output']})
#         st.chat_message(self.agent_name).write(outputs['output'])

class MyCustomHandler(BaseCallbackHandler):

    def __init__(self, agent_name: str, avatar_url: str) -> None:
        self.agent_name = agent_name
        self.avatar_url = avatar_url

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        st.session_state.messages.append({"role": "assistant", "content": inputs['input']})
        st.chat_message("assistant").write(inputs['input'])

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        st.session_state.messages.append({"role": self.agent_name, "content": outputs['output']})
        st.chat_message(self.agent_name, avatar=self.avatar_url).write(outputs['output'])

# def define_agents():
#     agents = []
#     for i in range(2):
#         with st.expander(f"Define Agent {i+1}", expanded=(i == 0)):
#             # name = st.text_input(f"Agent {i+1} Name", key=f"name_{i}")
#             role = st.text_input(f"Agent {i+1} Role", key=f"role_{i}")
#             backstory = st.text_area(f"Agent {i+1} Backstory", key=f"backstory_{i}")
#             goal = st.text_input(f"Agent {i+1} Goal", key=f"goal_{i}")

#             if role and backstory and goal:
#                 agent = Agent(
#                     role=role,
#                     backstory=backstory,
#                     goal=goal,
#                     llm=llm,
#                     callbacks=[MyCustomHandler(role)]
#                 )
#                 agents.append(agent)
#                 # Save agent to session state
#                 st.session_state[f"agent_{i}"] = {"role": role, "backstory": backstory, "goal": goal}
#     return agents

def define_agents():
    agents = []
    for i in range(4):
        with st.expander(f"Define Agent {i+1}", expanded=(i == 0)):
            role = st.text_input(f"Agent {i+1} Role", key=f"role_{i}")
            backstory = st.text_area(f"Agent {i+1} Backstory", key=f"backstory_{i}")
            goal = st.text_input(f"Agent {i+1} Goal", key=f"goal_{i}")

            if role and backstory and goal:
                # Initialize the specific tool if the role is "product owner"
                tools = []
                if role.lower() == "product owner":
                    tool_roadmap = WebsiteSearchTool(website='https://www.romanpichler.com/blog/10-tips-creating-agile-product-roadmap/')
                    tools.append(tool_roadmap)

                agent = Agent(
                    role=role,
                    backstory=backstory,
                    goal=goal,
                    llm=llm,
                    tools=tools,  # Include tools here
                    callbacks=[MyCustomHandler(role)]
                )

                agents.append(agent)
                # Save agent to session state
                st.session_state[f"agent_{i}"] = {"role": role, "backstory": backstory, "goal": goal}
    return agents

def main():
    st.title("💬 AI Agents - Product Roadmap and Backlog generation/simulation")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Describe your product strategy below"}]

    if "task_descriptions" not in st.session_state:
        st.session_state["task_descriptions"] = []

    if "define_tasks_clicked" not in st.session_state:
        st.session_state["define_tasks_clicked"] = False

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    agents = define_agents()
       
    if st.button("Define Tasks"):
        st.session_state["define_tasks_clicked"] = True

    if st.session_state["define_tasks_clicked"]:
        task_descriptions = []
        for i in range(4):
            if f"agent_{i}" in st.session_state:
                agent_data = st.session_state[f"agent_{i}"]
                agent = Agent(
                    role=agent_data["role"],
                    backstory=agent_data["backstory"],
                    goal=agent_data["goal"],
                    llm=llm,
                    callbacks=[MyCustomHandler(agent_data["role"])]
                )
                with st.expander(f"Define Task for {agent.role}", expanded=True):
                    task_description = st.text_area(f"Task Description for {agent.role}", key=f"task_description_{i}")
                    expected_output = st.text_input(f"Desired Output/Artefacts for {agent.role}", key=f"expected_output_{i}")

                    if task_description and expected_output:
                        task_descriptions.append((task_description, agent, expected_output))
                        # Save task descriptions to session state
                        st.session_state["task_descriptions"].append((task_description, agent_data, expected_output))
        
        if st.button("Run Tasks"):
            tasks = [
                Task(description=td, agent=Agent(
                    role=a["role"],
                    backstory=a["backstory"],
                    goal=a["goal"],
                    llm=llm,
                    callbacks=[MyCustomHandler(a["role"])]
                ), expected_output=eo)
                for td, a, eo in st.session_state["task_descriptions"]
            ]
            project_crew = Crew(
                tasks=tasks,
                agents=agents,
                manager_llm=llm,
                process=Process.hierarchical
            )
            final = project_crew.kickoff()
            result = f"## Here is the Final Result \n\n {final}"
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.chat_message("assistant").write(result)

if __name__ == "__main__":
    main()

