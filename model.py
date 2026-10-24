import torch
import torch.nn as nn
import torch.nn.functional as F

class EntityModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(EntityModel, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initial hidden layer
        self.hidden = nn.Linear(input_size, hidden_size)
        self.output = nn.Linear(hidden_size, output_size)
        
    def forward(self, x, add_layers=None):
        x = F.relu(self.hidden(x))
        
        # Add dynamic layers if any
        if add_layers:
            for layer_size in add_layers:
                dynamic_layer = nn.Linear(self.hidden_size, layer_size)
                x = F.relu(dynamic_layer(x))
                self.hidden_size = layer_size
        
        x = self.output(x)
        return x