from plugins.base.base_factory import Factory
from plugins.binary import network, criterion
from plugins.binary.binary_data_set import BinaryDataSet
from plugins.binary.binary_extension import BinaryExtension


class BinaryFactory(Factory):
    def __init__(self, config):
        self.config = config
        super(BinaryFactory, self).__init__(config)

    def create_data_set(self):
        return BinaryDataSet.get_data_loader(self.config)

    def create_criterion(self, criterion_name, criterion_param):
        criterion_fn = getattr(criterion, criterion_name)(**criterion_param)
        return criterion_fn

    def create_network(self, model_name, model_param):
        model = getattr(network, model_name)(**model_param)
        return model

    def create_extension(self):
        return BinaryExtension(self.config)
