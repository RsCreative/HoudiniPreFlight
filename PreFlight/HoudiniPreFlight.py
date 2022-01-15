# Houdini Pre Render Check
# Checks multiple setting and parameters in Houdini project file before sending file to farm
# v001 Created 03/12/2021(Raj Sandhu)
#   - Initial code creation
# v002 Created 14/01/2022(Raj Sandhu)
#   - Added Font style and color
#   - Added Resolution


import hou
from PySide2 import QtCore, QtGui, QtWidgets


class HoudiniPreFlightUI(QtWidgets.QWidget):
    # Create Window
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setGeometry(500, 300, 250, 110)
        self.setWindowTitle('Houdini PreFlight')

        headerfont = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)

        mainUi = QtWidgets.QVBoxLayout()
        layout_rop_section = QtWidgets.QHBoxLayout()
        layout_rop_camlist = QtWidgets.QVBoxLayout()
        layout_resolution = QtWidgets.QHBoxLayout()

        label_title = QtWidgets.QLabel('Houdini PreFlight', self)
        label_title.setFont(headerfont)
        #label_title.setStyleSheet("color: black")
        mainUi.addWidget(label_title)

        Ui_spacer = QtWidgets.QLabel('', self)
        mainUi.addWidget(Ui_spacer)

        label_camera_info = QtWidgets.QLabel('Camera Info', self)
        label_camera_info.setFont(headerfont)
        mainUi.addWidget(label_camera_info)

        mainUi.addLayout(layout_rop_section)
        label_rop_caminfo = QtWidgets.QLabel('ROP Cameras', self)
        label_rop_caminfo.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout_rop_section.addWidget(label_rop_caminfo)
        layout_rop_section.addLayout(layout_rop_camlist)
        def_cam, errors = cameraInfo()
        label_rop_defaultCam = QtWidgets.QLabel(def_cam, self)
        layout_rop_camlist.addWidget(label_rop_defaultCam)
        for message in errors:
            cam_listItem = QtWidgets.QLabel(message, self)
            cam_listItem.setStyleSheet("color: red")
            layout_rop_camlist.addWidget(cam_listItem)

        mainUi.addWidget(Ui_spacer)

        mainUi.addLayout(layout_resolution)
        label_resolution = QtWidgets.QLabel('Resolution', self)
        layout_resolution.addWidget(label_resolution)
        x, y = resolution()
        label_res_values = QtWidgets.QLabel('{x} x {y}'.format(x=x, y=y))
        label_res_values.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout_resolution.addWidget(label_res_values)

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
        cam = rop.parm("RS_renderCamera").eval()
        cameras.append(cam)
        print("[CameraInfo]{cam} added to Cameras List".format(cam=cam))

    # Get Count cameras being used
    for camera in cameras:
        num = cameras.count(camera)
        camera_count.update({camera: num})

    print("[CameraInfo]" + str(camera_count))

    # Get Default camera from count
    temp = 0
    for c in camera_count.values():
        if c > temp:
            temp = c
            cam = list(camera_count.keys())[list(camera_count.values()).index(c)]
            setDefaultCam(cam)
    print("[CameraInfo]Default Cam set to {cam}".format(cam=getDefaultCam()))

    # Check Rop Camera settings
    for rop in rop_list:
        rop_cam = rop.parm("RS_renderCamera").eval()
        print("[CameraInfo]{rop} Camera set to {rop_cam}".format(rop=rop, rop_cam=rop_cam))
        if rop_cam != default_cam:
            error.append("Warning: {rop} is set to {cam}".format(rop=rop, cam=rop_cam))

    message = 'Camera : Default set to {default_cam}'.format(output=output, default_cam=default_cam)

    info = []

    for txt in error:
        info.append(txt)

    return message, info


def resolution():
    cam = hou.node(getDefaultCam())
    resx = cam.parm('resx').eval()
    resy = cam.parm('resy').eval()
    print("[CamerInfo]Resolution {x} x {y}".format(x=resx, y=resy))
    return resx, resy


window = HoudiniPreFlightUI()
window.show()
