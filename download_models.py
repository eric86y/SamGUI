import os
import shutil
from SamGui.Utils import create_dir
from huggingface_hub import snapshot_download

MODEL_REPO = "Eric-23xd/MobileSam_Onnx"


if __name__ == '__main__':
    local_model_dir = "SamGui/Models"
    create_dir(local_model_dir)

    try:
        tmp_path = snapshot_download(
            repo_id=MODEL_REPO,
            repo_type="model",
            local_dir="tmp",
        )
    except BaseException as e:
        print(f"Failed to download default OCR model: {e}")

    assert os.path.isfile("tmp/sam_vit_b_decoder.onnx")
    assert os.path.isfile("tmp/sam_vit_b_encoder.onnx")

    target_file = f"{local_model_dir}/sam_vit_b_decoder.onnx"
    shutil.copy("tmp/sam_vit_b_decoder.onnx", target_file)

    target_file = f"{local_model_dir}/sam_vit_b_encoder.onnx"
    shutil.copy("tmp/sam_vit_b_encoder.onnx", target_file)
