# -*- coding: utf-8 -*-
"""VGG.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xHikNfm0mrqDiIu_UDBcRDIuABgzwGj5
"""

import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F

class Flatten(nn.Module):
    def forward(self, x):
        return x.view(x.size(0), -1)
        
class View(nn.Module):
    def __init__(self, channels, height, width):
        super(View, self).__init__()
        self.channels = channels
        self.height = height
        self.width = width

    def forward(self, x):
        # batch_size, channels, height, width
        return x.view(x.size(0), self.channels, self.height, self.width)
        
class Interpolate(nn.Module):
    def __init__(self):
        super(Interpolate, self).__init__()
        self.interp = nn.functional.interpolate
        
    def forward(self, x):
        x = self.interp(x, scale_factor=2)
        return x

def VGG(rep_dim=4900, kind='autoencoder'):
    cfg = [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M', 'C']
    kind = kind.lower()
    try:
        assert kind in ['encoder', 'decoder', 'classifier', 'autoencoder']
    except:
        raise ValueError('kind \'{}\' not in [encoder, decoder, classifier, autoencoder]'.format(kind))
    
    encoder = []
    in_channels = 1
    for v in cfg:
        if v == 'M':
            encoder += [nn.MaxPool2d(kernel_size=2, stride=2)]
        elif v == 'C':
            encoder += [nn.AdaptiveAvgPool2d((7, 7))]
            encoder += [Flatten()]
            encoder += [nn.Linear(512 * 7 * 7, 4096, bias=False), nn.ReLU(inplace=True), nn.Dropout()] 
            encoder += [nn.Linear(4096, 4096, bias=False), nn.ReLU(inplace=True), nn.Dropout()]
            encoder += [nn.Linear(4096, rep_dim, bias=False)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=5, padding=2, bias=False)
            encoder += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            
            in_channels = v
            
    if kind == 'classifier' or kind =='encoder':
        return nn.Sequential(*encoder)
     
    in_channels, out_channels = None, None
    cfg = [-1, 1] + cfg
    
    decoder = []
    for v in reversed(cfg):
        if v == 'M':
            decoder += [Interpolate()]
        elif v == 'C':
            decoder += [nn.Linear(rep_dim, 4096, bias=False)]
            decoder += [nn.Linear(4096, 4096, bias=False), nn.ReLU(inplace=True), nn.Dropout()]
            decoder += [nn.Linear(4096, 512 * 7 * 7, bias=False), nn.ReLU(inplace=True), nn.Dropout()]
            decoder += [View(512, 7, 7)]
            decoder += [nn.AdaptiveAvgPool2d((7, 7))]

        else:
            if in_channels is None:
                in_channels = v
                continue
            
            if out_channels is None:
                out_channels = v
                continue
                
            conv2d = nn.Conv2d(in_channels, out_channels, kernel_size=5, padding=2, bias=False)
            decoder += [conv2d, nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True)]
            
            in_channels = out_channels
            out_channels = v
    
    if kind == 'decoder':
        return nn.Sequential(*decoder)
        
    if kind == 'autoencoder':
        layers = encoder + decoder
        return nn.Sequential(*layers)