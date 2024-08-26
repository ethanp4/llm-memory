# simplechat
LLM interface capable of creating and retrieving "long term memories" by summarizing a number of recent chat messages. The memory and a 384-dim vector is added to the vectordb which is later queried with a number of previous messages (default: 4). Vectors are created by a smaller secondary transformer model

## Docker usage
requires nvidia-container-toolkit
```bash
docker pull ghcr.io/ethanp4/simplechat:main
docker run -p 5000:5000 --gpus all -it ghcr.io/ethanp4/simplechat:main
```

## Non-docker
[Unsloth](https://github.com/unslothai/unsloth/tree/main?tab=readme-ov-file#-installation-instructions)
```bash
pip install flask flask_cors lancedb sentence-transformers babel 
```
*You can use transformers instead by replacing this code in model.py
```py
from unsloth import FastLanguageModel
...
model, tokenizer = FastLanguageModel.from_pretrained(model_name=model_name, load_in_4bit=True, device_map="cuda")
FastLanguageModel.for_inference(model)
```
with
```py
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
...
bnbconfig = BitsAndBytesConfig(load_in_4bit=True)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnbconfig, device_map="cuda")
```
### Usage
``python server.py``
<br>Chat at http://127.0.0.1:5000/
<br>/generate POST
<br>/memories GET POST
<br>/stream GET POST

## Models used
Primary model: [Llama 3 8b](https://huggingface.co/unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit)
<br>Secondary model: [all MiniLM L6 v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
