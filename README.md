# Vashon Island RAG
A simple rag-based chatbot to answer questions about Vashon Island.
Author: Izzy Valdivia
January 2026

### Background: 
I created a basic chatbot enhanced with Retrieval-Augemented Generation (RAG). RAG is used to enhance the knowledge base of a generative LLM either to extend the context window or bolster its background on a specific topic. This also means the model does not need to be re-trained to contain specialized information. For example, I decided to use OpenAI's `gpt-5` as the basis for my chatbot and then gave it more context to answer questions specific to Vashon- an Island of ~11k people in the Puget Sound west of Seattle. 

### Tools: 
* Model: OpenAI's gpt-5
* Database: chromadb
* Pdf Parser: pyPDF

### Setup: 
I have included an environment.yml file with all required dependencies.
You will need to get an API key from OpenAI in order to run this tutorial. You will then need to add it to a .env file that is located in the root of the project that contains the line:  
`OPENAI_API_KEY="your-api-key"`

There are many resources online that explain the purpose of RAG. Here are a few links I used when attempting this mini-project: 
* [AWS- What is RAG?](https://aws.amazon.com/what-is/retrieval-augmented-generation/)
* [NVIDIA- What is Retrieval-Augmented Generation?](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/)
* [RAG Tutorial](https://learnbybuilding.ai/tutorial/rag-from-scratch/)

