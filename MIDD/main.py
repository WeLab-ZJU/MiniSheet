from utils import *
import tifffile as tf
import matplotlib.pyplot as plt
import self_learn_base as sl
import torch
np.random.seed(2)
if __name__ == "__main__":
    z_slice = 50
    angle = [10,0,-10]
    stripe_amplitude = 0.8
    noise_level = 0.02
    background = 0.1

    channel = 32
    epochs = 1000

    org = tf.imread("data/org.tif")[z_slice].astype(np.float32)
    org += background
    org /= np.max(org)
    
    raw1 = forward_model(org, angle=angle[0], stripe_amplitude=stripe_amplitude, noise_level=noise_level)
    raw2 = forward_model(org, angle=angle[0], stripe_amplitude=stripe_amplitude, noise_level=noise_level)
    raw3 = forward_model(org, angle=angle[0], stripe_amplitude=stripe_amplitude, noise_level=noise_level)
    raws = torch.zeros((3,1,org.shape[0],org.shape[1])).float()
    raws[0,0] = torch.from_numpy(raw1)
    raws[1,0] = torch.from_numpy(raw2)
    raws[2,0] = torch.from_numpy(raw3)

    
    
    net = sl.SelfCNN(channel_base=channel)
    res_self,loss_list = sl.train(net.cuda(),raws.cuda(),epochs)

    tf.imwrite('result/result.tif',res_self)
    tf.imwrite('result/raw1.tif',raw1)
    tf.imwrite('result/raw2.tif',raw2)
    tf.imwrite('result/raw3.tif',raw3)
