FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime

WORKDIR /shrimplechat

COPY . .
RUN apt update
RUN apt install git gcc -y
# triton requirement
# RUN git clone https://github.com/ethanp4/simplechat .
RUN pip install --upgrade pip
RUN pip install "unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git"
RUN pip install flask flask_cors lancedb sentence-transformers babel 

ENV PORT=5000
EXPOSE 5000

CMD ["python", "server.py"]