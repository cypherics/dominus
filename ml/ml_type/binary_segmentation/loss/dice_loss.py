from ml.base.base_loss.base_pt_loss import BaseLoss

from torch import nn


def calculate_dice(outputs, targets):
    dice = (2.0 * (outputs * targets).sum() + 1) / (outputs.sum() + targets.sum() + 1)
    return dice


class DiceLoss(BaseLoss):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nll_loss = nn.BCEWithLogitsLoss()
        self.dice_weights = kwargs["dice_weight"]

    def compute_loss(self, outputs, **kwargs):
        targets = kwargs["label"]
        bce_loss = self.nll_loss(outputs, targets)

        outputs = outputs.sigmoid()
        dice_loss = calculate_dice(outputs, targets)
        loss = bce_loss + self.dice_weights * (1 - dice_loss)
        return loss