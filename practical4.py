# coding: utf-8
import json
import time
import torch
import torch.nn as mods
import torch.nn.functional as F
from experiment import Experimenter
from dlc_practical_prologue import load_data, args


class CustomNet(torch.nn.Module):

    def __init__(self, hidden_units=200):
        super(CustomNet, self).__init__()
        self.conv1 = mods.Conv2d(1, 32, kernel_size=5)
        self.conv2 = mods.Conv2d(32, 64, kernel_size=5)
        self.fc1 = mods.Linear(256, hidden_units)
        self.fc2 = mods.Linear(hidden_units, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), kernel_size=3, stride=3))
        x = F.relu(F.max_pool2d(self.conv2(x), kernel_size=2, stride=2))
        x = x.view(-1, 256)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class CustomNetConv3(torch.nn.Module):

    def __init__(self, hidden_units=200):
        super(CustomNetConv3, self).__init__()
        self.conv1 = mods.Conv2d(1, 16, kernel_size=3)
        self.conv2 = mods.Conv2d(16, 32, kernel_size=4)
        self.conv3 = mods.Conv2d(32, 64, kernel_size=2)
        self.fc1 = mods.Linear(256, hidden_units)
        self.fc2 = mods.Linear(hidden_units, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2))
        x = F.relu(F.max_pool2d(self.conv3(x), 2))
        x = x.view(-1, 256)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class CustomNetTrainer(object):

    def __init__(self, model, data, parameters):
        self.model = model
        self.data = data
        self.params = parameters
        self.loss = mods.MSELoss()
        self.optimizer = torch.optim.SGD(model.parameters(), lr=self.params['eta'])

    def train(self):
        training_start = time.perf_counter()
        for step in range(self.params['steps']):
            self._train_step(step, training_start)
        return self._compute_test_error()

    def _train_step(self, step, training_start):
        chunk_nb = int(self.data['training_input'].size(0)/self.params['minibatch_size'])
        data_batches = torch.chunk(self.data['training_input'], chunk_nb)
        target_batches = torch.chunk(self.data['training_target'], chunk_nb)

        for data_batch, target_batch in zip(data_batches, target_batches):
            self._minibatch_step(data_batch, target_batch)

    def _print_step_data(self, step, training_start):
        with torch.no_grad():
            print("Step: {}, test error: {:.1f}%, time elapsed: {}s".format(
                step,
                self._compute_test_error() * 100,
                int(time.perf_counter() - training_start)
            ))

    def _minibatch_step(self, data_batch, target_batch):
        tr_loss = self.loss(self.model(data_batch), target_batch)
        self.optimizer.zero_grad()
        tr_loss.backward()
        self.optimizer.step()

    def _display_stats(self, step, training_start):
        with torch.no_grad():
            tr_error, test_error = self._compute_errors()
            print("Step {} : Loss {}, error {} %, test error: {} %, elapsed time: {}s".format(
                step,
                self.loss(self.model(self.data['training_input']), self.data['training_target']),
                100.0 * tr_error,
                100.0 * test_error,
                int(time.perf_counter() - training_start)
            ))

    def _compute_errors(self):
        '''Computes training error and test error'''
        tr_error = torch.nonzero(
            torch.argmax(self.data['training_target'], dim=1)
            - torch.argmax(self.model(self.data['training_input']), dim=1)
        ).size(0) / self.data['training_input'].size(0)

        return tr_error, self._compute_test_error()

    def _compute_test_error(self):
        return torch.nonzero(
            torch.argmax(self.data['test_target'], dim=1)
            - torch.argmax(self.model(self.data['test_input']), dim=1)
        ).size(0) / self.data['test_input'].size(0)


# Initialize data
train_data, train_target, test_data, test_target = load_data(
    normalize=True,
    one_hot_labels=True,
    flatten=False,
)
# zeta = 0.9
# train_target *= zeta

data = dict(
    training_input=train_data,
    training_target=train_target,
    test_input=test_data,
    test_target=test_target,
)

parameters = dict(
    steps=25,
    eta=0.1,
    minibatch_size=args.batchsize,
)

default_trainer = CustomNetTrainer(CustomNet(), data, parameters)


def hidden_layer_xp(hidden_layer_size):
    return CustomNetTrainer(CustomNet(hidden_layer_size), data, parameters).train()


def conv3_xp(convnet):
    parameters['step'] = 100
    return CustomNetTrainer(convnet(), data, parameters).train()


def conv3_experiment():
    # 3 conv layer experiment (ex. 4)
    results = Experimenter(conv3_xp).experiment(
        {'convnet': [CustomNetConv3, CustomNet]},
        iterations=5
    )
    with open("conv3_xp_{}_{}.json".format(args.suffix, int(time.time())), 'w') as res_file:
        json.dump(results, res_file)


def hidden_layer_experiment():
    # Hidden layer experiment (ex. 3)
    results = Experimenter(hidden_layer_xp).experiment(
        {'hidden_layer_size': [10, 50, 200, 500, 1000]},
        iterations=5
    )
    with open("hidden_layer_xp_{}_{}.json".format(args.suffix, int(time.time())), 'w') as res_file:
        json.dump(results, res_file)


if __name__ == '__main__':
    conv3_experiment()
