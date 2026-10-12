import numpy as np
import torch 
import torch.nn as nn
import os
from torch.nn import functional as F
from utils import *
import zs_n2n
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
class ResidualBlock(nn.Module):
    def __init__(self, channel_base):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channel_base, channel_base, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(channel_base, channel_base, kernel_size=3, stride=1, padding=1)
        self.relu = nn.LeakyReLU(0.2)
    def forward(self, x):
        out = self.relu(self.conv1(x))
        out = self.conv2(out)
        out = out + x
        return out
    
class SelfCNN(nn.Module):
    def __init__(self, channel_base):
        super(SelfCNN, self).__init__()
        self.relu = nn.LeakyReLU(0.2)
        self.conv1 = nn.Conv2d(1, channel_base, kernel_size=3, stride=1, padding=1)
        self.residual_block = ResidualBlock(channel_base)
        self.conv2 = nn.Conv2d(channel_base, 1, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        out = self.relu(self.conv1(x))
        out = self.residual_block(out)
        out = self.conv2(out)
        return out + x 
    
    def convloss(self, pred, x, lambda_consist = 0.01):
        loss = 1/3 * lambda_consist * torch.mean(pred-x)
        
        for i in range (pred.shape[0]-1):
            x_s = torch.roll(x.clone(), shifts=i+1, dims=0)
            loss = loss + torch.mean(torch.abs(pred-x_s))
        return loss
    
def train(net,raws,epochs,lr=1e-2):
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    loss_list = []

    for epoch in range(epochs):
        optimizer.zero_grad()
        out = net(raws)
        loss = net.convloss(out,raws)
        loss.backward()
        optimizer.step()
        loss_list.append(loss.item())
        if epoch % 10 == 0:
            print("epoch: %d, loss: %f" % (epoch, loss.item()))

    out = out.cpu().detach().numpy()
    res_self = mean_filter(out,0)[0]
    return res_self, loss_list

        