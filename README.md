# simplechat
Really basic llm chat interface with long term memory using lancedb

## Docker image
docker run -p 5000:5000 --gpus all -it docker.io/ethanp4/simplechat

## Requirements
[Unsloth](https://github.com/unslothai/unsloth/tree/main?tab=readme-ov-file#-installation-instructions) or *transformers
<br>flask
<br>lancedb

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

## Usage
``python server.py``
<br>Chat at http://127.0.0.1:5000/
<br>/generate POST
<br>/memories GET POST
<br>/stream GET POST
