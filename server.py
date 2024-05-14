from flask import Flask, request, jsonify, render_template
from model import generate_reply
from memory import retrieve_memories, add_memory
import threading, logging

app = Flask(__name__, template_folder="web", static_folder="web/static")

stream = { "status": "idle", "text": "" }

@app.route('/')
def serve_chat():
  return render_template("chat.html")

@app.route('/generate', methods=["POST"])
def post_generate():
  global stream
  if stream["status"] == "generating":
    return 'Generation already in progress', 503
  generate_kwargs = dict(
    message=request.get_json()["message"],
    role=request.get_json()["role"]
  )
  stream["status"] = "generating"
  generate_thread = threading.Thread(target=generate_reply, kwargs=generate_kwargs)
  generate_thread.start()
  return 'Started generation', 200

@app.route('/memories', methods=["GET"])
def get_memories():
  query = request.get_json()["query"]
  quantity = request.get_json()["quantity"]
  memories = retrieve_memories(query, quantity)
  return jsonify(memories), 200

@app.route('/memories', methods=["POST"])
def post_memories():
  text = request.get_json()["text"]
  add_memory(text)
  return '', 200

@app.route('/stream', methods=["GET"])
def get_stream():
  global stream
  return jsonify(stream), 200

@app.route('/stream', methods=["POST"])
def post_stream():
  global stream
  stream["status"] = request.get_json()["status"]
  stream["text"] = request.get_json()["text"]
  return '', 200

logging.getLogger('werkzeug').disabled = True

if __name__ == '__main__':
  app.run()