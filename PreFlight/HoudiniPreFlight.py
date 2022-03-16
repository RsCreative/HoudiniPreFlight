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
# v005 15/03/2022 (Raj Sandhu)
#   - Added Dome check
#   - Added Rs Env check
#   - Added Save check
# v006 16/03/2022 (Raj Sandhu)
#     - New UI

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

    messages = [hip_name, message]

    return messages


class HoudiniPreFlightUI(QtWidgets.QWidget):
    # Create Window
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setGeometry(500, 300, 600, 550)
        self.setWindowTitle('Houdini PreFlight')

        font_title = QtGui.QFont("Arial", 12, QtGui.QFont.Bold)
        font_header = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
        font_body = QtGui.QFont("Arial", 10)
        font_error = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)

        layout_window = QtWidgets.QVBoxLayout()
        layout_window.setAlignment(QtCore.Qt.AlignTop)
        Ui_spacer = QtWidgets.QLabel('', self)

        # Window Title
        text_title = QtWidgets.QLabel('Houdini PreFlight', self)
        text_title.setFont(font_title)
        layout_window.addWidget(text_title)
        layout_window.addWidget(Ui_spacer)

        # HIP Info
        layout_hip_main = QtWidgets.QHBoxLayout()
        layout_hip_main.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout_window.addLayout(layout_hip_main)

        text_hip_title = QtWidgets.QLabel('HIP File Status:', self)
        text_hip_title.setAlignment(QtCore.Qt.AlignTop)
        text_hip_title.setFont(font_header)
        layout_hip_main.addWidget(text_hip_title)

        layout_hip_list = QtWidgets.QVBoxLayout()
        layout_hip_main.addLayout(layout_hip_list)

        hip_info = saveStatus()
        if len(hip_info) > 0:
            for hip in hip_info:
                text_hip_list = QtWidgets.QLabel(hip)
                text_hip_list.setAlignment(QtCore.Qt.AlignTop)
                if "File Not Saved" in hip:
                    text_hip_list.setFont(font_error)
                    text_hip_list.setStyleSheet("color: red")
                else:
                    text_hip_list.setFont(font_body)
                layout_hip_list.addWidget(text_hip_list)

        layout_window.addWidget(Ui_spacer)
        # Main Layout
        layout_main = QtWidgets.QHBoxLayout()
        layout_window.addLayout(layout_main)

        # Column 1
        layout_col_1_main = QtWidgets.QVBoxLayout()
        layout_main.addLayout(layout_col_1_main)
        text_camera_title = QtWidgets.QLabel('Camera Settings', self)
        text_camera_title.setAlignment(QtCore.Qt.AlignTop)
        text_camera_title.setFont(font_title)
        layout_col_1_main.addWidget(text_camera_title)

        # Render Camera
        defaultCam, camErrors = cameraInfo()
        text_render_cam_title = QtWidgets.QLabel('Render Camera:', self)
        text_render_cam_title.setAlignment(QtCore.Qt.AlignTop)
        text_render_cam_title.setFont(font_header)
        layout_col_1_main.addWidget(text_render_cam_title)

        text_render_cam_list = QtWidgets.QLabel('      ' + defaultCam, self)
        text_render_cam_list.setAlignment(QtCore.Qt.AlignTop)
        text_render_cam_list.setFont(font_body)
        layout_col_1_main.addWidget(text_render_cam_list)

        # Render Mismatch

        if len(camErrors) > 0:
            for errors in camErrors:
                text_r_cam_list = QtWidgets.QLabel('      ' + errors)
                text_r_cam_list.setAlignment(QtCore.Qt.AlignTop)
                text_r_cam_list.setStyleSheet("color: red")
                text_r_cam_list.setFont(font_error)
                layout_col_1_main.addWidget(text_r_cam_list)
        layout_col_1_main.addWidget(Ui_spacer)

        # Camera Resolution
        text_resolution_title = QtWidgets.QLabel('Camera Resolution:', self)
        text_resolution_title.setAlignment(QtCore.Qt.AlignTop)
        text_resolution_title.setFont(font_header)
        layout_col_1_main.addWidget(text_resolution_title)

        x, y = resolution()
        text_resolution_list = QtWidgets.QLabel('      {x} x {y}'.format(x=x, y=y), self)
        text_resolution_list.setAlignment(QtCore.Qt.AlignTop)
        text_resolution_list.setFont(font_body)
        layout_col_1_main.addWidget(text_resolution_list)
        layout_col_1_main.addWidget(Ui_spacer)

        # Pixel Ratio

        text_pixel_title = QtWidgets.QLabel('Pixel Aspect Ratio:', self)
        text_pixel_title.setAlignment(QtCore.Qt.AlignTop)
        text_pixel_title.setFont(font_header)
        layout_col_1_main.addWidget(text_pixel_title)

        pixel = pixelRatio()
        text_pixel_list = QtWidgets.QLabel('      {pixel}'.format(pixel=pixel), self)
        text_pixel_list.setAlignment(QtCore.Qt.AlignTop)
        if float(pixel) > 2:
            text_pixel_list.setStyleSheet('color : red')
            text_pixel_list.setFont(font_error)
        else:
            text_pixel_list.setFont(font_body)
        layout_col_1_main.addWidget(text_pixel_list)
        layout_col_1_main.addWidget(Ui_spacer)

        # Depth of Field
        text_dof_title = QtWidgets.QLabel('Camera DOF:', self)
        text_dof_title.setAlignment(QtCore.Qt.AlignTop)
        text_dof_title.setFont(font_header)
        layout_col_1_main.addWidget(text_dof_title)

        cam_dof, dof_status = dof()
        text_dof_list = QtWidgets.QLabel('      {camdof}'.format(camdof=cam_dof), self)

        if dof_status <= 0:
            text_dof_list.setStyleSheet("color: yellow")

        text_dof_list.setAlignment(QtCore.Qt.AlignTop)
        text_dof_list.setFont(font_body)
        layout_col_1_main.addWidget(text_dof_list)

        layout_col_1_main.addWidget(Ui_spacer)

        # Frame Range
        text_frames_title = QtWidgets.QLabel('Frame Range:', self)
        text_frames_title.setAlignment(QtCore.Qt.AlignTop)
        text_frames_title.setFont(font_header)
        layout_col_1_main.addWidget(text_frames_title)

        frames, frame_mismatch = frameRange()

        text_prj_frames = QtWidgets.QLabel('     ' + frames, self)
        text_prj_frames.setAlignment(QtCore.Qt.AlignTop)
        text_prj_frames.setFont(font_body)
        layout_col_1_main.addWidget(text_prj_frames)

        # Frame Range Mismatch
        if len(frame_mismatch) > 0:
            for errors in frame_mismatch:
                text_frame_list = QtWidgets.QLabel('     ' + errors, self)
                text_frame_list.setAlignment(QtCore.Qt.AlignTop)
                text_frame_list.setFont(font_body)
                text_frame_list.setStyleSheet("color: yellow")
                layout_col_1_main.addWidget(text_frame_list)

        layout_col_1_main.addWidget(Ui_spacer)

        # Lights
        text_lights_title = QtWidgets.QLabel('Light Settings', self)
        text_lights_title.setAlignment(QtCore.Qt.AlignTop)
        text_lights_title.setFont(font_title)
        layout_col_1_main.addWidget(text_lights_title)

        # Dome Lights
        domelist = checklights()
        if len(domelist) > 0:
            text_dome_light_title = QtWidgets.QLabel('Dome Status:', self)
            text_dome_light_title.setAlignment(QtCore.Qt.AlignTop)
            text_dome_light_title.setFont(font_header)
            layout_col_1_main.addWidget(text_dome_light_title)

            for dome in domelist:
                text_dome_light_list = QtWidgets.QLabel('     ' + dome)
                text_dome_light_list.setAlignment(QtCore.Qt.AlignTop)
                text_dome_light_list.setFont(font_body)
                layout_col_1_main.addWidget(text_dome_light_list)

        # Column 2
        layout_col_2_main = QtWidgets.QVBoxLayout()
        layout_main.addLayout(layout_col_2_main)
        layout_col_2_main.addWidget(Ui_spacer)

        # Column 3
        layout_col_3_main = QtWidgets.QVBoxLayout()
        layout_main.addLayout(layout_col_3_main)

        # Aov Settings
        text_aov_header = QtWidgets.QLabel('AOV Settings', self)
        text_aov_header.setAlignment(QtCore.Qt.AlignTop)
        text_aov_header.setFont(font_title)
        layout_col_3_main.addWidget(text_aov_header)

        # AOV List
        aov_list = aovs()
        if len(aov_list) > 0:
            text_aov_title = QtWidgets.QLabel('AOV ROP Status:', self)
            text_aov_title.setAlignment(QtCore.Qt.AlignTop)
            text_aov_title.setFont(font_header)
            layout_col_3_main.addWidget(text_aov_title)

            for aov in aov_list:
                text_aov_list = QtWidgets.QLabel('     ' + aov)
                text_aov_list.setAlignment(QtCore.Qt.AlignTop)
                text_aov_list.setStyleSheet("color: red")
                text_aov_list.setFont(font_error)
                layout_col_3_main.addWidget(text_aov_list)
            layout_col_3_main.addWidget(Ui_spacer)

        # Crypto Check
        cryptomattes = crypto()
        if len(cryptomattes) > 0:
            text_crypto_title = QtWidgets.QLabel('Crypto AOV Status:', self)
            text_crypto_title.setAlignment(QtCore.Qt.AlignTop)
            text_crypto_title.setFont(font_header)
            layout_col_3_main.addWidget(text_crypto_title)

            for mattes in cryptomattes:
                text_crypto_list = QtWidgets.QLabel('     ' + mattes)
                text_crypto_list.setAlignment(QtCore.Qt.AlignTop)
                text_crypto_list.setFont(font_error)
                text_crypto_list.setStyleSheet("color: red")
                layout_col_3_main.addWidget(text_crypto_list)
            layout_col_3_main.addWidget(Ui_spacer)

        # GI Check
        gi_rs = gi()
        if len(gi_rs) > 0:
            text_gi_title = QtWidgets.QLabel('GI Status:', self)
            text_gi_title.setAlignment(QtCore.Qt.AlignTop)
            text_gi_title.setFont(font_header)
            layout_col_3_main.addWidget(text_gi_title)

            for g in gi_rs:
                text_gi_list = QtWidgets.QLabel('     ' + g)
                if "GI Disabled" in g:
                    text_gi_list.setStyleSheet('color : red')
                    text_gi_list.setFont(font_error)
                else:
                    text_gi_list.setFont(font_body)
                text_gi_list.setAlignment(QtCore.Qt.AlignTop)
                layout_col_3_main.addWidget(text_gi_list)
            layout_col_3_main.addWidget(Ui_spacer)

        # Z-Depth Check
        z_depth = zDepth()
        if len(z_depth) > 0:
            text_z_title = QtWidgets.QLabel('Z-Depth Status:', self)
            text_z_title.setAlignment(QtCore.Qt.AlignTop)
            text_z_title.setFont(font_header)
            layout_col_3_main.addWidget(text_z_title)

            for z in z_depth:
                text_z_list = QtWidgets.QLabel('     ' + z)
                text_z_list.setAlignment(QtCore.Qt.AlignTop)
                text_z_list.setStyleSheet('color : yellow')
                text_z_list.setFont(font_body)
                layout_col_3_main.addWidget(text_z_list)
            layout_col_3_main.addWidget(Ui_spacer)

        # Motion Check
        motion = motionCheck()
        if len(motion) > 0:
            text_motion_title = QtWidgets.QLabel('Motion Status:', self)
            text_motion_title.setAlignment(QtCore.Qt.AlignTop)
            text_motion_title.setFont(font_header)
            layout_col_3_main.addWidget(text_motion_title)

            for m in motion:
                text_motion_list = QtWidgets.QLabel('     ' + m)
                text_motion_list.setAlignment(QtCore.Qt.AlignTop)
                if "Motion Blur and Vector enabled" in m:
                    text_motion_list.setStyleSheet('color : red')
                    text_motion_list.setFont(font_error)
                else:
                    text_motion_list.setFont(font_body)
                layout_col_3_main.addWidget(text_motion_list)
            layout_col_3_main.addWidget(Ui_spacer)

        # RS ENV Check
        rs_env = rsEnv()
        if len(rs_env) > 0:
            text_env_title = QtWidgets.QLabel('RS ENV Status:', self)
            text_env_title.setAlignment(QtCore.Qt.AlignTop)
            text_env_title.setFont(font_header)
            layout_col_3_main.addWidget(text_env_title)

            for rs in rs_env:
                text_env_list = QtWidgets.QLabel('     ' + rs)
                text_env_list.setAlignment(QtCore.Qt.AlignTop)
                text_env_list.setFont(font_body)
                layout_col_3_main.addWidget(text_env_list)
            layout_col_3_main.addWidget(Ui_spacer)

        self.setLayout(layout_window)

try:
    setRopList()
    setRsLight()
    window = HoudiniPreFlightUI()
    window.show()
except:
    hou.ui.displayMessage("Error: No Camera or Rops Found")
