import lancedb, time
from sentence_transformers import SentenceTransformer
from babel.dates import format_timedelta

model_name = 'sentence-transformers/all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)
print(f"Loaded {model_name}")

uri = "./lancedb/memories"
db = lancedb.connect(uri)
try:
  tbl = db.open_table("memories")
  print("Opened db")
except:
  import pyarrow as pa
  tbl = db.create_table("memories", schema=pa.schema([
      ("vector", pa.list_(pa.float32(), 384)),
      ("time", pa.float64()),
      ("text", pa.string())
  ]))
  print("Created db")

def get_relative_time(t):
  currentTime = time.time()
  delta = t - currentTime
  relative = format_timedelta(delta, locale='en_CA', add_direction=True)
  return relative

def retrieve_memories(query, quantity):
  res = tbl.search(model.encode(query)).limit(quantity).to_list()
  for r in res:
    r["time"] = get_relative_time(r["time"])
    del r["vector"]
  return res

def add_memory(text):
  entry = [ { "vector": model.encode(text), "time": time.time(), "text": text} ]
  # print(f"Adding memory: {entry[0]['text']}")
  tbl.add(entry)
  return
