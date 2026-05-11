import os
import torch
import torchvision.transforms as T
import numpy as np
import cv2
from PIL import Image


class CNN:
    """
    Trích vector đặc trưng ảnh bằng DINOv2 ViT-B/14.
    Output: vector 768 chiều, đã L2-normalize.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        use_cuda = self.device.type == "cuda"

        if use_cuda:
            device_name = torch.cuda.get_device_name(0)
            print(f"[CNN] Using device: cuda ({device_name})")

            enable_tf32 = os.getenv("CNN_ENABLE_TF32", "0") == "1"
            enable_benchmark = os.getenv("CNN_CUDNN_BENCHMARK", "1") == "1"

            if enable_tf32:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                if hasattr(torch, "set_float32_matmul_precision"):
                    torch.set_float32_matmul_precision("high")

            if enable_benchmark:
                torch.backends.cudnn.benchmark = True

            print(
                f"[CNN] TF32={'on' if enable_tf32 else 'off'}, "
                f"cuDNN benchmark={'on' if enable_benchmark else 'off'}"
            )
        else:
            print("[CNN] Using device: cpu")

        self.model = torch.hub.load(
            "facebookresearch/dinov2",
            "dinov2_vitb14",
            pretrained=True
        )
        self.model = self.model.to(self.device)
        self.model.eval()

        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(
                mean=[0.485, 0.456, 0.406],
                std =[0.229, 0.224, 0.225],
            )
        ])

    def extract(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Args:
            img_bgr: numpy array (H, W, 3) BGR — format OpenCV

        Returns:
            vec: numpy array (768,) float32, đã L2-normalize
        """
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        tensor  = self.transform(Image.fromarray(img_rgb))
        tensor  = tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            vec = self.model(tensor)        # (1, 768)

        vec = vec.squeeze().cpu().numpy().astype(np.float32)

        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec /= norm

        return vec                          # (768,)

    def extract_batch(self, imgs_bgr: list) -> np.ndarray:
        """
        Args:
            imgs_bgr: list of numpy array BGR

        Returns:
            vecs: numpy array (N, 768) float32, đã L2-normalize từng hàng
        """
        tensors = []
        for img in imgs_bgr:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            tensors.append(self.transform(Image.fromarray(img_rgb)))

        batch = torch.stack(tensors).to(self.device)

        with torch.no_grad():
            vecs = self.model(batch)        # (N, 768)

        vecs  = vecs.cpu().numpy().astype(np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms < 1e-10, 1.0, norms)

        return vecs / norms                 # (N, 768)