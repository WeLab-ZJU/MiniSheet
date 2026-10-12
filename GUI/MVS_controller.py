from MVS_sdk.MvCameraControl_class import *
import threading
import queue
import cv2
import numpy as np
import time
g_bExit = False


def get_pixel_format(cam):
    """Get current pixel format enum value"""
    stEnumValue = MVCC_ENUMVALUE()
    memset(byref(stEnumValue), 0, sizeof(stEnumValue))
    ret = cam.MV_CC_GetEnumValue("PixelFormat", stEnumValue)
    if ret != 0:
        print(f"Failed to get pixel format, error code: {hex(ret)}")
        return None
    return stEnumValue.nCurValue


def set_pixel_format(cam, enum_value):
    """Set pixel format"""
    ret = cam.MV_CC_SetEnumValue("PixelFormat", enum_value)
    if ret != 0:
        print(f"Failed to set pixel format, error code: {hex(ret)}")
        return False
    return True

class MVS_controller:
    def __init__(self):
        self.is_connected = False
        self.acquisition_thread = None
    def init_camera(self):

        # Enumerate devices
        deviceList = MV_CC_DEVICE_INFO_LIST()
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
        if ret != 0 or deviceList.nDeviceNum == 0:
            print("Device not found")
            sys.exit()

        print(f"Found {deviceList.nDeviceNum} devices")
        for i in range(deviceList.nDeviceNum):
            device = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if device.nTLayerType == MV_GIGE_DEVICE:
                print(f"GigE device [{i}]:")
                model_name = ''.join([chr(c) for c in device.SpecialInfo.stGigEInfo.chModelName if c != 0])
                ip = '.'.join(str((device.SpecialInfo.stGigEInfo.nCurrentIp >> (24 - i * 8)) & 0xFF) for i in range(4))
                print(f"  Model: {model_name}, IP: {ip}")
            else:
                print(f"USB device [{i}]:")
                model_name = ''.join([chr(c) for c in device.SpecialInfo.stUsb3VInfo.chModelName if c != 0])
                print(f"  Model: {model_name}")


        cam_index = 0

        # Initialize camera
        self.cam = MvCamera()
        stDevice = cast(deviceList.pDeviceInfo[cam_index], POINTER(MV_CC_DEVICE_INFO)).contents
        ret = self.cam.MV_CC_CreateHandle(stDevice)
        if ret != 0:
            print(f"Failed to create handle: {hex(ret)}")
            sys.exit()

        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"Failed to open device: {hex(ret)}")
            self.is_connected = False
            sys.exit()
        else:
            self.is_connected = True

        # Set network packet size (GigE only)
        if stDevice.nTLayerType == MV_GIGE_DEVICE:
            packet_size = self.cam.MV_CC_GetOptimalPacketSize()
            if packet_size > 0:
                self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", packet_size)

        # Set trigger mode off
        self.cam.MV_CC_SetEnumValue("TriggerMode", 0)

        # Set target pixel format
        target_pixel_format = 0x01100005  # Modify as needed
        if set_pixel_format(self.cam, target_pixel_format):
            print(f"Pixel format set to: {hex(target_pixel_format)}")

        # Set parameters
        self.cam.MV_CC_SetEnumValue("ExposureTime", 10000)
        self.cam.MV_CC_SetEnumValue("Gain", 1)
        self.cam.MV_CC_SetEnumValue("BinningHorizontal", 2)
        self.cam.MV_CC_SetEnumValue("BinningVertical", 2)

        # Get PayloadSize and start grabbing
        self.stParam = MVCC_INTVALUE()
        ret = self.cam.MV_CC_GetIntValue("PayloadSize", self.stParam)
        if ret != 0:
            print(f"Failed to get PayloadSize: {hex(ret)}")
            sys.exit()

        self.data_buf = (c_ubyte * self.stParam.nCurValue)()

        self.cam.MV_CC_StartGrabbing()

        self._image_queue = queue.Queue(maxsize=10)  # Increase queue capacity
        self._stop_event = threading.Event()

        return True
    def stop_acquisition(self):


        if self.acquisition_thread:
            self.acquisition_thread.stop()
            self.acquisition_thread = None
        time.sleep(0.1)
        ret = self.cam.MV_CC_StopGrabbing()
        time.sleep(0.1)
        return ret
    def close_camera(self):
        self.stop_acquisition()
        if self.cam:
            self.cam.MV_CC_StopGrabbing()
            self.cam.MV_CC_CloseDevice()
            self.cam.MV_CC_DestroyHandle()
            self.cam = None
        self.is_connected = False


    def start_acquisition(self):
        """Start image acquisition"""
        if self.cam and not self.acquisition_thread:
            self.cam.MV_CC_StartGrabbing()
            self.acquisition_thread = ImageAcquisitionThread(self.cam, self.data_buf, self.stParam.nCurValue)
            self.acquisition_thread.start()
            return self.acquisition_thread.get_output_queue()
        return None
    def capture_frame(self):
        if self.acquisition_thread:
            try:
                return self.acquisition_thread.get_output_queue().get_nowait()
            except queue.Empty:
                return None

    def take_snapshot(self,path):
        import tifffile
        if self.acquisition_thread:
            try:
                frame = self.acquisition_thread.get_output_queue().get_nowait()
                filepath = os.path.join(path, 'snapshot%.4f.tif'%time.time())
                tifffile.imwrite(filepath, frame, imagej=True)
                print(f"Snapshot saved to {filepath}")
                return True
            except queue.Empty:
                return False
        return False

    def set_parameter(self, param_name, param_value):
        if self.cam:
            if param_name == "BinningHorizontal" \
                or param_name == "BinningVertical" \
                or param_name == "TriggerMode" \
                or param_name == "TriggerSource" \
                or param_name == "TriggerActivation" \
                or param_name == "TriggerSelector":

                # ret = self.stop_acquisition()
                # if ret != 0:
                #     print(f"Failed to stop acquisition, error code: {hex(ret)}")
                #     return

                ret = self.cam.MV_CC_SetEnumValue(param_name, param_value)
                if ret != 0:
                    print(f"Failed to set parameter {param_name}, error code: {hex(ret)}")
                    return
                time.sleep(0.1)
                pass

            elif isinstance(param_value, int):
                ret = self.cam.MV_CC_SetIntValue(param_name, param_value)
            elif isinstance(param_value, float):
                ret = self.cam.MV_CC_SetFloatValue(param_name, param_value)
            if ret != 0:
                print(f"Failed to set parameter {param_name}, error code: {hex(ret)}")
            else:
                print(f"Set parameter {param_name} success, value: {param_value}")

            if param_name == "BinningHorizontal" or param_name == "BinningVertical":
                # Get PayloadSize and start grabbing
                self.stParam = MVCC_INTVALUE()
                ret = self.cam.MV_CC_GetIntValue("PayloadSize", self.stParam)
                if ret != 0:
                    print(f"Failed to get PayloadSize: {hex(ret)}")
                    sys.exit()

                self.data_buf = (c_ubyte * self.stParam.nCurValue)()

                self.cam.MV_CC_StartGrabbing()
                if ret != 0:
                    print(f"Failed to start grabbing, error code: {hex(ret)}")
                    return
                time.sleep(0.1)
                pass


class ImageAcquisitionThread(threading.Thread):
    def __init__(self, cam, pData, nDataSize):
        super(ImageAcquisitionThread, self).__init__()
        self.cam = cam
        self._previous_timestamp = 0
        self.fps = 0
        self.pData = pData
        self.nDataSize = nDataSize
        self.last_frame_id = 0


        self._image_queue = queue.Queue(maxsize=500)  # Increase queue capacity
        self._stop_event = threading.Event()

        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()

        # Get pixel format
        pixel_format_code = get_pixel_format(cam)
        if pixel_format_code is None:
            print("Using default pixel format processing (assumed Mono8)")
            pixel_format_code = 0x01080001  # Default Mono8
        self.pixel_format_code = pixel_format_code

        # Pixel format mapping
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
        format_name = pixel_format_map.get(pixel_format_code, "Unknown format")
        print(f"Current pixel format: {format_name} (0x{pixel_format_code:x})")

    def get_output_queue(self):
        return self._image_queue

    def stop(self):
        self._stop_event.set()
        self.join(0.5)

    def _get_image(self):
        ret = self.cam.MV_CC_GetOneFrameTimeout(self.pData, self.nDataSize, self.stFrameInfo, 100)
        if ret != 0:
            #print(f"Failed to get frame, error code: {hex(ret)}")
            return None
        frame_id = self.stFrameInfo.nFrameNum
        if frame_id != self.last_frame_id+1:
            print(f"Frame number discontinuity: current {frame_id}, previous {self.last_frame_id}")
        self.last_frame_id = frame_id



        width = self.stFrameInfo.nWidth
        height = self.stFrameInfo.nHeight
        temp = np.asarray(self.pData)

        try:
            if self.pixel_format_code in [0x01100003, 0x01100005]:  # Mono10/Mono12
                # Convert to 16-bit array and adjust dynamic range
                temp = temp.view(np.uint16).reshape((height, width))
                #temp = ((temp >> (12 - 8)) & 0xFF).astype(np.uint16)
            else:
                print(f"Unsupported format: {hex(self.pixel_format_code)}")
            self._image_queue.put(temp.copy())
            # current_timestamp = time.time()
            # if current_timestamp - self._previous_timestamp != 0:
            #     self.fps = 1 / ((current_timestamp - self._previous_timestamp))
            # #print('%.4f'%(current_timestamp - self._previous_timestamp))
            # self._previous_timestamp = current_timestamp



        except Exception as e:
            print(f"Data processing error: {str(e)}")


    def run(self):

        while not self._stop_event.is_set():
            try:
                self._get_image()
            except queue.Full:
                # Skip frame when queue is full
                pass
            except Exception as error:
                print(f"Error encountered: {error}, image acquisition will stop")
                break
        print("Image acquisition stopped")