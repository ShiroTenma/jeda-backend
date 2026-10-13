import io
import time
from pathlib import Path
import numpy as np
from PIL import Image
import onnxruntime as ort

class VisualClassifier:
    """Singleton ONNX inference engine using CPUExecutionProvider."""
    
    _instance: "VisualClassifier | None" = None

    def __init__(self, model_path: str = "models/baseline_classifier.onnx"):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at {model_path}")

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    @classmethod
    def get_instance(cls, model_path: str = "models/baseline_classifier.onnx") -> "VisualClassifier":
        if cls._instance is None:
            cls._instance = cls(model_path)
        return cls._instance

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Decodes image bytes, resizes to 224x224 RGB, normalizes to NCHW float32."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((224, 224), Image.Resampling.BILINEAR)
        arr = np.array(image, dtype=np.float32) / 255.0  # [224, 224, 3]
        
        # Standard ImageNet normalization: (x - mean) / std
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std

        # Transpose HWC -> CHW, add batch dimension -> NCHW [1, 3, 224, 224]
        arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, axis=0)
        return arr

    def infer(self, image_bytes: bytes) -> tuple[float, float]:
        """Runs inference. Returns (risk_confidence: float [0..1], latency_ms: float)."""
        t0 = time.perf_counter()
        tensor = self.preprocess(image_bytes)
        outputs = self.session.run([self.output_name], {self.input_name: tensor})
        latency_ms = (time.perf_counter() - t0) * 1000.0

        probs = outputs[0][0]
        # Assume class 1 represents target risk / explicit confidence
        risk_confidence = float(probs[1]) if len(probs) > 1 else float(probs[0])
        return risk_confidence, latency_ms
