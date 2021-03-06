import os
import sys
import copy
import random
import argparse
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from sklearn.metrics import f1_score

import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.utils.checkpoint as cp
from torchvision import datasets, models, transforms

from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets

class Model:
	def set_parameter_requires_grad(self, model, feature_extracting):
	    if feature_extracting:
	        for param in model.parameters():
	            param.requires_grad = False
	            
	def initialize_model(self, use_pretrained=True):
	    self.model_ft = None
	    self.input_size = 0
	    self.crop_size = 0

	    if self.modelname == "resnet":  # ResNet-50
	        self.model_ft = models.resnet50(pretrained=use_pretrained)
	        self.set_parameter_requires_grad(self.model_ft, self.feature_extract)
	        num_ftrs = self.model_ft.fc.in_features
	        self.model_ft.fc = nn.Linear(num_ftrs, self.num_classes)
	        self.input_size = 224
	        self.crop_size = 224

	    elif self.modelname == "vgg":  # VGG-11
	        self.model_ft = models.vgg11_bn(pretrained=use_pretrained)
	        self.set_parameter_requires_grad(self.model_ft, self.feature_extract)
	        num_ftrs = self.model_ft.classifier[6].in_features
	        self.model_ft.classifier[6] = nn.Linear(num_ftrs,self.num_classes)
	        self.input_size = 224
	        self.crop_size = 224

	    elif self.modelname == "densenet":  # DenseNet-121
	        self.model_ft = models.densenet121(pretrained=use_pretrained)
	        self.set_parameter_requires_grad(self.model_ft, self.feature_extract)
	        num_ftrs = self.model_ft.classifier.in_features
	        self.model_ft.classifier = nn.Linear(num_ftrs, self.num_classes)
	        self.input_size = 224
	        self.crop_size = 224
	    
	    elif self.modelname == "inception":
	        self.model_ft = models.inception_v3(pretrained=use_pretrained, aux_logits=False)
	        self.set_parameter_requires_grad(self.model_ft, self.feature_extract)
	        num_ftrs = self.model_ft.fc.in_features
	        self.model_ft.fc = nn.Linear(num_ftrs, self.num_classes+1)
	        self.input_size = 299
	        self.crop_size = 299
	    
	    elif self.modelname == "resnext":
	        self.model_ft = models.resnext50_32x4d(pretrained=use_pretrained)
	        self.set_parameter_requires_grad(self.model_ft, self.feature_extract)
	        num_ftrs = self.model_ft.fc.in_features
	        self.model_ft.fc = nn.Linear(num_ftrs, self.num_classes)
	        self.input_size = 224
	        self.crop_size = 224

	def get_model_name(self):
		print(self.modeldir)
		if "resnext" in self.modeldir.lower():
			self.modelname = "resnext"
		elif "inception" in self.modeldir.lower():
			self.modelname = "inception"
		elif "densenet" in self.modeldir.lower():
			self.modelname = "densenet"
		else:
			return False
		return True

	def load_weights(self):
		model_weights = torch.load(self.modeldir, map_location = self.device)
		self.model_ft.load_state_dict(model_weights)
		print('Loaded weights')
		self.model_ft = self.model_ft.to(self.device)
		self.model_ft.eval()

	def single_image_loader(self, loader, image_name):
	    image = Image.open(image_name)
	    image = loader(image).float()
	    image = torch.tensor(image, requires_grad = True)
	    image = image.unsqueeze(0)
	    return image

	def predict(self, image_dir):
		data_transforms = transforms.Compose([
		    transforms.Resize(256),
		    transforms.CenterCrop(224),
		    transforms.ToTensor()
		])
		pred = self.model_ft(self.single_image_loader(data_transforms, image_dir))
		_, pred = torch.max(pred, 1)
		try:
			return "The class label is: " + str(self.classes[pred][0]) + ".\nClass index is: " + str(self.classes[pred][0])
		except:
			return "Some error... Try another image"

	def __init__(self, modeldir):
		self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
		self.modeldir = modeldir
		self.num_classes = 45
		self.feature_extract = False
		self.classes = None
		self.model_ft = None
		self.classes = [['thamnophis_proximus',4], ['nerodia_sipedon',67], ['opheodrys_vernalis',72], ['crotalus_horridus',78], ['crotalus_pyrrhus',128], ['nerodia_rhombifer',140], ['thamnophis_sirtalis',204], ['natrix_natrix',239], ['crotalus_adamanteus',273], ['charina_bottae',326], ['pituophis_catenifer',337], ['lampropeltis_triangulum',362], ['nerodia_erythrogaster',390], ['thamnophis_marcianus',394], ['lampropeltis_californiae',448], ['crotalus_ruber',450], ['rhinocheilus_lecontei',460], ['opheodrys_aestivus',508], ['thamnophis_ordinoides',526], ['thamnophis_radix',536], ['masticophis_flagellum',540], ['pantherophis_vulpinus',543], ['hierophis_viridiflavus',561], ['heterodon_platirhinos',581], ['pantherophis_emoryi',597], ['regina_septemvittata',629], ['haldea_striatula',635], ['diadophis_punctatus',639], ['nerodia_fasciata',653], ['storeria_occipitomaculata',654], ['crotalus_scutulatus',663], ['storeria_dekayi',697], ['crotalus_viridis',707], ['boa_imperator',734], ['pantherophis_obsoletus',771], ['lichanura_trivirgata',784], ['agkistrodon_contortrix',804], ['thamnophis_elegans',811], ['agkistrodon_piscivorus',854], ['pantherophis_guttatus',857], ['crotalus_atrox',872], ['carphophis_amoenus',957], ['coluber_constrictor',966], ['pantherophis_spiloides',1059], ['pantherophis_alleghaniensis',1625]]

		got_model_name = self.get_model_name()
		print(got_model_name)
		if got_model_name:
			self.initialize_model()
			print("Loaded " + self.modelname + " model")
			self.load_weights()
		else:
			return
		

class MainWindow(QtWidgets.QMainWindow):
	
	def SelectModel(self):
		modelname = QtWidgets.QFileDialog.getOpenFileName()[0]
		if modelname == "":
			return
		print(modelname)
		self.model = Model(modelname)
		if self.model.model_ft == None:
			self.outLabel.setText("Cannot load model")
			return
		else:
			self.outLabel.setText("Loaded model")
		if self.image != None:
			self.predict.setStyleSheet("background-color: green; font: white")

	def SelectImage(self):
		imagename = QtWidgets.QFileDialog.getOpenFileName()[0]
		self.image = imagename
		if self.image == "":
			return
		print("Image loaded")
		print(self.image)
		imagename = imagename.split("/")[-1]
		self.outLabel.setText("Loaded image: " + imagename)
		if self.model != None:
			self.predict.setStyleSheet("background-color: green; font: white")

	def Predict(self):
		if self.image == None:
			self.outLabel.setText("Provide a valid image")
			return
		if self.model == None:
			self.outLabel.setText("Provide a valid model")
			return
		pred = self.model.predict(self.image)
		print(pred)
		self.outLabel.setText(str(pred))

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		uic.loadUi("mainwindow.ui", self)

		self.model = None
		self.image = None

		self.predict.setStyleSheet("background-color: red; font: white")
		self.selectModel.clicked.connect(self.SelectModel)
		self.selectImage.clicked.connect(self.SelectImage)
		self.predict.clicked.connect(self.Predict)

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()