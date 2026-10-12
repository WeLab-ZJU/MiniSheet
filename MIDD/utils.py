import numpy as np
import tifffile as tf

def max_fliter(image_stack, axis=0):
    """
    Apply maximum intensity projection along the specified axis.

    Parameters:
    image_stack (numpy.ndarray): Input 3D image stack.
    axis (int): Axis along which to perform the maximum projection.

    Returns:
    numpy.ndarray: 2D image after maximum intensity projection.
    """
    return np.max(image_stack, axis=axis)

def TV_denoising(image, weight=0.1, num_iter=50):
    """
    Perform Total Variation denoising on a 2D image.

    Parameters:
    image (numpy.ndarray): Input 2D image.
    weight (float): Denoising weight.
    num_iter (int): Number of iterations.

    Returns:
    numpy.ndarray: Denoised 2D image.
    """
    from skimage.restoration import denoise_tv_chambolle
    return denoise_tv_chambolle(image, weight=weight, max_num_iter=num_iter)

def bm3d_denoising(image, sigma=0.1):
    import bm3d
    return bm3d.bm3d(image, sigma_psd=sigma)

def mean_filter(image_stack, axis=0):
    """
    Apply mean intensity projection along the specified axis.

    Parameters:
    image_stack (numpy.ndarray): Input 3D image stack.
    axis (int): Axis along which to perform the mean projection.

    Returns:
    numpy.ndarray: 2D image after mean intensity projection.
    """
    return np.mean(image_stack, axis=axis)
def median_filter(image_stack, axis=0):
    """
    Apply median intensity projection along the specified axis.

    Parameters:
    image_stack (numpy.ndarray): Input 3D image stack.
    axis (int): Axis along which to perform the median projection.

    Returns:
    numpy.ndarray: 2D image after median intensity projection.
    """
    return np.median(image_stack, axis=axis)

def mean_filter_2d(image, kernel_size=3):
    """
    Apply 2D mean filter to a 2D image.

    Parameters:
    image (numpy.ndarray): Input 2D image.
    kernel_size (int): Size of the mean filter kernel.

    Returns:
    numpy.ndarray: Filtered 2D image.
    """
    from scipy.ndimage import uniform_filter
    return uniform_filter(image, size=kernel_size)


def Gabor_filter(image, frequency=0.2, theta=0):
    """
    Apply Gabor filter to a 2D image.

    Parameters:
    image (numpy.ndarray): Input 2D image.
    frequency (float): Frequency of the sinusoidal function.
    theta (float): Orientation of the Gabor filter in radians.

    Returns:
    numpy.ndarray: Filtered 2D image.
    """
    from skimage.filters import gabor
    from skimage.filters import gabor_kernel
    real, imag = gabor(image, frequency=frequency, theta=theta,sigma_x=image.shape[0]/1,sigma_y=3)
    g = gabor_kernel(frequency=frequency, theta=theta,sigma_x=image.shape[0]/1,sigma_y=3)
    scaling_factor = 1/np.sum(np.real(g))
    # magnitude = np.sqrt(real**2 + imag**2)
    # phase = np.arctan2(imag, real)
    # estimated_stripes = magnitude * np.cos(phase)
    # scaling_factor = estimate_scaling_factor(image, estimated_stripes)
    
    # 缩放条纹估计
    estimated_stripes = real * scaling_factor
    print("Scaling factor:", scaling_factor)

    
    # 从原图中减去估计的条纹
    result = image.astype(float) - estimated_stripes.astype(float)
    
    return result
def estimate_scaling_factor(original, estimated):
    """
    自适应估计缩放因子
    """
    # 计算局部方差比
    window_size = 15
    original_var = local_variance(original, window_size)
    estimated_var = local_variance(estimated, window_size)
    
    # 避免除零
    estimated_var = np.maximum(estimated_var, 1e-6)
    
    # 计算方差比
    var_ratio = original_var / estimated_var
    
    # 取中位数作为缩放因子
    scaling = np.median(var_ratio)
    import matplotlib.pyplot as plt
    plt.imshow(original_var, cmap='gray')
    plt.show()
    plt.imshow(estimated_var, cmap='gray')
    plt.show()
    
    return scaling

def local_variance(image, window_size):
    """计算局部方差"""
    from scipy.ndimage import uniform_filter
    
    mean = uniform_filter(image, window_size)
    mean_sq = uniform_filter(image**2, window_size)
    variance = mean_sq - mean**2
    
    return variance

def forward_model(image,angle,stripe_amplitude=0.5,stripe_width = 3,stripe_width_range = 3, stripe_num = 40,stripe_thred = 0.2, noise_level=0.01,n2nflag=False):
    # Simulate imaging artifacts including stripes and Gaussian noise.
    # Stripe artifact generation
    stripe_img = np.ones_like(image).astype(np.float32)
    for i in range (stripe_num):
        amplitude = np.random.random()*stripe_amplitude
        width = np.random.randint(stripe_width/stripe_width_range,stripe_width*stripe_width_range)
        position = np.random.randint(0,image.shape[0])
        stripe_img[(position-width//2)%image.shape[0]:(position+width//2)%image.shape[0],:] -= amplitude
    stripe_img = np.clip(stripe_img,stripe_thred,1)

    # Rotate the stripe image
    from scipy.ndimage import rotate
    stripe_img = rotate(stripe_img, angle, reshape=False, order=1, mode='nearest')

    # Apply stripe artifact to the original image
    stripe_img = image * stripe_img

    if n2nflag:
        # Add Gaussian noise
        noise1 = np.random.normal(0, noise_level, image.shape)
        noise2 = np.random.normal(0, noise_level, image.shape)
        stripe_img1 = stripe_img + noise1
        stripe_img2 = stripe_img + noise2
        return np.clip(stripe_img1,0,1),np.clip(stripe_img2,0,1)
    else:
        # Add Gaussian noise
        noise = np.random.normal(0, noise_level, image.shape)
        stripe_img += noise
 
        return np.clip(stripe_img,0,1)

    