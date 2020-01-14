import numpy as np
import torch
from torchvision.utils import make_grid

from ml.base import BaseValidationPt
from ml.commons.metrics import iou, precision, recall, f_score
from ml.commons.utils.torch_tensor_conversion import cuda_variable


class BuildingBoundaryValidation(BaseValidationPt):
    def __init__(self):
        self.iou_building = list()
        self.precision_building = list()
        self.recall_building = list()
        self.f_score_building = list()

        self.iou_boundary = list()
        self.precision_boundary = list()
        self.recall_boundary = list()
        self.f_score_boundary = list()

    def compute_metric(self, targets, outputs):
        building_targets = targets[:, 0:1, :, :]
        boundary_targets = targets[:, 1:2, :, :]

        building_outputs = outputs[:, 0:1, :, :]
        boundary_outputs = outputs[:, 1:2, :, :]

        self.iou_building += [
            iou(building_targets, (building_outputs > 0).float()).item()
        ]
        self.precision_building += [
            precision(building_targets, (building_outputs > 0).float()).item()
        ]
        self.recall_building += [
            recall(building_targets, (building_outputs > 0).float()).item()
        ]
        self.f_score_building += [
            f_score(building_targets, (building_outputs > 0).float()).item()
        ]

        self.iou_boundary += [
            iou(boundary_targets, (boundary_outputs > 0).float()).item()
        ]
        self.precision_boundary += [
            precision(building_targets, (boundary_outputs > 0).float()).item()
        ]
        self.recall_boundary += [
            recall(boundary_targets, (boundary_outputs > 0).float()).item()
        ]
        self.f_score_boundary += [
            f_score(boundary_targets, (boundary_outputs > 0).float()).item()
        ]

    def get_computed_mean_metric(self, **kwargs):
        self.iou_building = np.mean(self.iou_building)
        self.precision_building = np.mean(self.precision_building)
        self.recall_building = np.mean(self.recall_building)
        self.f_score_building = np.mean(self.f_score_building)

        self.iou_boundary = np.mean(self.iou_boundary)
        self.precision_boundary = np.mean(self.precision_boundary)
        self.recall_boundary = np.mean(self.recall_boundary)
        self.f_score_boundary = np.mean(self.f_score_boundary)

        metrics = self.generate_dictionary()
        self._re_initialize_metric_variables()

        return metrics

    def generate_dictionary(self):
        metrics = {
            "Building IOU": self.iou_building,
            "Building Precision": self.precision_building,
            "Building Recall": self.recall_building,
            "Building F_Score": self.f_score_building,
            "Boundary IOU": self.iou_boundary,
            "Boundary Precision": self.precision_boundary,
            "Boundary Recall": self.recall_boundary,
            "Boundary F_Score": self.f_score_boundary,
        }
        return metrics

    def generate_inference_output(self, img):
        _, w, h = img.shape

        merged_image = np.zeros((w, h, 3))
        building_image = img[0:1, :, :]
        boundary_image = img[1:2, :, :]

        building_image = building_image.sigmoid().data.cpu().numpy()
        boundary_image = boundary_image.sigmoid().data.cpu().numpy()

        building_image = building_image.reshape((w, h, 1))
        boundary_image = boundary_image.reshape((w, h, 1))

        building_image[building_image >= 0.30] = 255
        building_image[building_image < 0.30] = 0

        boundary_image[boundary_image >= 0.10] = 255
        boundary_image[boundary_image < 0.10] = 0

        boundary_image = np.concatenate(3 * (boundary_image,), axis=-1)
        building_image = np.concatenate(3 * (building_image,), axis=-1)

        merged_image[np.where((building_image == [(255, 255, 255)]).all(axis=2))] = [
            (255, 0, 0)
        ]
        merged_image[np.where((boundary_image == [(255, 255, 255)]).all(axis=2))] = [
            (0, 255, 0)
        ]

        return merged_image

    def _re_initialize_metric_variables(self):
        self.jaccard = []
        self.precision_metric = []
        self.recall_metric = []
        self.f_score_metric = []

    @staticmethod
    def create_prediction_grid(inputs, prediction):
        prediction = prediction.sigmoid()
        prediction = prediction[:, 0:1, :, :]
        display_image = cuda_variable(inputs)
        display_image = torch.FloatTensor(display_image["image"].cpu())
        grid = make_grid(prediction, nrow=2, normalize=True)
        nda = grid.mul(255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
        grid_sat = make_grid(display_image, nrow=2, normalize=True)
        grid_sat_nda = (
            grid_sat.mul(255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
        )

        return np.vstack((nda, grid_sat_nda))
