# -*- coding: utf-8 -*-
"""main.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TEbNp-AsfVUtycIT9hlfzTUpXkkkHWGE
"""

'''from google.colab import drive
drive.mount('/content/gdrive')
import os
os.getcwd()
os.chdir('/content/gdrive/My Drive/ChestXRay')'''

import numpy as np
import torch

import os
import random
import logging
import time
from datetime import datetime

from utils.setup_logging import setup_logging
from utils.unzip_data import unzip_data
from utils.dataloaders import get_dataloader

from models.models import get_model
from exp.pretraining import pretrain
from exp.pretesting import pretest
from exp.finding_center import find_center
from exp.training import train
from exp.testing import test

'''
+ load data/
+ perform experiments (train, val and test)
+ write results to logs/

Later versions :
+ download (pull from NIH and filter one file at a time)
'''
def main(model='resnet18', rep_dim=490, dataset='curated', base_path=None, unzip=False, 
         ae_train=True, clf_train=True, ae_epochs=100, clf_epochs=100, 
         batch_size=4, accumulation_steps=32, ae_loadfile=None, clf_loadfile=None,
         save_model=True, ae_test=True, accumulate=False):
    '''
    model : CNN architecture to use ['LeNet', 'VGG', ...]
    data : 'curated' or 'full'
    base_path : path/to/ChestXRay eg. /home/paperspace/ChestXRay
    '''
    if base_path is None:
        raise ValueError('Please point base_path to ChestXRay/')
        
    if ae_train and (ae_loadfile or clf_loadfile):
        raise ValueError('Please either set ae_train to True or specify a loadfile but not both.')
    
    filename = setup_logging(base_path=base_path, model=model, rep_dim=rep_dim)
    logger = logging.getLogger()
    logging.info('Architecture : {}'.format(model))
    logging.info('Representaion Dimensionality : {}'.format(rep_dim))
    logging.info('Dataset : {}'.format(dataset))
        
    if unzip:
        unzip_data(base_path)
   
    trainloader = get_dataloader(dataset=dataset, set_='train', batch_size=batch_size)
    testloader = get_dataloader(dataset=dataset, set_='test', batch_size=batch_size)
    
    #autoencoder = resnet18(num_classes=490, autoencoder=True)
    autoencoder = get_model(model=model, kind='autoencoder', rep_dim=rep_dim)
    if ae_loadfile is not None:
        ae_load_path = os.path.join(base_path, 'models/saved_models/') + ae_loadfile
        autoencoder.load_state_dict(torch.load(ae_load_path), strict=False)
    if ae_train:
        autoencoder = pretrain(trainloader=trainloader, 
                               autoencoder=autoencoder, 
                               ae_epochs=ae_epochs,
                               accumulation_steps=accumulation_steps,
                               accumulate=accumulate)
        
        if save_model:
            save_path = os.path.join(base_path, 'models/saved_models/') + 'ae: ' + filename + '.pt'
            torch.save(autoencoder.state_dict(), save_path)
    
    if ae_test:
        pretest(testloader=testloader, autoencoder=autoencoder)
    del autoencoder
    
    classifier = get_model(model=model, kind='classifier', rep_dim=rep_dim)
    classifier.load_state_dict(torch.load(save_path), strict=False)
    if clf_loadfile is not None:
        clf_load_path = os.path.join(base_path, 'models/saved_models/') + clf_loadfile
        classifier.load_state_dict(torch.load(clf_load_path), strict=False)
    
    c = find_center(trainloader=trainloader, classifier=classifier, rep_dim=rep_dim)
    
    if clf_train:
        classifier = train(trainloader=trainloader,
                           classifier=classifier, 
                           clf_epochs=clf_epochs,
                           accumulation_steps=accumulation_steps,
                           c=c,
                           accumulate=accumulate)
        
        if save_model:
            save_path = os.path.join(base_path, 'models/saved_models/') + 'clf: ' + filename + '.pt'
            torch.save(classifier.state_dict(), save_path)
        
    test(testloader=testloader, classifier=classifier, c=c)
    return

if __name__ == '__main__':
    main()

'''main(base_path='/content/gdrive/My Drive/ChestXRay', 
     model='resnet18', rep_dim=4900, ae_epochs=10, clf_epochs=10, dataset='clean', ae_train=True, ae_test=True, accumulation_steps=16)'''

