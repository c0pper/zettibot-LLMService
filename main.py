from flask import Flask, request, jsonify
import langchain_community
from langchain_community.llms import Ollama
from prompts import base_prompt, prompts
from rag import chroma_db
import re
import logging


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

llm = Ollama(model="llama3", stop=["<|eot_id|>"], base_url="http://192.168.1.164:11434") 

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
    answer = remove_parenthesis(answer).replace("\"", "").replace("### RISPOSTA:", "").capitalize()
    answer = re.sub(r'[\,\!\.]', ' ', answer)
    answer = re.sub(r'[\']', '', answer)
    return remove_parenthesis(answer).replace("\"", "").replace("### RISPOSTA:", "").capitalize()



@app.route('/generate_message', methods=['POST'])
def generate_message():
    print("got request")
    data = request.json
    user_message = data.get('user_message')
    intent = data.get('intent')

    nl = "\n"
    examples = chroma_db.similarity_search(user_message, filter={"intent": intent}, k=2)
    examples = [f"{x.metadata['nap']} ({x.page_content})" for x in examples]
    formatted_prompt = format_llm_prompt(user_message=user_message, examples=examples)

    logger.info(f"User message: {user_message}")
    logger.info(f"Intent: {intent}")
    logger.info(f"Examples: \n{nl.join(examples)}")
    logger.info(f"Formatted prompt: \n{formatted_prompt}")

    try:
        llm_response = llm.invoke(formatted_prompt)
        llm_response = clean_llm_answer(llm_response)
        logger.info(f"LLM Response: {llm_response}")
        return jsonify({'llm_response': llm_response})
    except langchain_community.llms.ollama.OllamaEndpointNotFoundError as e:
        print(f"Ollama error: {e}")
        return jsonify({'llm_response': ""})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
