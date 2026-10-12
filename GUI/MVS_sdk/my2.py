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
 
 
 
def work_thread3(cam, pData, nDataSize):
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    cv2.namedWindow("image", cv2.WINDOW_NORMAL)
 
    # 获取像素格式
    pixel_format_code = get_pixel_format(cam)
    if pixel_format_code is None:
        print("使用默认像素格式处理（假设为 Mono8）")
        pixel_format_code = 0x01080001  # 默认 Mono8
 
    # 像素格式映射表
    pixel_format_map = {
        0x01080001: "Mono8",
        0x01100003: "Mono10",
        0x01100005: "Mono12",
        0x02180014: "RGB8",
        0x02180015: "BGR8",
        0x02100032: "YUV422_YUYV",
        0x0210001F: "YUV422Packed",
        0x01080009: "BayerRG8",
    }
    format_name = pixel_format_map.get(pixel_format_code, "未知格式")
    print(f"当前像素格式: {format_name} (0x{pixel_format_code:x})")
 
    while not g_bExit:
        ret = cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
        if ret != 0:
            print(f"获取帧失败，错误码: {hex(ret)}")
            continue
 
        width = stFrameInfo.nWidth
        height = stFrameInfo.nHeight
        temp = np.asarray(pData)
 
        try:
            # 根据格式处理数据
            if pixel_format_code == 0x01080001:  # Mono8
                temp = temp.reshape((height, width))  # 单通道灰度图
 
            elif pixel_format_code in [0x01100003, 0x01100005]:  # Mono10/Mono12
                # 转换为 16 位数组并调整动态范围
                temp = temp.view(np.uint16).reshape((height, width))
                temp = ((temp >> (12 - 8)) & 0xFF).astype(np.uint8)
            elif pixel_format_code == 0x01080009:  # BayerRG8
                temp = temp.reshape((height, width))
                temp = cv2.cvtColor(temp, cv2.COLOR_BAYER_RG2RGB)
 
            elif pixel_format_code == 0x02100032:  # YUV422_YUYV
                temp = temp.reshape((height, width, 2))
                temp = cv2.cvtColor(temp, cv2.COLOR_YUV2BGR_YUYV)
 
            # 新增 YUV422Packed 处理逻辑
            elif pixel_format_code == 0x0210001F:  # YUV422Packed
                temp = temp.reshape((height, width, 2))  # YUV422 数据
                temp = cv2.cvtColor(temp, cv2.COLOR_YUV2BGR_Y422)  # 转换为 BGR
 
            elif pixel_format_code in [0x02180014, 0x02180015]:  # RGB8/BGR8
                temp = temp.reshape((height, width, 3))
                if pixel_format_code == 0x02180015:  # BGR8 转 RGB
                    temp = cv2.cvtColor(temp, cv2.COLOR_BGR2RGB)
 
            else:
                print(f"不支持的格式: {hex(pixel_format_code)}")
                continue
 
            # 显示图像
            cv2.imshow("image", temp)
 
        except Exception as e:
            print(f"数据处理错误: {str(e)}")
 
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
 
    cv2.destroyAllWindows()
 
 
if __name__ == "__main__":
    # 枚举设备
    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        print("未找到设备")
        sys.exit()
 
    print(f"找到 {deviceList.nDeviceNum} 个设备")
    for i in range(deviceList.nDeviceNum):
        device = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if device.nTLayerType == MV_GIGE_DEVICE:
            print(f"GigE 设备 [{i}]:")
            model_name = ''.join([chr(c) for c in device.SpecialInfo.stGigEInfo.chModelName if c != 0])
            ip = '.'.join(str((device.SpecialInfo.stGigEInfo.nCurrentIp >> (24 - i * 8)) & 0xFF) for i in range(4))
            print(f"  型号: {model_name}, IP: {ip}")
        else:
            print(f"USB 设备 [{i}]:")
            model_name = ''.join([chr(c) for c in device.SpecialInfo.stUsb3VInfo.chModelName if c != 0])
            print(f"  型号: {model_name}")
 
    # 选择设备
    # cam_index = int(input("请选择相机索引: "))
    # if cam_index >= deviceList.nDeviceNum:
    #     print("输入错误")
    #     sys.exit()
    cam_index = 0
 
    # 初始化相机
    cam = MvCamera()
    stDevice = cast(deviceList.pDeviceInfo[cam_index], POINTER(MV_CC_DEVICE_INFO)).contents
    ret = cam.MV_CC_CreateHandle(stDevice)
    if ret != 0:
        print(f"创建句柄失败: {hex(ret)}")
        sys.exit()
 
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print(f"打开设备失败: {hex(ret)}")
        sys.exit()
 
    # 设置网络包大小（仅GigE相机）
    if stDevice.nTLayerType == MV_GIGE_DEVICE:
        packet_size = cam.MV_CC_GetOptimalPacketSize()
        if packet_size > 0:
            cam.MV_CC_SetIntValue("GevSCPSPacketSize", packet_size)
 
    # 设置触发模式为关闭
    cam.MV_CC_SetEnumValue("TriggerMode", 0)
 
    # 设置目标像素格式
    target_pixel_format = 0x0210001F  # 修改为所需格式
    if set_pixel_format(cam, target_pixel_format):
        print(f"像素格式设置为: {hex(target_pixel_format)}")
 
    # 获取PayloadSize并开始取流
    stParam = MVCC_INTVALUE()
    ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
    if ret != 0:
        print(f"获取PayloadSize失败: {hex(ret)}")
        sys.exit()
 
    data_buf = (c_ubyte * stParam.nCurValue)()
    cam.MV_CC_StartGrabbing()
 
    # 启动线程
    try:
        print(data_buf)
        print(stParam.nCurValue)
        thread = threading.Thread(target=work_thread3, args=(cam, data_buf, stParam.nCurValue))
        thread.start()
    except Exception as e:
        print(f"线程启动失败: {str(e)}")
        sys.exit()
 
    print("按 q 退出...")
    msvcrt.getch()
    g_bExit = True
    thread.join()
 
    # 释放资源
    cam.MV_CC_StopGrabbing()
    cam.MV_CC_CloseDevice()
    cam.MV_CC_DestroyHandle()