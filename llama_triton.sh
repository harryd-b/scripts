#!/usr/bin/env bash
set -e

###############################################################################
# 0. CREATE A CUSTOM TRITON DOCKER IMAGE WITH PYTORCH
###############################################################################
echo ">>> Creating Dockerfile.triton with PyTorch and Transformers..."
cat <<EOF > Dockerfile.triton
# Start from the official Triton container
FROM nvcr.io/nvidia/tritonserver:23.01-py3

# Install PyTorch, Transformers, and any other dependencies you need
RUN apt-get update && apt-get install -y git && \
    pip3 install --no-cache-dir torch transformers
EOF

echo ">>> Building custom Triton image: tritonserver:23.01-py3-torch ..."
docker build -t tritonserver:23.01-py3-torch -f Dockerfile.triton .

###############################################################################
# CONFIGURATION
###############################################################################
# We will store everything under ~/triton by default.
TRITON_HOME="$HOME/triton"

# Set HF_HOME so huggingface_hub stores cache inside ~/triton, avoiding permission issues.
export HF_HOME="${TRITON_HOME}/.huggingface_cache"

if [ -z "$HUGGINGFACE_TOKEN" ]; then
  echo "Error: HUGGINGFACE_TOKEN is not set!"
  exit 1
fi

# Hugging Face info for downloading
HUGGINGFACE_TOKEN=$HUGGINGFACE_TOKEN
HUGGINGFACE_REPO="meta-llama/Meta-Llama-3-8B"   # ID for HF download (has slash)

# Triton model name & folder (no slash)
TRITON_MODEL_NAME="meta-llama_Meta-Llama-3-8B"

# Use our newly built Docker image
TRITON_IMAGE="tritonserver:23.01-py3-torch"
CONTAINER_NAME="triton_llama_server"

# Triton server ports
HTTP_PORT=8000
GRPC_PORT=8001
METRICS_PORT=8002

###############################################################################
# 1. PREPARE ENVIRONMENT: Install needed packages on HOST (optional, for testing)
###############################################################################
echo ">>> (HOST) Installing or upgrading Python packages: huggingface_hub, tritonclient, numpy..."
pip install --upgrade huggingface_hub tritonclient[all] numpy >/dev/null

###############################################################################
# 2. CREATE LOCAL TRITON MODEL REPOSITORY FOLDERS
###############################################################################
echo ">>> Ensuring base directory: ${TRITON_HOME}"
mkdir -p "${TRITON_HOME}"

MODEL_REPO_PATH="${TRITON_HOME}/model_repository/${TRITON_MODEL_NAME}"
echo ">>> Creating Triton model repository folders for ${TRITON_MODEL_NAME} at ${MODEL_REPO_PATH}"
mkdir -p "${MODEL_REPO_PATH}/1/model_weights"

# Also ensure our custom HF_HOME cache directory exists
mkdir -p "${HF_HOME}"

###############################################################################
# 3. DOWNLOAD MODEL WEIGHTS USING PYTHON (huggingface_hub)
###############################################################################
echo ">>> Downloading model weights from Hugging Face: ${HUGGINGFACE_REPO} ..."
PYTHON_SCRIPT=$(cat <<END_PY
from huggingface_hub import snapshot_download
repo_id = "${HUGGINGFACE_REPO}"
local_dir = "${MODEL_REPO_PATH}/1/model_weights"
token = "${HUGGINGFACE_TOKEN}"
snapshot_download(repo_id=repo_id, revision='main', local_dir=local_dir, token=token)
END_PY
)
python3 -c "${PYTHON_SCRIPT}"

###############################################################################
# 4. CREATE config.pbtxt
###############################################################################
# We'll keep max_batch_size: 8, meaning the first dimension is batch size.
# We'll define dims: [-1], meaning the second dimension is "text_length".
# So effectively the server sees shape = [batch_size, text_length].
# We'll pass shape [N, 1] in the client if we have N prompts, each with 1 text item.
cat <<EOF > "${MODEL_REPO_PATH}/config.pbtxt"
name: "${TRITON_MODEL_NAME}"
backend: "python"

max_batch_size: 8

input [
  {
    name: "TEXT"
    data_type: TYPE_STRING
    dims: [ -1 ]
  }
]

output [
  {
    name: "GENERATED_TEXT"
    data_type: TYPE_STRING
    dims: [ -1 ]
  }
]

instance_group [
  {
    kind: KIND_GPU
    count: 1
  }
]

dynamic_batching {
  preferred_batch_size: [1,2,4]
  max_queue_delay_microseconds: 10000
}

version_policy: { specific { versions: [ 1 ] } }
EOF

###############################################################################
# 5. CREATE model.py FOR THE PYTHON BACKEND
###############################################################################
# We do not duplicate folder names in the path (avoids the double-subfolder issue).
cat <<'EOF' > "${MODEL_REPO_PATH}/1/model.py"
import os
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import triton_python_backend_utils as pb_utils

class TritonPythonModel:
    def initialize(self, args):
        model_repo_path = args['model_repository']  # e.g. /models/meta-llama_Meta-Llama-3-8B
        model_version = args['model_version']       # "1"

        model_path = os.path.join(model_repo_path, model_version, "model_weights")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16).cuda()
        # Print a parameter's dtype to confirm
        print(">>> Debug: Model dtype:", next(self.model.parameters()).dtype)

        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0,
        )

    def execute(self, requests):
        responses = []
        for request in requests:
            in_tensor = pb_utils.get_input_tensor_by_name(request, "TEXT")
            # Because dims: [-1], we effectively have shape [batch_size, text_length].
            # If text_length=1, shape = (batch_size, 1). We'll flatten to (batch_size,).
            batch_texts_2d = in_tensor.as_numpy()  # shape: (batch_size, text_length)

            # Flatten the second dimension if it's always 1
            # or handle multiple columns if you want, but typically for text: shape (batch, 1).
            batch_size = batch_texts_2d.shape[0]
            text_len   = batch_texts_2d.shape[1]
            flattened_prompts = []
            for i in range(batch_size):
                for j in range(text_len):
                    text_val = batch_texts_2d[i, j]
                    prompt_str = text_val.decode("utf-8") if isinstance(text_val, bytes) else text_val
                    flattened_prompts.append(prompt_str)

            # We'll generate text for each prompt in flattened_prompts
            # Then reshape back into (batch_size, text_len).
            outputs_2d = []
            idx = 0
            for i in range(batch_size):
                row_outputs = []
                for j in range(text_len):
                    prompt = flattened_prompts[idx]
                    idx += 1
                    out = self.pipe(
                        prompt,
                        max_length=256,
                        num_return_sequences=1,
                        do_sample=True,
                        top_k=50,
                        top_p=0.9,
                        temperature=0.7
                    )
                    row_outputs.append(out[0]["generated_text"])
                outputs_2d.append(row_outputs)

            # Convert outputs_2d back to a numpy array of shape (batch_size, text_len).
            out_tensor = pb_utils.Tensor(
                "GENERATED_TEXT", np.array(outputs_2d, dtype=object)
            )
            inference_response = pb_utils.InferenceResponse(output_tensors=[out_tensor])
            responses.append(inference_response)
        return responses

    def finalize(self):
        pass
EOF

###############################################################################
# 6. VERIFY TRITON IMAGE
###############################################################################
echo ">>> Confirming custom Triton image exists..."
docker images | grep tritonserver

###############################################################################
# 7. RUN TRITON SERVER IN THE BACKGROUND
###############################################################################
echo ">>> Stopping and removing any previous container named '${CONTAINER_NAME}' if exists..."
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}\$"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

echo ">>> Starting Triton server container with custom image: ${TRITON_IMAGE}"
docker run -d \
  --gpus=all \
  --name "${CONTAINER_NAME}" \
  -p ${HTTP_PORT}:8000 \
  -p ${GRPC_PORT}:8001 \
  -p ${METRICS_PORT}:8002 \
  -v "${TRITON_HOME}/model_repository":/models \
  "${TRITON_IMAGE}" \
  tritonserver --model-repository=/models --log-verbose=1

# Give Triton some time to spin up
echo ">>> Waiting 15 seconds for Triton to initialize..."
sleep 15

###############################################################################
# 8. TEST INFERENCE USING TRITON PYTHON CLIENT
###############################################################################
echo ">>> Creating test_inference.py..."
cat <<EOF > test_inference.py
import numpy as np
import tritonclient.http as httpclient

model_name = "${TRITON_MODEL_NAME}"
server_url = "localhost:${HTTP_PORT}"

try:
    client = httpclient.InferenceServerClient(url=server_url)
except Exception as e:
    print("Failed to create Triton client:", e)
    exit(1)

#
# Because dims: [-1] with max_batch_size, the server sees [batch_size, text_length].
# For a single prompt, let text_length = 1, so shape is [1,1].
#
input_data = np.array([["Hello, can you explain what large language models are?"]], dtype=object)
input0 = httpclient.InferInput("TEXT", [1, 1], "BYTES")
input0.set_data_from_numpy(input_data)

output0 = httpclient.InferRequestedOutput("GENERATED_TEXT")

try:
    results = client.infer(
        model_name,
        inputs=[input0],
        outputs=[output0],
    )
    # The model.py returns shape [batch_size, text_length].
    # That's [1,1] here. So results.as_numpy("GENERATED_TEXT") is shape (1,1).
    generated_text = results.as_numpy("GENERATED_TEXT")
    batch_size, text_len = generated_text.shape
    print(f">>> Got output shape: {generated_text.shape}")
    # For our single prompt, that's (1,1). Let's print the single generated string:
    resp = generated_text[0, 0]
    response_text = resp.decode("utf-8") if isinstance(resp, bytes) else resp
    print(">>> Model response (batch_size=1, text_len=1):")
    print(response_text)
except Exception as e:
    print("Inference failed:", e)
    exit(1)

# (Optional) Demonstrate multiple prompts in one request:
# multi_data = np.array([
#     ["Hello from prompt #1!"],
#     ["And hello from prompt #2!"]
# ], dtype=object)
# multi_input = httpclient.InferInput("TEXT", [2, 1], "BYTES")
# multi_input.set_data_from_numpy(multi_data)
# multi_results = client.infer(
#     model_name,
#     inputs=[multi_input],
#     outputs=[output0],
# )
# # multi_results is shape (2,1)
# multi_out = multi_results.as_numpy("GENERATED_TEXT")
# for i in range(multi_out.shape[0]):
#     for j in range(multi_out.shape[1]):
#         val = multi_out[i, j]
#         print(f"Output for prompt {i}:", val.decode("utf-8") if isinstance(val, bytes) else val)
EOF

echo ">>> Testing inference with custom Triton server: python3 test_inference.py"
python3 test_inference.py || {
  echo ">>> Inference test encountered an error. Check container logs with: docker logs ${CONTAINER_NAME}"
  exit 1
}

echo ">>> Done!"
echo "You can view the Triton server logs with: docker logs ${CONTAINER_NAME}"
echo "Stop the container with: docker rm -f ${CONTAINER_NAME}"
