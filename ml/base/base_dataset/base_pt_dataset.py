import sys
import numpy as np
from pathlib import Path

from torch.utils.data import Dataset

from ml.commons.utils.image import (
    get_pad_limit,
    pad_image,
    get_random_crop_x_and_y,
    crop_image,
    load_image,
)
from utils.print_format import print_exception
from ml.commons.utils import normalizer, augmentation

from abc import ABCMeta


class BaseDataSetPt(Dataset, metaclass=ABCMeta):
    def __init__(
        self,
        root,
        model_input_dim=None,
        mode="train",
        transform=None,
        normalization=None,
    ):
        if mode == "train":
            self.transform = self.load_transformation(transform)
        else:
            self.transform = None

        self.mode = mode
        self.normalization = self.load_normalization(normalization)
        self.model_input_dimension = tuple(model_input_dim)

        self.root = Path(root)

        self.images = sorted(list((self.root / self.mode / "images").glob("*")))
        self.labels = sorted(list((self.root / self.mode / "labels").glob("*")))

    def __len__(self):
        if len(self.images) != 0:
            return len(self.images)
        else:
            return len(self.labels)

    def __getitem__(self, idx):

        if self.mode in ["train", "val"]:
            img, _ = self.read_data(idx, self.images)
            mask, _ = self.read_data(idx, self.labels)

            input_dictionary = self.perform_image_operation_train_and_val(
                img=img, mask=mask
            )
            assert isinstance(input_dictionary, dict), "Return type should be dict"

            assert (
                "image" in input_dictionary and "label" in input_dictionary
            ), "while passing image use key-image and for label use key-label"

            return input_dictionary

        elif self.mode == "test":
            img, file_name = self.read_data(idx, self.images)
            input_dictionary = self.perform_image_operation_test(img=img)
            assert isinstance(input_dictionary, dict), "Return type should be dict"
            assert "image" in input_dictionary, "while passing image use key-image"

            return input_dictionary, str(file_name)
        else:
            raise NotImplementedError

    def perform_image_operation_train_and_val(self, **kwargs) -> dict:
        raise NotImplementedError

    def perform_image_operation_test(self, **kwargs) -> dict:
        raise NotImplementedError

    def get_label_normalization(self, **kwargs) -> np.ndarray:
        raise NotImplementedError

    def load_transformation(self, transformation_param):
        try:
            transform_type = list(transformation_param.keys())[0]
            transformation_to_perform = list(transformation_param.values())[0]
            number_of_transformation = len(list(transformation_param.values())[0])

            transformation_to_applied = list()
            for i in range(number_of_transformation):
                for _, transform_param in transformation_to_perform.items():
                    transformation_to_applied.append(
                        self._get_train_transformation(**transform_param)
                    )
            if number_of_transformation == 1:
                transformation = transformation_to_applied[0]
            else:
                transformation = getattr(augmentation, transform_type)(
                    transformation_to_applied, prob=0.5
                )
            return transformation

        except Exception as ex:
            print_exception(
                exception=str(ex),
                error_name="Configuration",
                error_message="Configuring Transformation failed",
            )
            sys.exit(1)

    @staticmethod
    def _get_train_transformation(to_perform, transform_type, augment_prob):
        transformation = []
        transforms_type = getattr(augmentation, transform_type)

        for trans in to_perform:
            transformation.append(getattr(augmentation, trans)(prob=augment_prob))

        train_transformation = transforms_type(transformation)
        return train_transformation

    @staticmethod
    def load_normalization(normalization_name):
        try:
            normalization = getattr(normalizer, normalization_name)()
            return normalization

        except Exception as ex:
            print_exception(
                exception=str(ex),
                error_name="Configuration",
                error_message="Configuring normalization failed",
            )
            sys.exit(1)

    @staticmethod
    def handle_image_size(img, mask, model_input_dimension):
        if model_input_dimension < (img.shape[0], img.shape[1]):
            height, width = get_random_crop_x_and_y(model_input_dimension, img.shape)
            img = crop_image(img, model_input_dimension, (height, width))
            if mask is not None:
                mask = crop_image(mask, model_input_dimension, (height, width))
            return img, mask

        elif model_input_dimension > (img.shape[0], img.shape[1]):
            limit = get_pad_limit(model_input_dimension, img.shape)
            img = pad_image(img, limit)
            if mask is not None:
                mask = pad_image(mask, limit)
            return img, mask
        else:
            return img, mask

    def perform_normalization(self, img):
        img = self.normalization(img)
        return img

    def perform_transformation(self, img, mask):
        if self.mode == "train":
            img, mask = self.transform(img, mask)
        return img, mask

    @staticmethod
    def read_data(idx, data_list):
        if len(data_list) != 0:
            image_file_name = data_list[idx]
            image = load_image(str(image_file_name))
            return image, image_file_name
        else:
            return None, None
