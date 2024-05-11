from unsloth import FastLanguageModel
from transformers import TextIteratorStreamer
import threading, time, requests, os

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

model, tokenizer = FastLanguageModel.from_pretrained(
  model_name="unsloth/llama-3-8b-Instruct-bnb-4bit",
  load_in_4bit=True,
  device_map="cuda"
)
FastLanguageModel.for_inference(model)
tokenizer.eos_token = "<|eot_id|>"
streamer = TextIteratorStreamer(tokenizer)
print("Model loaded")

messages = [
  {"role": "system", "content": "You are a helpful assistant."},
]

def generate_reply(message, role):
  messages.append({
    "role": role,
    "content": message
  })
  inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
  generation_kwargs = dict(
    inputs=inputs,
    streamer=streamer,
    eos_token_id=tokenizer.eos_token_id, 
    pad_token_id=tokenizer.pad_token_id, 
    do_sample=True,
    use_cache=True,
    max_new_tokens = 1000,
    temperature = 1.1,
    repetition_penalty = 1.0,
  )
  gen_thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
  gen_thread.start()

  generated_text = ""
  #first iteration of streamer contains the context which can be ignored
  done_prompt = False
  for i in streamer:
    if i == "":
      continue
    if not done_prompt:
      done_prompt = True
      continue
    if tokenizer.eos_token in i:
      # remove the eos_token when it appears in the final iteration of the streamer
      i = i[:-len(tokenizer.eos_token)]
    generated_text += i
    print(generated_text)
    requests.post("http://127.0.0.1:5000/stream", json={"status": "generating", "text": generated_text})

  requests.post("http://127.0.0.1:5000/stream", json={"status": "idle", "text": generated_text})

  messages.append({
    "role": "Assistant",
    "content": generated_text
  })