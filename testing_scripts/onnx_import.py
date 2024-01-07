import onnxruntime as rt
import cv2
import onnx
from onnx import numpy_helper
import numpy as np 

# import torch 
# Load the ONNX model
# onnx_path = "/home/maxwell/Propagation_explainers/alexnet.onnx"
onnx_path = "/home/maxwell/detectron2_ws/detectron2/tools/deploy/pano_R101/model.onnx"


session = rt.InferenceSession(onnx_path)

# get the name of the first input of the model
input_info = session.get_inputs()[0]  
input_name = input_info.name

print('Input Name:', input_name)

def preprocess(input_data):
    # convert the input data into the float32 input
    img_data = input_data.astype('float32')

    #normalize
    mean_vec = np.array([0.485, 0.456, 0.406])
    stddev_vec = np.array([0.229, 0.224, 0.225])
    norm_img_data = np.zeros(img_data.shape).astype('float32')
    for i in range(img_data.shape[0]):
        norm_img_data[i,:,:] = (img_data[i,:,:]/255 - mean_vec[i]) / stddev_vec[i]
        
    #add batch channel
    norm_img_data = norm_img_data.reshape(1, 3, 224, 224).astype('float32')
    return norm_img_data


def softmax(x):
    x = x.reshape(-1)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def postprocess(result):
    return softmax(np.array(result))

test_img_fn = "/home/maxwell/coco/images/val2017/000000001584.jpg"
img = cv2.resize(cv2.imread(test_img_fn), (224,224))
print(img.shape)

image_data = img.transpose(2, 0, 1)
input_data = preprocess(image_data)

# input_data = np.concatenate((input_data,)*10, axis = 0)
print(input_data.shape)

raw_result = session.run([], {input_name: input_data})
res = postprocess(raw_result)

print(res.shape)

idx = np.argmax(res)

print(idx)