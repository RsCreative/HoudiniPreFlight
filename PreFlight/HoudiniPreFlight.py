"""
Houdini Pre Render Check
Checks multiple setting and parameters in Houdini project file before sending file to farm
v001 Created 03/12/2021 (Raj Sandhu)
   - Initial code creation
v002 14/01/2022 (Raj Sandhu)
   - Added Font style and color
   - Added Resolution
v003 08/02/2022 (Raj Sandhu)
   - Added frame range
   - Added Pixel Ratios
   - Added AOV list check
   - Added DOF check
   - added method to find rops instead of copying and pasting code
v004 11/03/2022 (Raj Sandhu)
   - Added Motion Check
   - Added Crypto Chcck
   - Added Gi check
v005 15/03/2022 (Raj Sandhu)
   - Added Dome check
   - Added Rs Env check
   - Added Save check
v006 16/03/2022 (Raj Sandhu)
    - New UI
v007 04/04/2022 (Raj Sandhu)
    - New UI
v008 12/04/2022 (Raj Sandhu)
    - Updated UI to resize correctly
"""

import hou
from PySide2 import QtCore, QtGui, QtWidgets

# Global Variables
default_cam = ''
rop_list = []
rsLights = []
rsdomes = []


def getDefaultCam():
    global default_cam
    return default_cam


def setDefaultCam(cam):
    global default_cam
    default_cam = cam


def getRsLight():
    global rsLights, rsdomes
    domes = rsdomes
    lights = rsLights
    return lights, domes


def setRsLight():
    global rsLights, rsdomes
    lights = hou.objNodeTypeCategory().nodeType('rslight').instances()
    domes = hou.objNodeTypeCategory().nodeType('rslightdome::2.0').instances()
    rsLights = lights
    rsdomes = domes


def getRopList():
    global rop_list
    rops = rop_list
    return rops


def setRopList():
    global rop_list
    rop_list = hou.ropNodeTypeCategory().nodeType("Redshift_ROP").instances()


def getAOVList(rop):
    aov_list_length = rop.parm('RS_aov').eval()
    aovs = []
    for i in range(aov_list_length):
        aov = rop.parm('RS_aovSuffix_{i}'.format(i=i + 1)).eval()
        aovs.append(aov)
    return aovs


# Check Rop Cameras
def cameraInfo():
    rops = getRopList()
    cameras = []
    camera_count = {}
    output = ''
    error = []
    # Find ROP Cameras
    for rop in rops:
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
    for rop in rops:
        rop_cam = rop.parm("RS_renderCamera").eval()
        print("[CameraInfo]{rop} Camera set to {rop_cam}".format(rop=rop, rop_cam=rop_cam))
        if rop_cam != default_cam:
            error.append("{rop} is set to {cam}".format(rop=rop, cam=rop_cam))

    message = '{default_cam}'.format(output=output, default_cam=default_cam)

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


def pixelRatio():
    cam = hou.node(getDefaultCam())
    pixel = cam.parm('aspect').eval()
    print("[CamerInfo]Pixel Aspect Ratio {pixel}".format(pixel=pixel))
    return pixel


def dof():
    cam = hou.node(getDefaultCam())
    dof = cam.parm("RS_campro_dofEnable").eval()
    print("[CamerInfo]Camera DOF {dof}".format(dof=dof))
    if dof <= 0:
        message = 'DOF Disabled'
    if dof > 0:
        message = 'DOF Enabled'
    return message, dof


def frameRange():
    range = hou.playbar.playbackRange()
    f_frame = range[0]
    l_frame = range[1]
    rops = getRopList()
    warning = []
    frames = "{f} - {l}".format(f=f_frame, l=l_frame)
    for rop in rops:
        rop_fFrame = rop.parm("f1").eval()
        rop_lFrame = rop.parm("f2").eval()
        if rop_fFrame != f_frame or rop_lFrame != l_frame:
            warning.append(
                "{rop} set to {fFrame} - {lFrame}".format(rop=rop, fFrame=rop_fFrame, lFrame=rop_lFrame))

    return frames, warning


def aovs():
    rops = getRopList()
    warnings = []
    for rop in rops:
        aovListLength = rop.parm('RS_aov').eval()
        if aovListLength <= 0:
            warnings.append('{rop} missing AOVs'.format(rop=rop))
        else:
            continue
    return warnings


def zDepth():
    rops = getRopList()
    messages = []
    for rop in rops:
        z_depth = rop.parm("RS_aovDeepEnabled").eval()
        print("[ROP INFO]ROP ZDepth {z_depth}".format(z_depth=z_depth))
        if z_depth <= 0:
            message = '{rop} Z-Depth Disabled'.format(rop=rop)
            messages.append(message)
        else:
            continue
    return messages


def motionVector(rop):
    aov_list_length = rop.parm('RS_aov').eval()
    check = 0
    for i in range(aov_list_length):
        aov = rop.parm('RS_aovID_{i}'.format(i=i + 1)).eval()
        if aov == 2:
            check = 1
            break
        else:
            check = 0
    return check


def motionBlur(rop):
    moblur = rop.parm('MotionBlurEnabled').eval()
    if moblur == 1:
        check = 1
    else:
        check = 0
    return check


def motionCheck():
    rops = getRopList()
    messages = []
    for rop in rops:
        mo_Vector = motionVector(rop)
        mo_blur = motionBlur(rop)
        if mo_Vector >= 1 and mo_blur >= 1:
            message = "Motion Blur and Vector enabled"
        elif mo_blur >= 1:
            message = "Motion Blur Enabled"
        elif mo_Vector >= 1:
            message = "Motion Vector Enabled"
        messages.append("{rop} {m}".format(rop=rop, m=message))
    return messages


def gi():
    rops = getRopList()
    messages = []
    for rop in rops:
        rs_gi = rop.parm('RS_GIEnabled').eval()
        if rs_gi >= 1:
            message = str(rop) + " GI Enabled"
        if rs_gi < 1:
            message = str(rop) + ' GI Disabled'
        messages.append(message)
    return messages


def crypto():
    rops = getRopList()
    messages = []

    for rop in rops:
        aovlist = getAOVList(rop)
        if 'U_CRYMAT_matte' not in aovlist and 'U_CRYOBJ_matte' not in aovlist:
            message = 'Crypto Missing'
            messages.append('{rop} {m}'.format(rop=rop, m=message))

        elif 'U_CRYMAT_matte' not in aovlist:
            message = 'Crypto Matte Missing'
            messages.append('{rop} {m}'.format(rop=rop, m=message))

        elif 'U_CRYOBJ_matte' not in aovlist:
            message = 'Crypto OBJ Missing'
            messages.append('{rop} {m}'.format(rop=rop, m=message))

    return messages


def checklights():
    lights, domes = getRsLight()
    messages = []
    for dome in domes:
        domeblackdrop = dome.parm('background_enable').eval()
        domebackplate = dome.parm('backPlateEnabled').eval()
        if domeblackdrop >= 1:
            message = '{d} background is ON'.format(d=dome.name())
            messages.append(message)
        if domeblackdrop <= 0:
            message = '{d} background is OFF'.format(d=dome.name())
            messages.append(message)
        if domebackplate >= 1:
            message = '{d} backplate is ON'.format(d=dome.name())
            messages.append(message)
        if domebackplate <= 0:
            message = '{d} backplate is OFF'.format(d=dome.name())
            messages.append(message)

    return messages


def rsEnv():
    rops = getRopList()
    messages = []
    for rop in rops:
        rs_env = rop.parm('RS_globalEnvironment').eval()

        if rs_env != '':
            message = '{rop} has RS ENV Enabled'.format(rop=rop)
            messages.append(message)
        else:
            continue
    return messages


def saveStatus():
    hip_name = hou.hipFile.basename()
    save_check = hou.hipFile.hasUnsavedChanges()
    if save_check:
        message = 'File Not Saved'
    else:
        message = 'File Saved'

    name = hip_name
    message = message

    return name, message


# Form implementation generated from reading ui file 'preflight.ui'
#
# Created by: PyQt6 UI code generator 6.2.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide2 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("HoudiniPreflight")
        MainWindow.resize(736, 531)
        MainWindow.setWindowTitle("Houdini Preflight")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setMinimumSize(QtCore.QSize(0, 0))
        self.centralwidget.setMaximumSize(QtCore.QSize(16777215, 800))
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        # Title
        self.title = QtWidgets.QLabel(self.centralwidget)
        self.title.setStyleSheet("font-weight: bold;font-size: 1.5 em;")
        self.title.setObjectName("title")
        self.title.setText("Houdini Preflight")

        self.gridLayout.addWidget(self.title, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QtCore.QSize(350, 400))
        self.scrollArea.setStyleSheet("")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")

        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 333, 592))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.section_heading = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.section_heading.setStyleSheet("font-weight: bold;font-size: 1.5 em;")
        self.section_heading.setObjectName("section_heading")
        self.section_heading.setText("Camera Settings")
        self.verticalLayout.addWidget(self.section_heading)

        self.frame = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        # Camera Title
        self.render_cam = QtWidgets.QLabel(self.frame)
        self.render_cam.setStyleSheet("font-weight: bold;")
        self.render_cam.setObjectName("render_cam")
        self.render_cam.setText("Render Camera:")
        self.verticalLayout_3.addWidget(self.render_cam)

        # Camera Default
        defaultCam, camErrors = cameraInfo()
        self.render_cam_value = QtWidgets.QLabel(self.frame)
        self.render_cam_value.setObjectName("render_cam_value")
        self.render_cam_value.setText('      ' + defaultCam)
        self.verticalLayout_3.addWidget(self.render_cam_value)

        # Camera Mismatch
        for e in camErrors:
            self.render_cam_value_2 = QtWidgets.QLabel(self.frame)
            self.render_cam_value_2.setStyleSheet("color:orange;")
            self.render_cam_value_2.setObjectName("render_cam_value_2")
            self.render_cam_value_2.setText('      ' + e)
            self.verticalLayout_3.addWidget(self.render_cam_value_2)

        # Camera Resolution
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame_2.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        # Camera Res Title
        self.cam_res = QtWidgets.QLabel(self.frame_2)
        self.cam_res.setStyleSheet("font-weight: bold;")
        self.cam_res.setObjectName("cam_res")
        self.cam_res.setText("Camera Resolution:")
        self.verticalLayout_4.addWidget(self.cam_res)

        # Camera Res Value
        x, y = resolution()
        self.cam_rez_value = QtWidgets.QLabel(self.frame_2)
        self.cam_rez_value.setObjectName("cam_rez_value")
        self.cam_rez_value.setText('      {x} x {y}'.format(x=x, y=y))
        self.verticalLayout_4.addWidget(self.cam_rez_value)
        self.verticalLayout.addWidget(self.frame_2)

        # Pixel Ratio Section
        self.frame_32 = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame_32.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
        self.frame_32.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_32.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_32.setObjectName("frame_32")
        self.verticalLayout_52 = QtWidgets.QVBoxLayout(self.frame_32)
        self.verticalLayout_52.setObjectName("verticalLayout_52")

        # Pixel Ratio Title
        self.pixel_ratio = QtWidgets.QLabel(self.frame_32)
        self.pixel_ratio.setStyleSheet("font-weight: bold;")
        self.pixel_ratio.setObjectName("pixel_ratio")
        self.pixel_ratio.setText("Pixel Aspect Ratio:")
        self.verticalLayout_52.addWidget(self.pixel_ratio)

        # Pixel Ratio Values
        pixel = pixelRatio()
        self.pixel_ratio_value = QtWidgets.QLabel(self.frame_32)
        if float(pixel) > 2:
            self.pixel_ratio_value.setStyleSheet('color: red;')
        self.pixel_ratio_value.setObjectName("pixel_ratio_value")
        self.pixel_ratio_value.setText('      {pixel}'.format(pixel=pixel))
        self.verticalLayout_52.addWidget(self.pixel_ratio_value)
        self.verticalLayout.addWidget(self.frame_32)

        # Dof Section
        self.frame_3 = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame_3.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
        self.frame_3.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_5.setObjectName("verticalLayout_5")

        # Dof Title
        self.cam_dof = QtWidgets.QLabel(self.frame_3)
        self.cam_dof.setStyleSheet("font-weight: bold;")
        self.cam_dof.setObjectName("cam_dof")
        self.cam_dof.setText("Camera DOF:")
        self.verticalLayout_5.addWidget(self.cam_dof)

        # Dof Values
        cam_dof, dof_status = dof()
        self.cam_dof_value = QtWidgets.QLabel(self.frame_3)
        if float(pixel) > 2:
            self.cam_dof_value.setStyleSheet('color:orange;')
        self.cam_dof_value.setObjectName("cam_dof_value")
        self.cam_dof_value.setText('      {camdof}'.format(camdof=cam_dof))
        self.verticalLayout_5.addWidget(self.cam_dof_value)
        self.verticalLayout.addWidget(self.frame_3)

        # Frame Range Section
        self.frame_4 = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame_4.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
        self.frame_4.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_4.setObjectName("frame_4")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.frame_4)
        self.verticalLayout_6.setObjectName("verticalLayout_6")

        # Frame Range Title
        self.frame_range = QtWidgets.QLabel(self.frame_4)
        self.frame_range.setStyleSheet("font-weight: bold;")
        self.frame_range.setObjectName("frame_range")
        self.frame_range.setText('Frame Range:')
        self.verticalLayout_6.addWidget(self.frame_range)

        # Frame Range Value
        frames, frame_mismatch = frameRange()
        self.frame_range_value = QtWidgets.QLabel(self.frame_4)
        self.frame_range_value.setObjectName("frame_range_value")
        self.frame_range_value.setText('     ' + frames)
        self.verticalLayout_6.addWidget(self.frame_range_value)

        # Frame Range Mismatch
        if len(frame_mismatch) > 0:
            for errors in frame_mismatch:
                self.frame_range_value_2 = QtWidgets.QLabel(self.frame_4)
                self.frame_range_value_2.setStyleSheet("color:orange;")
                self.frame_range_value_2.setObjectName("frame_range_value_2")
                self.frame_range_value_2.setText('     ' + errors)
                self.verticalLayout_6.addWidget(self.frame_range_value_2)

        self.verticalLayout.addWidget(self.frame_4)

        # Lighting Section
        domelist = checklights()
        if len(domelist) > 0:
            self.section_heading_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            self.section_heading_2.setStyleSheet("font-weight: bold;font-size: 1.5 em;")
            self.section_heading_2.setObjectName("section_heading_2")
            self.section_heading_2.setText("Light Settings")
            self.verticalLayout.addWidget(self.section_heading_2)

            # Dome Section
            self.frame_5 = QtWidgets.QFrame(self.scrollAreaWidgetContents)
            self.frame_5.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_5.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_5.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_5.setObjectName("frame_5")
            self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.frame_5)

            # Dome Title
            self.verticalLayout_7.setObjectName("verticalLayout_7")
            self.dome = QtWidgets.QLabel(self.frame_5)
            self.dome.setStyleSheet("font-weight: bold;")
            self.dome.setObjectName("dome")
            self.dome.setText('Dome Status:')
            self.verticalLayout_7.addWidget(self.dome)

            for dome in domelist:
                # Dome ENV Status
                self.dome_env = QtWidgets.QLabel(self.frame_5)
                self.dome_env.setObjectName("dome_env")
                self.dome_env.setText('     ' + dome)
                self.verticalLayout_7.addWidget(self.dome_env)
            self.verticalLayout.addWidget(self.frame_5)

        # Right Side Scroll Area
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout.addWidget(self.scrollArea)
        self.scrollArea_2 = QtWidgets.QScrollArea(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_2.sizePolicy().hasHeightForWidth())
        self.scrollArea_2.setSizePolicy(sizePolicy)
        self.scrollArea_2.setMinimumSize(QtCore.QSize(350, 0))
        self.scrollArea_2.setStyleSheet("")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 348, 398))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents_2.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_2.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.section_heading_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.section_heading_3.setStyleSheet("font-weight: bold;font-size: 1.5 em;")
        self.section_heading_3.setObjectName("section_heading_3")
        self.section_heading_3.setText("AOV Settings")
        self.verticalLayout_2.addWidget(self.section_heading_3)

        # AOV Section
        aov_list = aovs()
        if len(aov_list) > 0:
            self.frame_9 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
            self.frame_9.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_9.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_9.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_9.setObjectName("frame_9")
            self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.frame_9)
            self.verticalLayout_8.setObjectName("verticalLayout_8")

            # AOV Status Title
            self.AOV_ROP = QtWidgets.QLabel(self.frame_9)
            self.AOV_ROP.setStyleSheet("font-weight: bold;")
            self.AOV_ROP.setObjectName("AOV_ROP")
            self.AOV_ROP.setText("AOV ROP Status:")
            self.verticalLayout_8.addWidget(self.AOV_ROP)

            # AOV Status Value
            for aov in aov_list:
                self.aov_rop_value = QtWidgets.QLabel(self.frame_9)
                self.aov_rop_value.setStyleSheet("color:red;")
                self.aov_rop_value.setObjectName("aov_rop_value")
                self.aov_rop_value.setText('     ' + aov)
                self.verticalLayout_8.addWidget(self.aov_rop_value)

            self.verticalLayout_2.addWidget(self.frame_9)

        # Crypto Section
        cryptomattes = crypto()
        if len(cryptomattes) > 0:
            self.frame_7 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
            self.frame_7.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_7.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_7.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_7.setObjectName("frame_7")
            self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.frame_7)
            self.verticalLayout_9.setObjectName("verticalLayout_9")

            # Crypto Title
            self.cry_aov = QtWidgets.QLabel(self.frame_7)
            self.cry_aov.setStyleSheet("font-weight: bold;")
            self.cry_aov.setObjectName("cry_aov")
            self.cry_aov.setText('Crypto AOV Status:')
            self.verticalLayout_9.addWidget(self.cry_aov)

            for mattes in cryptomattes:
                self.cry_aov_value = QtWidgets.QLabel(self.frame_7)
                self.cry_aov_value.setStyleSheet("color:orange;")
                self.cry_aov_value.setObjectName("cry_aov_value")
                self.cry_aov_value.setText('     ' + mattes)
                self.verticalLayout_9.addWidget(self.cry_aov_value)

            self.verticalLayout_2.addWidget(self.frame_7)

        # GI Section
        gi_rs = gi()
        if len(gi_rs) > 0:
            self.frame_8 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
            self.frame_8.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_8.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_8.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_8.setObjectName("frame_8")
            self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.frame_8)
            self.verticalLayout_10.setObjectName("verticalLayout_10")

            # Gi Title
            self.gi_aov = QtWidgets.QLabel(self.frame_8)
            self.gi_aov.setStyleSheet("font-weight: bold;")
            self.gi_aov.setObjectName("gi_aov")
            self.gi_aov.setText('GI Status:')
            self.verticalLayout_10.addWidget(self.gi_aov)

            # GI Values
            for g in gi_rs:
                self.gi_aov_value = QtWidgets.QLabel(self.frame_8)
                if "GI Disabled" in g:
                    self.gi_aov_value.setStyleSheet('Color: red;')
                self.gi_aov_value.setObjectName("gi_aov_value")
                self.gi_aov_value.setText('     ' + g)
                self.verticalLayout_10.addWidget(self.gi_aov_value)

            self.verticalLayout_2.addWidget(self.frame_8)

        # Motion Section
        motion = motionCheck()
        if len(motion) > 0:
            self.frame_6 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
            self.frame_6.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_6.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_6.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_6.setObjectName("frame_6")
            self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.frame_6)
            self.verticalLayout_11.setObjectName("verticalLayout_11")

            # Motion Title
            self.motion_aov = QtWidgets.QLabel(self.frame_6)
            self.motion_aov.setStyleSheet("font-weight: bold;")
            self.motion_aov.setObjectName("motion_aov")
            self.motion_aov.setText('Motion Status:')
            self.verticalLayout_11.addWidget(self.motion_aov)

            # Motion Values
            for m in motion:
                self.motion_aov_value = QtWidgets.QLabel(self.frame_6)
                if "Motion Blur and Vector enabled" in m:
                    self.motion_aov_value.setStyleSheet('Color: red;')
                self.motion_aov_value.setObjectName("motion_aov_value")
                self.motion_aov_value.setText('     ' + m)
                self.verticalLayout_11.addWidget(self.motion_aov_value)

            self.verticalLayout_2.addWidget(self.frame_6)

        # RS Env Section
        rs_env = rsEnv()
        if len(rs_env) > 0:
            self.frame_61 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
            self.frame_61.setStyleSheet("background-color:rgb(74, 75, 75);border-style:none;")
            self.frame_61.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            self.frame_61.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            self.frame_61.setObjectName("frame_6")
            self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.frame_61)
            self.verticalLayout_12.setObjectName("verticalLayout_11")

            # RS Env Title
            self.rsenv_aov = QtWidgets.QLabel(self.frame_61)
            self.rsenv_aov.setStyleSheet("font-weight: bold;")
            self.rsenv_aov.setObjectName("motion_aov")
            self.rsenv_aov.setText('RS ENV Status:')
            self.verticalLayout_12.addWidget(self.rsenv_aov)

            # RS Env Values
            for rs in rs_env:
                self.rsenv_aov_value = QtWidgets.QLabel(self.frame_61)
                self.rsenv_aov_value.setObjectName("motion_aov_value")
                self.rsenv_aov_value.setText('     ' + rs)
                self.verticalLayout_12.addWidget(self.rsenv_aov_value)

            self.verticalLayout_2.addWidget(self.frame_61)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.horizontalLayout.addWidget(self.scrollArea_2)

        # Top Header
        self.gridLayout.addLayout(self.horizontalLayout, 6, 0, 1, 4)

        # HIP info
        hip_name, status = saveStatus()
        # HIP TITLE
        self.file_name = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_name.sizePolicy().hasHeightForWidth())
        self.file_name.setSizePolicy(sizePolicy)
        self.file_name.setStyleSheet("font-weight: bold;")
        self.file_name.setObjectName("file_name")
        self.file_name.setText("File Name:")
        self.gridLayout.addWidget(self.file_name, 3, 0, 1, 1)

        # HIP Status Title
        self.file_status = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_status.sizePolicy().hasHeightForWidth())
        self.file_status.setSizePolicy(sizePolicy)
        self.file_status.setStyleSheet("font-weight: bold;")
        self.file_status.setObjectName("file_status")
        self.file_status.setText("File Status:")
        self.gridLayout.addWidget(self.file_status, 3, 1, 1, 1)

        # HIP Save Status
        self.file_save = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_save.sizePolicy().hasHeightForWidth())
        self.file_save.setSizePolicy(sizePolicy)
        if "File Not Saved" in status:
            self.file_save.setStyleSheet("color:red;")
        self.file_save.setObjectName("file_save")
        self.file_save.setText(status)
        self.gridLayout.addWidget(self.file_save, 4, 1, 1, 1)

        # HIP File Path
        self.file_path = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_path.sizePolicy().hasHeightForWidth())
        self.file_path.setSizePolicy(sizePolicy)
        self.file_path.setObjectName("file_path")
        self.file_path.setText(hip_name)

        self.gridLayout.addWidget(self.file_path, 4, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

try:
    setRopList()
    setRsLight()
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

except:
    hou.ui.displayMessage("Error: No Camera or Rops Found")
