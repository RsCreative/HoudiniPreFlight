# Houdini Pre Render Check
# Checks multiple setting and parameters in Houdini project file before sending file to farm
# v001 Created 03/12/2021(Raj Sandhu)
#   - Initial code creation

import hou
from PySide2 import QtCore
from PySide2 import QtWidgets


class HoudiniPreFlightUI(QtWidgets.QWidget):
    # Create Window
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setGeometry(500, 300, 250, 110)
        self.setWindowTitle('Houdini PreFlight')

        mainUi = QtWidgets.QVBoxLayout()
        rop_section = QtWidgets.QHBoxLayout()
        rop_camlist = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel('Houdini PreFlight', self)
        camera_info = QtWidgets.QLabel('Camera Info', self)
        rop_caminfo = QtWidgets.QLabel('ROP Cameras', self)
        spacer = QtWidgets.QLabel('', self)

        mainUi.addWidget(title)
        mainUi.addWidget(spacer)
        mainUi.addWidget(camera_info)
        mainUi.addLayout(rop_section)
        rop_section.addWidget(rop_caminfo)
        rop_section.addLayout(rop_camlist)
        for message in cameraInfo():
            cam_listItem = QtWidgets.QLabel(message, self)
            rop_camlist.addWidget(cam_listItem)
        mainUi.addWidget(spacer)
        button = QtWidgets.QPushButton('Change Font', self)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.move(20, 20)

        mainUi.addWidget(button)

        self.connect(button, QtCore.SIGNAL('clicked()'), self.showDialog)

        self.label = QtWidgets.QLabel('This is some sample text', self)
        self.label.move(130, 20)

        mainUi.addWidget(self.label, 1)
        self.setLayout(mainUi)

    # Funtions for Preflight
    def showDialog(self):
        ok, font = QtWidgets.QFontDialog.getFont()
        if ok:
            self.label.setFont(font)


# Global Variables
default_cam = ''


def getDefaultCam():
    global default_cam
    return default_cam


def setDefaultCam(cam):
    global default_cam
    default_cam = cam


# Check Rop Cameras
def cameraInfo():
    rop_list = hou.ropNodeTypeCategory().nodeType("Redshift_ROP").instances()
    cameras = []
    camera_count = {}
    output = ''
    error = []
    # Find ROP Cameras
    for rop in rop_list:
        cameras.append(rop.parm("RS_renderCamera").eval())

    # Get Count cameras being used
    for camera in cameras:
        camera_count = {camera: cameras.count(camera)}

    # Get Default camera from count
    for c in camera_count.values():
        temp = 0
        if c > temp:
            temp = c
            cam = list(camera_count.keys())[list(camera_count.values()).index(c)]
            setDefaultCam(cam)

    # Check Rop Camera settings
    for rop in rop_list:
        # if rop.parm("RS_renderCamera").eval() == default_cam:
        #     output += "{rop}, ".format(output=output, rop=rop)
        if rop.parm("RS_renderCamera").eval() != default_cam:
            cam = rop.parm("RS_renderCamera").eval()
            error.append("Warning: {rop} is set to {cam}".format(rop=rop, cam=cam))

    message = 'Camera : Default set to {default_cam}'.format(output=output, default_cam=default_cam)

    info = [message]

    for txt in error:
        info.append(txt)

    print(info)

    return info


def resolution():
    print()


cameraInfo()

window = HoudiniPreFlightUI()
window.show()
