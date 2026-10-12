import sys
import threading
import msvcrt
import numpy as np
import cv2
import matplotlib.pyplot as plt
from ctypes import *
 
#sys.path.append(R'D:\MVS\MVS\Development\Samples\Python\MvImport')
from MvCameraControl_class import *
 
g_bExit = False
 
 
def get_pixel_format(cam):
    """获取当前像素格式的枚举值"""
    stEnumValue = MVCC_ENUMVALUE()
    memset(byref(stEnumValue), 0, sizeof(stEnumValue))
    ret = cam.MV_CC_GetEnumValue("PixelFormat", stEnumValue)
    if ret != 0:
        print(f"获取像素格式失败，错误码: {hex(ret)}")
        return None
    return stEnumValue.nCurValue
 
 
def set_pixel_format(cam, enum_value):
    """设置像素格式"""
    ret = cam.MV_CC_SetEnumValue("PixelFormat", enum_value)
    if ret != 0:
        print(f"设置像素格式失败，错误码: {hex(ret)}")
        return False
    return True