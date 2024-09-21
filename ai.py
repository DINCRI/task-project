from langchain_community.llms import Ollama



query = "Tell me a joke"

print(llm.invoke(query))