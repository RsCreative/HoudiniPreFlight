# Houdini Pre Render Check
# Checks multiple setting and parameters in Houdini project file before sending file to farm
# v001 Created 03/12/2021 (Raj Sandhu)
#   - Initial code creation
# v002 14/01/2022 (Raj Sandhu)
#   - Added Font style and color
#   - Added Resolution
# v003 08/02/2022 (Raj Sandhu)
#   - Added frame range
#   - Added Pixel Ratios
#   - Added AOV list check
#   - Added DOF check
#   - added method to find rops instead of copying and pasting code
# v004 11/03/2022 (Raj Sandhu)
#   - Added Motion Check
#   - Added Crypto Chcck
#   - Added Gi check
# v005 11/03/2022 (Raj Sandhu)
#   - Added Dome check
#   - Added Rs Env check
#   - Added Save check


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
            error.append("Error: {rop} is set to {cam}".format(rop=rop, cam=rop_cam))

    message = 'Render Cam set to {default_cam}'.format(output=output, default_cam=default_cam)

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
                "Warning: {rop} set to {fFrame} - {lFrame}".format(rop=rop, fFrame=rop_fFrame, lFrame=rop_lFrame))

    return frames, warning


def aovs():
    rops = getRopList()
    warnings = []
    for rop in rops:
        aovListLength = rop.parm('RS_aov').eval()
        if aovListLength <= 0:
            warnings.append('Error: {rop} missing AOVs'.format(rop=rop))
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
            message = 'Warning: {rop} Z-Depth Disabled'.format(rop=rop)
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
        message = 'File not saved'
    else:
        message = 'File saved'

    messages = [hip_name, message]

    return messages


class HoudiniPreFlightUI(QtWidgets.QWidget):
    # Create Window
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setGeometry(500, 300, 250, 210)
        self.setWindowTitle('Houdini PreFlight')

        headerfont = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)

        mainUi = QtWidgets.QVBoxLayout()
        layout_rop_section = QtWidgets.QHBoxLayout()
        layout_rop_camlist = QtWidgets.QVBoxLayout()
        layout_rendercam = QtWidgets.QGridLayout()
        layout_Aov = QtWidgets.QGridLayout()

        label_title = QtWidgets.QLabel('Houdini PreFlight', self)
        label_title.setFont(headerfont)
        # label_title.setStyleSheet("color: black")
        mainUi.addWidget(label_title)

        Ui_spacer = QtWidgets.QLabel('', self)
        mainUi.addWidget(Ui_spacer)

        # ROP Camera Section
        label_camera_info = QtWidgets.QLabel('ROP Camera Info', self)
        label_camera_info.setFont(headerfont)
        mainUi.addWidget(label_camera_info)

        mainUi.addLayout(layout_rop_section)
        label_rop_caminfo = QtWidgets.QLabel('ROP Cameras:', self)
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

        # Render Camera Section
        label_defaultcam = QtWidgets.QLabel('Render Camera Settings', self)
        label_defaultcam.setFont(headerfont)
        mainUi.addWidget(label_defaultcam)
        mainUi.addLayout(layout_rendercam)

        # Resolution
        label_resolution = QtWidgets.QLabel('Resolution:', self)
        layout_rendercam.addWidget(label_resolution, 0, 0, 1, 1)
        x, y = resolution()
        label_res_values = QtWidgets.QLabel('{x} x {y}'.format(x=x, y=y))
        label_res_values.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout_rendercam.addWidget(label_res_values, 0, 1, 1, 1)

        # Pixel Ratio
        label_pixelRatio = QtWidgets.QLabel('Pixel Aspect Ratio:', self)
        layout_rendercam.addWidget(label_pixelRatio, 1, 0, 1, 1)
        pixel = pixelRatio()
        label_pxValues = QtWidgets.QLabel('{pixel}'.format(pixel=pixel))
        label_pxValues.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout_rendercam.addWidget(label_pxValues, 1, 1, 1, 1)

        # Depth of Field
        label_doftitle = QtWidgets.QLabel('Camera DOF:', self)
        layout_rendercam.addWidget(label_doftitle, 2, 0, 1, 1)
        camdof, dof_status = dof()
        if dof_status <= 0:
            label_dofValues = QtWidgets.QLabel('{camdof}'.format(camdof=camdof))
            label_dofValues.setStyleSheet("color: yellow")
        else:
            label_dofValues = QtWidgets.QLabel('{camdof}'.format(camdof=camdof))

        label_dofValues.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout_rendercam.addWidget(label_dofValues, 2, 1, 1, 1)

        # Frame Range
        label_frameheader = QtWidgets.QLabel('Frame Range:', self)
        layout_rendercam.addWidget(label_frameheader, 3, 0, 1, 1)

        frames, FrameMismatch = frameRange()

        label_framerange = QtWidgets.QLabel(frames, self)
        label_framerange.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout_rendercam.addWidget(label_framerange, 3, 1, 1, 1)
        x = 3
        for warning in FrameMismatch:
            x = x + 1
            label_framewarning = QtWidgets.QLabel(warning, self)
            label_framewarning.setStyleSheet("color: yellow")
            label_framewarning.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            layout_rendercam.addWidget(label_framewarning, x, 1, 1, 1)

        mainUi.addWidget(Ui_spacer)

        # AOV Section
        label_AovHeader = QtWidgets.QLabel('AOV Settings', self)
        label_AovHeader.setFont(headerfont)
        mainUi.addWidget(label_AovHeader)
        mainUi.addLayout(layout_Aov)

        aov_list = aovs()
        if len(aov_list) > 0:
            label_Aovtitle = QtWidgets.QLabel('AOV Status:')
            layout_Aov.addWidget(label_Aovtitle, 0, 0, 1, 1)
            y = -1
            for aov in aov_list:
                y = y + 1
                label_Aovtitle = QtWidgets.QLabel(aov)
                label_Aovtitle.setStyleSheet("color: red")
                label_Aovtitle.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_Aovtitle, y, 1, 1, 2)

        z_depth = zDepth()
        if len(z_depth) > 0:
            label_zdepth_title = QtWidgets.QLabel('Z-Depth Status:')
            layout_Aov.addWidget(label_zdepth_title, y + 1, 0, 1, 1)
            for z in z_depth:
                y = y + 1
                label_zdepth_value = QtWidgets.QLabel(z)
                label_zdepth_value.setStyleSheet("color: yellow")
                label_zdepth_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_zdepth_value, y, 1, 1, 2)

        motion = motionCheck()
        if len(motion) > 0:
            label_motion_title = QtWidgets.QLabel('Motion:')
            layout_Aov.addWidget(label_motion_title, y + 2, 0, 1, 1)
            for m in motion:
                y = y + 1
                label_motion_value = QtWidgets.QLabel(m)
                if "Motion Blur and Vector enabled" in m:
                    label_motion_value.setStyleSheet("color: red")
                    label_motion_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    layout_Aov.addWidget(label_motion_value, y + 1, 1, 1, 2)
                else:
                    label_motion_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    layout_Aov.addWidget(label_motion_value, y + 1, 1, 1, 2)

        gi_rs = gi()
        if len(gi_rs) > 0:
            label_gi_title = QtWidgets.QLabel('GI Status:')
            layout_Aov.addWidget(label_gi_title, y + 3, 0, 1, 1)
            for g in gi_rs:
                y = y + 1
                label_gi_value = QtWidgets.QLabel(g)
                label_gi_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_gi_value, y + 2, 1, 1, 2)

        cryptomatte = crypto()
        if len(cryptomatte) > 0:
            label_crypto_title = QtWidgets.QLabel('Crypto Status:')
            layout_Aov.addWidget(label_crypto_title, y + 4, 0, 1, 1)
            for c in cryptomatte:
                y = y + 1
                label_crypto_value = QtWidgets.QLabel(c)
                label_crypto_value.setStyleSheet("color: red")
                label_crypto_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_crypto_value, y + 3, 1, 1, 2)

        domelists = checklights()
        if len(domelists) > 0:
            label_dome_title = QtWidgets.QLabel('Domelight Status:')
            layout_Aov.addWidget(label_dome_title, y + 5, 0, 1, 1)
            for c in domelists:
                y = y + 1
                label_dome_value = QtWidgets.QLabel(c)
                label_dome_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_dome_value, y + 4, 1, 1, 2)

        hipinfo = saveStatus()
        if len(hipinfo) > 0:
            label_hip_title = QtWidgets.QLabel('HIP Status:')
            layout_Aov.addWidget(label_hip_title, y + 6, 0, 1, 1)
            for h in hipinfo:
                y = y + 1
                label_hip_value = QtWidgets.QLabel(h)
                if "File not saved" in h:
                    label_hip_value.setStyleSheet("color: red")
                    label_hip_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    layout_Aov.addWidget(label_hip_value, y + 5, 1, 1, 2)
                else:
                    label_hip_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    layout_Aov.addWidget(label_hip_value, y + 5, 1, 1, 2)

        rsenv = rsEnv()
        if len(rsenv) > 0:
            label_env_title = QtWidgets.QLabel('RS ENV Status:')
            layout_Aov.addWidget(label_env_title, y + 7, 0, 1, 1)
            for r in rsenv:
                y = y + 1
                label_env_value = QtWidgets.QLabel(r)
                label_env_value.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                layout_Aov.addWidget(label_env_value, y + 6, 1, 1, 2)

        mainUi.addWidget(Ui_spacer)
        # button = QtWidgets.QPushButton('Change Font', self)
        # button.setFocusPolicy(QtCore.Qt.NoFocus)
        # button.move(20, 20)
        #
        # mainUi.addWidget(button)

        # self.connect(button, QtCore.SIGNAL('clicked()'), self.showDialog)
        #
        # self.label = QtWidgets.QLabel('This is some sample text', self)
        # self.label.move(130, 20)
        #
        # mainUi.addWidget(self.label, 1)
        self.setLayout(mainUi)


setRopList()
setRsLight()
window = HoudiniPreFlightUI()
window.show()
