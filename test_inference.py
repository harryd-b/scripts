import numpy as np
import tritonclient.http as httpclient

model_name = "meta-llama_Meta-Llama-3-8B"
server_url = "localhost:8000"

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
