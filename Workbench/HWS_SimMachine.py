# -*- coding: utf-8 -*-
# HWS (Hot Wire Slicer) workbench for FreeCAD 
# (c) 2024 Peter Christensen

# HWS is based on Javier Martínez García NiCr (Hot Wire CNC Cutter) workbench for FreeCAD
# https://github.com/JMG1/NiCr

#***************************************************************************
#*   (c)  Peter Christensen 2024                                           *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

import FreeCAD
import Part
import json

default_table_cfg = [] #["Default", 500.0, 400.0, 400.0, 10.0, 50.0, 2.0, 200.0, 20.0, 200.0, 0.0]
default_foam_cfg = [] #["Default", 1.6, 4, 1.9, 75]

class HWS_Machine:
    
    #default_foam_cfg = ["Default", 1.6, 4, 1.9, 2]
    #foam_cfg = []
    #default_table_cfg = ["Default", 500, 400, 400, 10, 50, 2, 200, 20, 200, 0]
    #table_cfg = []

    def __init__( self, obj ):

        default_foam_cfg = ["Default", 1.6, 4.0, 1.9, 75]
        foam_cfg = []
        foam_cfg.append(json.JSONEncoder().encode(default_foam_cfg))
        default_table_cfg = ["Default", 500.0, 400.0, 400.0, 10.0, 50.0, 2.0, 200.0, 20.0, 200.0, 0.0, 5.0]
        table_cfg = []
        table_cfg.append(json.JSONEncoder().encode(default_table_cfg))
        default_cut_cfg = json.JSONEncoder().encode([300, 100, 100, 10])
        
        obj.addProperty( 'App::PropertyString',
                         'PathToHWS_cfg',
                         'Paths' ).PathToHWS_cfg = ''
                         
        obj.addProperty( 'App::PropertyString',
                         'SaveFilePath',
                         'Paths' ).SaveFilePath = ''

        obj.addProperty( 'App::PropertyInteger',
                         'TableIndex',
                         'Table and Foam Settings' ).TableIndex = 0
        
        obj.addProperty( 'App::PropertyStringList',
                         'FoamConfig',
                         'Table and Foam Settings' ).FoamConfig = foam_cfg
        
        obj.addProperty( 'App::PropertyStringList',
                         'TableConfig',
                         'Table and Foam Settings' ).TableConfig = table_cfg
        
        obj.addProperty( 'App::PropertyStringList',
                         'CutConfig',
                         'Cut Settings' ).CutConfig = default_cut_cfg
        
        obj.addProperty( 'App::PropertyBool',
                         'G93',
                         'Table and Foam Settings' ).G93 = True
       

        # geometric properties
        obj.addProperty( 'App::PropertyFloat',
                         'XLength',
                         'Machine Geometry' ).XLength = float(default_table_cfg[2])

        obj.addProperty( 'App::PropertyFloat',
                         'YLength',
                         'Machine Geometry' ).YLength = float(default_table_cfg[3])

        obj.addProperty( 'App::PropertyFloat',
                         'ZLength',
                         'Machine Geometry' ).ZLength = float(default_table_cfg[1])

        obj.addProperty('App::PropertyFloat',
                        'FrameDiameter',
                        'Machine Geometry').FrameDiameter = 30.0

        obj.addProperty('App::PropertyVector',
                        'VirtualMachineZero',
                        'Machine Geometry').VirtualMachineZero = FreeCAD.Vector(0, 0, 0)
        
        obj.addProperty('App::PropertyBool',
                        'ClearTrajectory',
                        'Animation').ClearTrajectory = False

        obj.addProperty('App::PropertyBool',
                        'ReturnHome',
                        'Animation').ReturnHome = False

        obj.addProperty('App::PropertyBool',
                        'HideWireTrajectory',
                        'Animation').HideWireTrajectory = False

        obj.addProperty('App::PropertyBool',
                        'HideWire',
                        'Animation').HideWire = False

        obj.addProperty('App::PropertyFloat',
                        'AnimationDelay',
                        'Animation',
                        'Time between animation frames (0.0 = max speed)').AnimationDelay = 0.01
        
            #foam_type -> index, name, PWM_controlled_heat, high_cutting_speed[speed, heat], low_cutting_speed[speed, heat], kerf_root, kerf_tip
            #foam_cfg = []

        obj.Proxy = self
        self.addMachineToDocument( obj.FrameDiameter, obj.XLength, obj.YLength, obj.ZLength, created=False )


    def onChanged(self, fp, prop):
        try:
            if prop == 'XLength' or prop == 'YLength' or prop == 'ZLength' or prop == 'FrameDiameter':
                self.addMachineToDocument( fp.FrameDiameter, fp.XLength, fp.YLength, fp.ZLength )

            if prop == 'ReturnHome' and fp.ReturnHome:
                # reset machine position
                returnHome()

            if prop == 'ClearTrajectory' and fp.ClearTrajectory:
                # clear machine trajectory
                clearWireTrack()

            if prop == 'HideWireTrajectory':
                for obj in FreeCAD.ActiveDocument.WireTrajectory.Group:
                    obj.ViewObject.Visibility = not fp.HideWireTrajectory

            if prop == 'HideWire':
                FreeCAD.ActiveDocument.Wire.ViewObject.Visibility = not fp.HideWire

        except AttributeError:
            pass


    def execute( self, fp ):
        pass

    def buildMachine( self, tube_diameter, w_x, w_y, w_z ):
        main_cube = Part.makeBox( w_x + 2*tube_diameter,
                                  w_y + 2*tube_diameter,
                                  w_z + 2*tube_diameter,
                                  FreeCAD.Vector(-1.6*tube_diameter,
                                                 -1.8*tube_diameter,
                                                 -1.1*tube_diameter))

        xy_cutcube = Part.makeBox( w_x,
                                   w_y,
                                   w_z*1.5,
                                   FreeCAD.Vector(-0.6*tube_diameter,
                                                  -0.8*tube_diameter,
                                                  -2.1*tube_diameter))
        
        xz_cutcube = Part.makeBox( w_x,
                                   w_y*1.5,
                                   w_z,
                                   FreeCAD.Vector( -0.6*tube_diameter,
                                                   -2.8*tube_diameter,
                                                   -0.1*tube_diameter))

        yz_cutcube = Part.makeBox( w_x*1.5,
                                   w_y,
                                   w_z,
                                   FreeCAD.Vector( -2.6*tube_diameter,
                                                   -0.8*tube_diameter,
                                                   -0.1*tube_diameter ) )

        frame = main_cube.cut( xy_cutcube )
        frame = frame.cut( xz_cutcube )
        frame = frame.cut( yz_cutcube )
        # machine x axis frame
        xa_frame = Part.makeBox( tube_diameter,
                                 w_y,
                                 tube_diameter,
                                 FreeCAD.Vector( -0.5*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 -1.1*tube_diameter))

        xb_frame = Part.makeBox( tube_diameter,
                                 w_y,
                                 tube_diameter,
                                 FreeCAD.Vector( -0.5*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 w_z + -0.1*tube_diameter))

        # machine y axis frame
        ya_frame = Part.makeBox( tube_diameter*1.2,
                                 tube_diameter*1.6,
                                 tube_diameter*1.2,
                                 FreeCAD.Vector( -0.6*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 -1.2*tube_diameter))

        yb_frame = Part.makeBox( tube_diameter*1.2,
                                 tube_diameter*1.6,
                                 tube_diameter*1.2,
                                 FreeCAD.Vector( -0.6*tube_diameter,
                                                 -0.8*tube_diameter,
                                                 w_z - tube_diameter*0.2 ) )
        #dbm('2.3')
        return frame, xa_frame, xb_frame, ya_frame, yb_frame

    def addMachineToDocument(self, FrameDiameter, XLength, YLength, ZLength, created=True):
        # temporal workarround until:http://forum.freecadweb.org/viewtopic.php?f=22&t=13337
        #dbm( '0' )
        mfolder = FreeCAD.ActiveDocument.getObject('HWS_Machine')
        #dbm( '1' )
        # Remove previous machine parts
        if created:
            FreeCAD.ActiveDocument.removeObject('Frame')
            FreeCAD.ActiveDocument.removeObject('XA')
            FreeCAD.ActiveDocument.removeObject('XB')
            FreeCAD.ActiveDocument.removeObject('YA')
            FreeCAD.ActiveDocument.removeObject('YB')
            FreeCAD.ActiveDocument.removeObject('Base')

        # machine shapes
        machine_shapes = self.buildMachine(FrameDiameter,
                                           XLength,
                                           YLength,
                                           ZLength)
        # temporal workaround
        #mfolder = FreeCAD.ActiveDocument.addObject( 'App::DocumentObjectGroup','HWS_Machine' )
        obj_frame = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Frame')
        obj_XA = FreeCAD.ActiveDocument.addObject('Part::Feature', 'XA')
        obj_XB = FreeCAD.ActiveDocument.addObject('Part::Feature', 'XB')
        obj_YA = FreeCAD.ActiveDocument.addObject('Part::Feature', 'YA')
        obj_YB = FreeCAD.ActiveDocument.addObject('Part::Feature', 'YB')
        obj_frame.Shape = machine_shapes[0]
        obj_XA.Shape = machine_shapes[1]
        obj_XB.Shape = machine_shapes[2]
        obj_YA.Shape = machine_shapes[3]
        obj_YB.Shape = machine_shapes[4]
        obj_frame.ViewObject.ShapeColor = (0.67, 0.78, 0.85)
        obj_XA.ViewObject.ShapeColor = (0.00, 0.67, 1.00)
        obj_XB.ViewObject.ShapeColor = (0.00, 0.67, 1.00)
        obj_YA.ViewObject.ShapeColor = (0.00, 1.00, 0.00)
        obj_YB.ViewObject.ShapeColor = (0.00, 1.00, 0.00)
        obj_frame.ViewObject.Selectable = False
        obj_XA.ViewObject.Selectable = False
        obj_XB.ViewObject.Selectable = False
        obj_YA.ViewObject.Selectable = False
        obj_YB.ViewObject.Selectable = False
        mfolder.addObject(obj_frame)
        mfolder.addObject(obj_XA)
        mfolder.addObject(obj_XB)
        mfolder.addObject(obj_YA)
        mfolder.addObject(obj_YB)

        #add base
        obj_base = FreeCAD.ActiveDocument.addObject("Part::Box", "Base")
        obj_base.Length = 200
        obj_base.Width = 20
        obj_base.Height = 200
        machine_center_z = ZLength / 2
        base_center_z =  obj_base.Height / 2
        new_base_z = float(machine_center_z) - float(base_center_z)
        obj_base.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, new_base_z), FreeCAD.Rotation(0, 0, 0))
        obj_base.ViewObject.Selectable = False
        mfolder.addObject(obj_base)




class HWS_MachineViewProvider:
    def __init__(self, obj):
        obj.Proxy = self

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/CreateMachine.svg'

def dbm(ms):
    # debug messages
    FreeCAD.Console.PrintMessage( '\n' + ms + '\n' )


# Machine animation ----------------------------------------------------------
def runSimulation(complete_raw_path):
    # FreeCAD.ActiveDocument.WirePath.ViewObject.Visibility = False
    projected_trajectory_A = []
    projected_trajectory_B = []
    Z0 = FreeCAD.ActiveDocument.HWS_Machine.FrameDiameter*1.1*0
    #print("Z0:",Z0)
    ZL = FreeCAD.ActiveDocument.HWS_Machine.ZLength
    Z1 = ZL + Z0 - FreeCAD.ActiveDocument.HWS_Machine.FrameDiameter*0.2
    #print("Z1:",Z1)
    for i in range(len(complete_raw_path[0])):
        PA = complete_raw_path[0][i]
        PB = complete_raw_path[1][i]
        proj_A, proj_B = projectEdgeToTrajectory(PA, PB, Z0, Z1)
        projected_trajectory_A.append(proj_A)
        projected_trajectory_B.append(proj_B)

    machine_path = (projected_trajectory_A, projected_trajectory_B)

    # simulate machine path
    import time
    # create wire
    try:
        wire = FreeCAD.ActiveDocument.Wire
    except:
        wire = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Wire')



    try:
        # remove previous trajectories
        for obj in FreeCAD.ActiveDocument.WireTrajectory.Group:
            FreeCAD.ActiveDocument.removeObject(obj.Name)

        FreeCAD.ActiveDocument.removeObject('WireTrajectory')

    except:
        pass

    wire_tr_folder = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroup', 'WireTrajectory')
    FreeCAD.ActiveDocument.HWS_Machine.addObject(wire_tr_folder)
    
    # retrieve machine shapes
    XA = FreeCAD.ActiveDocument.XA
    XB = FreeCAD.ActiveDocument.XB
    YA = FreeCAD.ActiveDocument.YA
    YB = FreeCAD.ActiveDocument.YB
    # ofsets
    xoff = FreeCAD.ActiveDocument.HWS_Machine.FrameDiameter*1.5*0
    yoff = FreeCAD.ActiveDocument.HWS_Machine.FrameDiameter*1.8*0
    wire_t_list = []
    animation_delay = FreeCAD.ActiveDocument.HWS_Machine.AnimationDelay
    #wire_trajectory = FreeCAD.ActiveDocument.addObject('Part::Feature','wire_tr')
    #wire_tr_folder.addObject(wire_trajectory)
    # n iterator (for wire color)
    n = 0
    # visualization color
    vcolor = FreeCAD.ActiveDocument.WirePath.TrajectoryColor
    # determine the first value for the wire color
    if vcolor == 'Speed':
        mxspeed = FreeCAD.ActiveDocument.WirePath.MaxCutSpeed
        cpspeed = 4 #complete_raw_path[2][n][1]
        wire_color = WireColor(cpspeed, mxspeed, 'Speed')

    if vcolor == 'Temperature':
        mxtemp = FreeCAD.ActiveDocument.WirePath.MaxWireTemp
        cptemp = 4 #complete_raw_path[2][n][1]
        wire_color = WireColor(cptemp, mxtemp, 'Temperature')

    # animation loop
    for i in range(0, len(machine_path[0])):
        pa = machine_path[0][i]
        pb = machine_path[1][i]
        # draw wire
        w = Part.makeLine(pa, pb)
        wire.Shape = w
        wire.ViewObject.LineColor = wire_color
        
        #TODO make wire end points red when negative
        #print(pa,pb)
        
        if i < complete_raw_path[2][n][0]:
            # draw wire trajectory
            wire_t_list.append(w)
            wire_trajectory.Shape = Part.makeCompound(wire_t_list)
            wire_trajectory.ViewObject.LineColor = wire_color

        else:
            # create new wire trajectory object
            wire_trajectory = FreeCAD.ActiveDocument.addObject('Part::Feature', 'wire_tr')
            wire_tr_folder.addObject(wire_trajectory)
            # reset compound list
            wire_t_list = []
            wire_t_list.append(w)
            wire_trajectory.Shape = Part.makeCompound(wire_t_list)
            # establish wire color
            #print(n)
            if vcolor == 'Speed':
                mxspeed = FreeCAD.ActiveDocument.WirePath.MaxCutSpeed
                #print(n,len(complete_raw_path[2][n]))
                #print(complete_raw_path[2][n][1])
                cpspeed = 4 #complete_raw_path[2][n][1]
                wire_color = WireColor(cpspeed, mxspeed, 'Speed')

            if vcolor == 'Temperature':
                mxtemp = FreeCAD.ActiveDocument.WirePath.MaxWireTemp
                cptemp = 4 #complete_raw_path[2][n][1]
                wire_color = WireColor(cptemp, mxtemp, 'Temperature')
            n += 1  #out of range if range starts at 1
            # assign wire color
            wire_trajectory.ViewObject.LineColor = wire_color

        # move machine ---------------------------------------------------
        # side A
        # -XA
        base_XA = XA.Placement.Base
        rot_XA = XA.Placement.Rotation
        base_XA = FreeCAD.Vector(pa.x-xoff, base_XA.y, base_XA.z)
        XA.Placement = FreeCAD.Placement(base_XA, rot_XA)
        # -YA
        base_YA = YA.Placement.Base
        rot_YA = YA.Placement.Rotation
        base_YA = FreeCAD.Vector(pa.x-xoff, pa.y-yoff, base_XA.z)
        YA.Placement = FreeCAD.Placement(base_YA, rot_XA)
        # -XB
        base_XB = XB.Placement.Base
        rot_XB = XB.Placement.Rotation
        base_XB = FreeCAD.Vector(pb.x-xoff, base_XB.y, base_XB.z)
        XB.Placement = FreeCAD.Placement(base_XB, rot_XB)
        # -YB
        base_YB = YB.Placement.Base
        rot_YB = YB.Placement.Rotation
        base_YB = FreeCAD.Vector(pb.x-xoff, pb.y-yoff, base_XB.z)
        YB.Placement = FreeCAD.Placement(base_YB, rot_XB)
        # gui update -------------------------------------------------------
        FreeCAD.Gui.updateGui()
        time.sleep(animation_delay)
        #input("Press Enter to continue...")


def projectEdgeToTrajectory(PA, PB, Z0, Z1):
    # aux function of runSimulation
    # projects shape points to machine workplanes
    
    # DONE fix so wire streches out to match machine width (ZLength)
    
    pa = FreeCAD.Vector(PA[0], PA[1], PA[2])
    pb = FreeCAD.Vector(PB[0], PB[1], PB[2])
    #line_vector = FreeCAD.Vector(PA[0]-PB[0], PA[1]-PB[1], PA[2]-PB[2]).normalize()
    #print(pa + line_vector*(pa[2] - Z0), " - ", line_vector*(pa[2] - Z0))
    #input("press enter\n")
    
    vx = pb[2] - pa[2] #z
    vy = pb[1] - pa[1] #y
    vz = pb[0] - pa[0] #x

    scale = -(pa[2] - Z0) / vx
    newA_y = pa[1] + vy * scale
    newA_z = pa[0] + vz * scale

    scale = -(pb[2] - Z1) / vx
    newB_y = pb[1] + vy * scale
    newB_z = pb[0] + vz * scale

    new_pa = FreeCAD.Vector(newA_z, newA_y, Z0)
    new_pb = FreeCAD.Vector(newB_z, newB_y, Z1)

    return new_pa, new_pb


def WireColor(value, crange, ctype):
    if ctype == 'Temperature':
        k = value / crange*1.0
        r = k
        g = 0.0
        b = 1.0 - k

    if ctype == 'Speed':
        k = value / crange*1.0
        r = 0.0
        g = k
        b = 1.0 - k

    return (r, g, b)
    
def delWithChildren(obj):
	doc = FreeCAD.ActiveDocument
	for o in obj.OutList:
		delWithChildren(o)
	doc.removeObject(obj.Name)	

def clearWireTrack():
    
    group_obj = FreeCAD.ActiveDocument.getObject('WireTrajectory')
    if group_obj != None:
        delWithChildren(FreeCAD.ActiveDocument.getObject('WireTrajectory'))
        #delWithChildren(FreeCAD.ActiveDocument.getObject('Wire'))
        returnHome()
        FreeCAD.ActiveDocument.getObject('HWS_Machine').ClearTrajectory = False

def returnHome():
    # reset machine position
    homePlm = FreeCAD.Placement(FreeCAD.Vector(0,0,0),FreeCAD.Rotation(FreeCAD.Vector(0,0,0),0))
    FreeCAD.ActiveDocument.getObject('XA').Placement = homePlm
    FreeCAD.ActiveDocument.getObject('XB').Placement = homePlm
    FreeCAD.ActiveDocument.getObject('YA').Placement = homePlm
    FreeCAD.ActiveDocument.getObject('YB').Placement = homePlm
    FreeCAD.ActiveDocument.getObject('HWS_Machine').ReturnHome = False
    
def getType(obj):
    """getType(object): returns the Draft type of the given object"""
    import Part
    if not obj:
        return None
    if isinstance(obj,Part.Shape):
        return "Shape"
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        return "Sketch"
    if (obj.TypeId == "Part::Line"):
        return "Part::Line"
    if (obj.TypeId == "Part::Offset2D"):
        return "Offset2D"
    if obj.isDerivedFrom("Part::Feature"):
        return "Part"
    if (obj.TypeId == "App::Annotation"):
        return "Annotation"
    if obj.isDerivedFrom("Mesh::Feature"):
        return "Mesh"
    if obj.isDerivedFrom("Points::Feature"):
        return "Points"
    if (obj.TypeId == "App::DocumentObjectGroup"):
        return "Group"
    if (obj.TypeId == "App::Part"):
        return "App::Part"
    if "Proxy" in obj.PropertiesList:
        if hasattr(obj.Proxy,"Type"):
            return obj.Proxy.Type
    return "Unknown"

