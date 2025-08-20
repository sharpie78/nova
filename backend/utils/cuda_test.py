
import onnxruntime as ort

# Check if CUDA is available
providers = ort.get_available_providers()
print("Available providers:", providers)

# Specifically check for CUDA
if 'CUDAExecutionProvider' in providers:
    print("CUDA is available!")
else:
    print("CUDA is NOT available.")
