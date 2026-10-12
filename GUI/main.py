import sys
import numpy as np
import napari
import time
import tifffile as tf
import os
import threading
from queue import Queue
from PyQt5.QtCore import QTimer
from MVS_controller import MVS_controller
from camera_panel import CameraPanel
from esp32_panel import ESP32Panel
from scan_panel import ScanPanel
from log_panel import LogPanel

class CameraImagingApp:
    def __init__(self):
        self.viewer = None
        self.camera_controller = None
        self.timer = None
        self.scan_state = False
        self.frame_save_queue = Queue(maxsize=10)
        self.save_thread = None
        self.init_app()

    def init_app(self):
        # Create napari viewer
        self.viewer = napari.Viewer(title="Mini Sheet 3D Imaging System")

        # Init camera controller
        self.camera_controller = MVS_controller()

        # Init panels
        self.camera_panel = CameraPanel(self.camera_controller)
        self.esp32_panel = ESP32Panel()
        self.scan_panel = ScanPanel()
        self.log_panel = LogPanel()

        # Add panels to viewer
        self.viewer.window.add_dock_widget(self.camera_panel, name="Camera", area='left')
        self.viewer.window.add_dock_widget(self.esp32_panel, name="Stage", area='right')
        self.viewer.window.add_dock_widget(self.scan_panel, name="Scan", area='right')
        self.viewer.window.add_dock_widget(self.log_panel, name="Log", area='bottom')

        # Connect signals
        self.connect_signals()

        # Init system
        self.log_panel.add_log("System initialized")

    def connect_signals(self):
        # Camera panel
        self.camera_panel.start_preview.connect(self.start_preview)
        self.camera_panel.stop_preview.connect(self.stop_preview)
        self.camera_panel.camera_params_exposure.connect(self.update_camera_exposure)
        self.camera_panel.camera_params_gain.connect(self.update_camera_gain)
        self.camera_panel.camera_params_binning.connect(self.update_camera_binning)
        self.scan_panel.scan_started.connect(self.start_scan)
        self.scan_panel.normal_scan_started.connect(self.start_normal_scan)
        self.scan_panel.scan_stopped.connect(self.stop_scan)


    def start_preview(self):

        self.camera_controller.start_acquisition()


        # Init frame rate display
        self.frame_count = 0
        self.last_frame_time = time.time()

        # Create timer to update frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30fps

        # Create frame rate display update
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps_display)
        self.fps_timer.start(1000)  # Update every 1 second

        # Update preview button state
        self.camera_panel.set_preview_state(True)

        self.log_panel.add_log("Start preview")

    def stop_preview(self):
        """Stop preview"""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        print('stop preview')
        self.camera_controller.stop_acquisition()
        self.camera_panel.update_frame_rate(0)

        # Update preview button state
        self.camera_panel.set_preview_state(False)

        self.log_panel.add_log("Stop preview")

        # Stop fps timer
        if hasattr(self, 'fps_timer') and self.fps_timer.isActive():
            self.fps_timer.stop()


    def update_camera_exposure(self, params):
        """Update camera exposure"""
        self.camera_controller.set_parameter('ExposureTime',float(params))
        self.log_panel.add_log(f"Camera parameter updated: Exposure time: {params/1000}ms")
    def update_camera_gain(self, params):
        """Update camera gain"""
        self.camera_controller.set_parameter('Gain',float(params))
        self.log_panel.add_log(f"Camera parameter updated: Gain: {params}{params}")
    def update_camera_binning(self, params):
        """Update camera binning"""
        self.camera_controller.stop_acquisition()
        self.camera_controller.set_parameter('BinningHorizontal',int(params))
        self.camera_controller.stop_acquisition()
        self.camera_controller.set_parameter('BinningVertical',int(params))
        self.log_panel.add_log(f"Camera parameter updated: binning{params}")

    def start_scan(self, settings):

        """Start scan"""
        self.log_panel.add_log(f"Scan started: {settings}")
        path = settings['folder']
        distance = settings['distance']
        self.scan_state = True
        exposure = self.camera_panel.exposure_spin.value()
        print(exposure)
        self.esp32_panel.comm_thread.main2esp_queue.put("e"+str(exposure))
        time.sleep(1.5)
        self.esp32_panel.comm_thread.main2esp_queue.put("t"+str(distance))

        self.camera_controller.stop_acquisition()

        self.camera_controller.set_parameter('TriggerMode', 0)
        time.sleep(0.1)


        self.camera_controller.set_parameter('TriggerSource',2)
        self.camera_controller.set_parameter('TriggerActivation',2)

        self.camera_controller.set_parameter('TriggerMode',1)
        time.sleep(0.1)

        self.scan_thread = threading.Thread(target=self.scan_worker, args=(path,))
        self.scan_thread.start()
        if self.scan_state == False:
            self.scan_thread.join()

    def start_normal_scan(self, settings):

        """Start scan"""
        self.log_panel.add_log(f"Scan started: {settings}")
        path = settings['folder']
        distance = settings['distance']
        self.scan_state = True
        exposure = self.camera_panel.exposure_spin.value()
        print(exposure)
        self.esp32_panel.comm_thread.main2esp_queue.put("e"+str(exposure))
        time.sleep(1.5)
        self.esp32_panel.comm_thread.main2esp_queue.put("y"+str(distance))

        self.camera_controller.stop_acquisition()

        self.camera_controller.set_parameter('TriggerMode', 0)
        time.sleep(0.1)


        self.camera_controller.set_parameter('TriggerSource',2)
        self.camera_controller.set_parameter('TriggerActivation',2)

        self.camera_controller.set_parameter('TriggerMode',1)
        time.sleep(0.1)

        self.scan_thread = threading.Thread(target=self.scan_worker, args=(path,))
        self.scan_thread.start()
        if self.scan_state == False:
            self.scan_thread.join()

    def scan_worker(self, scan_path):
        frame_ord = 0
        self.camera_controller.start_acquisition()
        time0 = time.time()
        if os.path.exists('log.txt'):
            os.remove('log.txt')
        frame_batch = []
        batch_size = 300

        while True:
            if self.scan_state:
                frame = self.camera_controller.capture_frame()
                if frame is not None:
                    try:
                        frame_batch.append(frame.copy())
                        frame_ord += 1
                        if len(frame_batch) >= batch_size:
                            tf.imwrite(os.path.join(scan_path, f"frame_{frame_ord}.tif"), np.stack(frame_batch))
                            frame_batch = []

                            time1 = time.time()
                            self.log_panel.add_log(f"Saved frame: { f'frame_{frame_ord}.tif'}")
                            self.camera_panel.update_frame_rate(batch_size/(time1-time0))
                            time0 = time1
                    except:
                        pass



    def stop_scan(self):
        """Stop scan"""
        self.log_panel.add_log("Scan stopped")
        self.scan_state = False
        if hasattr(self, 'scan_thread') and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2.0)
        if hasattr(self, 'save_thread') and self.save_thread.is_alive():
            self.save_thread.join(timeout=2.0)

        self.camera_controller.stop_acquisition()
        self.camera_controller.set_parameter('TriggerMode',0)




    def on_camera_initialized(self, success, message):
        """Camera initialized callback"""
        if success:
            self.log_panel.add_log(message)
        else:
            self.log_panel.add_log(message, "error")

    def update_frame(self):
        """Update frame"""
        try:
            current_time = time.time()
            # if current_time - self.last_frame_time <0.1 and self.frame_count < 30:
            #     frame =  None
            # else:
            frame = self.camera_controller.capture_frame()
            if frame is not None:
                if len(self.viewer.layers) == 0:
                    self.viewer.add_image(frame, name="image")
                else:
                    self.viewer.layers['image'].data = frame
                self.frame_count += 1
                self.last_frame_time = current_time

        except Exception as e:
            self.log_panel.add_log(f"Failed to get frame: {e}", "error")

    def update_fps_display(self):
        """Update fps display"""
        self.camera_panel.update_frame_rate(self.camera_controller.acquisition_thread.fps)


def main():
    app = CameraImagingApp()
    napari.run()

if __name__ == "__main__":
    main()