from unsloth import FastLanguageModel
from transformers import TextIteratorStreamer
import threading, time, requests, os, json

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit"

model, tokenizer = FastLanguageModel.from_pretrained(
  model_name=model_name,
  load_in_4bit=True,
  device_map="cuda"
)
FastLanguageModel.for_inference(model)
tokenizer.eos_token = "<|eot_id|>"
streamer = TextIteratorStreamer(tokenizer)
print(f"Loaded {model_name}")

messages = [
  {
  }
]

MEMORY_FREQUENCY = 5 # the frequency to create a memory summary
MEMORY_SUMMARY_CONTEXT_MESSAGES = 2 # extra messages (prior to new messages) to include in the summary prompt for context
MEMORY_RECALL_COUNT = 6 # the number of separate memories to recall
MEMORY_QUERY_LENGTH = 2 # the max number of pairs of messages to include in the query
MAX_TOKEN_COUNT = 1600
SYSTEM = "You are an opinionated assistant."

def create_memory_summary():
  temp_messages = [
    {
      "role": "system",
      "content": SYSTEM
    }
  ]
  # add as many messages as possible to the summary while avoiding index out of range
  diff = (len(messages)-1) - MEMORY_FREQUENCY*2
  rnge = reversed(range(MEMORY_FREQUENCY*2 + (MEMORY_SUMMARY_CONTEXT_MESSAGES if diff > MEMORY_SUMMARY_CONTEXT_MESSAGES else diff)))
  for x in rnge:
    temp_messages.append({
      "role": messages[-(x+1)]["role"],
      "content": messages[-(x+1)]["content"]
    })
  temp_messages.append({
    "role": "SYSTEM",
    "content": "Summarise the previous conversation in first person for your memory. Don't preface it with 'this is a summary' or add unnecessary context"
  })
  print(f"Context for summary:\n{temp_messages}")
  inputs = tokenizer.apply_chat_template(temp_messages, add_generation_prompt=True, return_tensors="pt").to("cuda")
  generation_kwargs = dict(
    inputs=inputs,
    eos_token_id=tokenizer.eos_token_id, 
    pad_token_id=tokenizer.pad_token_id, 
    do_sample=True,
    use_cache=True,
    max_new_tokens = 1000,
    temperature = 1.0,
    repetition_penalty = 1.0,
  )
  generated_ids = model.generate(**generation_kwargs)
  generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].split('\n')[-1]
  print(f"Generated memory summary:\n{generated_text}")
  requests.post('http://127.0.0.1:5000/memories', json={ "text": generated_text })
  return 

def recall_memories():
  query = ""
  memory_segment = ""
  rnge = range(-MEMORY_QUERY_LENGTH*2 if len(messages)-1 > MEMORY_QUERY_LENGTH*2 else len(messages)-1, 0)
  for x in rnge:
    query += f"{messages[x]['role']}: {messages[x]['content']}\n"
  res = requests.get('http://127.0.0.1:5000/memories', json={ "query": query, "quantity": MEMORY_RECALL_COUNT }).json()
  for m in res:
    memory_segment += f"{m['time']}: {m['text']}\n"
  if len(res) == 0:
    print("No memories yet")
  else:
    print(f"Memory segment is {len(tokenizer(memory_segment))} tokens long")
  return ("\nMEMORIES:\n" + memory_segment) if len(res) > 0 else ''

def generate_reply(message, role):
  messages[0] = {
    "role": "system",
    "content": SYSTEM
  }
  messages.append({
    "role": role,
    "content": message
  })
  if MEMORY_RECALL_COUNT > 0:
    messages[0]['content'] += recall_memories()
  print(f"Full system context:\n{messages[0]['content']}\n")

  while len(tokenizer.apply_chat_template(messages)) > MAX_TOKEN_COUNT:
    del messages[1]

  inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
  generation_kwargs = dict(
    inputs=inputs,
    streamer=streamer,
    eos_token_id=tokenizer.eos_token_id, 
    pad_token_id=tokenizer.pad_token_id, 
    do_sample=True,
    use_cache=True,
    max_new_tokens = 1000,
    temperature = 1.0,
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
    # print(generated_text)
    requests.post("http://127.0.0.1:5000/stream", json={"status": "generating", "text": generated_text})

  messages.append({
    "role": "Assistant",
    "content": generated_text
  })

  if (len(messages)-1) % (MEMORY_FREQUENCY*2) == 0:
    create_memory_summary()
  
  requests.post("http://127.0.0.1:5000/stream", json={"status": "idle", "text": generated_text})
