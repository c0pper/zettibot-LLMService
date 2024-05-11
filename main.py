from flask import Flask, request, jsonify
import langchain_community
from langchain_community.llms import Ollama
from prompts import base_prompt, prompts
from rag import chroma_db
import re


app = Flask(__name__)

llm = Ollama(model="llama3", stop=["<|eot_id|>"]) 

def format_llm_prompt(user_message, examples):
    formatted_prompt = base_prompt.format(
        system_prompt=prompts["insulto"]["system"], 
        user_prompt=prompts["insulto"]["user"].format(examples="\n".join(examples), message=user_message)
    )

    return formatted_prompt


def remove_parenthesis(text):
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^)]*\]', '', text)
    return text


def clean_llm_answer(answer):
    return remove_parenthesis(answer).replace("\"", "").replace("### RISPOSTA:", "")



@app.route('/generate_message', methods=['POST'])
def generate_message():
    data = request.json
    user_message = data.get('user_message')
    intent = data.get('intent')

    examples = chroma_db.similarity_search(user_message, filter={"intent": intent}, k=2)
    examples = [f"{x.metadata['nap']} ({x.page_content})" for x in examples]
    formatted_prompt = format_llm_prompt(user_message=user_message, examples=examples)

    try:
        llm_response = llm.invoke(formatted_prompt)
        llm_response = clean_llm_answer(llm_response)
        return jsonify({'llm_response': llm_response})
    except langchain_community.llms.ollama.OllamaEndpointNotFoundError as e:
        print(f"Ollama error: {e}")
        return jsonify({'llm_response': ""})



if __name__ == '__main__':
    app.run(debug=True)
