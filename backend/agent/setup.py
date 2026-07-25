from setuptools import setup, find_packages

setup(
    name="agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langgraph>=1.0.0",
        "langchain-core>=0.1.0",
        "langchain-groq>=0.1.0",
        "requests>=2.0.0",
    ],
)
