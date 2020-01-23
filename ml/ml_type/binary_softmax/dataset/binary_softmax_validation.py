import torch
import numpy as np
from torchvision.utils import make_grid

from ml.base import BaseValidationPt
from ml.commons.metrics import (
    calculate_confusion_matrix_from_arrays,
    calculate_iou_on_confusion_matrix,
)
from ml.commons.utils.torch_tensor_conversion import cuda_variable


class BinarySoftmaxValidation(BaseValidationPt):
    def __init__(self):
        self.iou = None
        self.confusion_matrix = np.zeros((2, 2), dtype=np.uint32)

    def compute_metric(self, targets, outputs):
        outputs = outputs.log_softmax(dim=1)
        output_classes = outputs.data.cpu().numpy().argmax(axis=1)
        target_classes = targets.data.cpu().numpy()

        confusion = calculate_confusion_matrix_from_arrays(
            output_classes, target_classes, 2
        )
        self.confusion_matrix += confusion

    def get_computed_mean_metric(self, **kwargs):
        confusion_matrix = self.confusion_matrix[1:, 1:]
        self.iou = np.mean(calculate_iou_on_confusion_matrix(confusion_matrix))
        metrics = self.generate_dictionary()
        self._re_initialize_metric_variables()
        return metrics

    def _re_initialize_metric_variables(self):
        self.confusion_matrix = np.zeros((2, 2), dtype=np.uint32)

    def generate_dictionary(self):
        metrics = {"IOU": self.iou}
        return metrics

    def generate_inference_output(self, img):
        img = torch.argmax(img.log_softmax(dim=0), dim=0)
        img = img.data.cpu().numpy()
        return img

    @staticmethod
    def create_prediction_grid(inputs, prediction):
        prediction = torch.argmax(prediction.log_softmax(dim=1), dim=1)
        display_image = cuda_variable(inputs)
        display_image = torch.FloatTensor(display_image["image"].cpu())
        grid = make_grid(prediction, nrow=2, normalize=True)
        nda = grid.mul(255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
        grid_sat = make_grid(display_image, nrow=2, normalize=True)
        grid_sat_nda = (
            grid_sat.mul(255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
        )

        return np.vstack((nda, grid_sat_nda))
