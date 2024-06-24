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
import FreeCADGui
import Part
import time
import json
import HWS_SimMachine as HWS_SM
import HWS_Foam
from PySide import QtGui

#remova when not needed
from pprint import pprint


class WirePathFolder:
    def __init__(self, obj):
        obj.addProperty('App::PropertyVector', 'ZeroPoint', 'Machine Limits')
        obj.addProperty('App::PropertyBool', 'UpdateContent')
        obj.addProperty('App::PropertyFloat', 'MaxCutSpeed', 'Machine Limits')
        obj.addProperty('App::PropertyFloat', 'MaxWireTemp', 'Machine Limits')
        #obj.addProperty('App::PropertyFloat', 'setCutSpeed', 'PathSettings')
        #obj.addProperty('App::PropertyFloat', 'setWireTemp', 'PathSettings')
        obj.addProperty('App::PropertyInteger','FoamIndex','Foam Settings')
        obj.addProperty('App::PropertyEnumeration', 'TrajectoryColor', 'View')
        obj.TrajectoryColor = ['Speed', 'Temperature']
        obj.Proxy = self
        
        obj.MaxCutSpeed = 10
        obj.MaxWireTemp = 80
        
        obj.FoamIndex = 0 #Default = 0

        #obj.setCutSpeed = 4
        #obj.setWireTemp = 25

    def execute(self, fp):
        pass
        """
        for obj in FreeCAD.ActiveDocument.Objects:
            try:
                if obj.CutSpeed == 2:
                    obj.CutSpeed = fp.setCutSpeed

                if obj.WireTemperature == 50:
                    obj.WireTemperature = fp.setWireTemp

            except:
                pass
        """


class WirePathViewProvider:
    def __init__(self, obj):
        obj.Proxy = self

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/WirePath.svg'

class InnerPathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/ShapePath.svg'
    
    """
    def attach(self, obj):
        #Attach things.
        self.ViewObject = obj
        self.Object = obj.Object
    """


class InnerPath:
    def __init__(self, obj, inner_path, orig_obj):
        obj.addProperty('App::PropertyString',
                       'ShapeName',
                       'Path Data').ShapeName = orig_obj.Name

        obj.addProperty('App::PropertyPythonObject',
                        'RawPath',
                        'Path Data')
        
        obj.addProperty('App::PropertyFloat',
                        'PathALength',
                        'Path Settings').PathALength = 0.0
        
        obj.addProperty('App::PropertyFloat',
                        'PathBLength',
                        'Path Settings').PathBLength = 0.0
        """
        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 2.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 50.0
        """
        """
        obj.addProperty('App::PropertyFloat',
                        'PointDensity',
                        'Path Settings',
                        'Path density in mm/point').PointDensity = 5.0
        
        obj.addProperty('App::PropertyBool',
                        'Reverse',
                        'Path Settings',
                        'Reverses the cut direction of this path').Reverse = False
        """       
        
        obj.addProperty('App::PropertyBool',
                        'ShowMachinePath',
                        'Visualization',
                        'Shows the path projected to the machine sides')
        
        """
        obj.addExtension('Part::AttachExtensionPython')

        obj.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0.0000000000, 0.0000000000, 0.0000000000),  FreeCAD.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
        obj.MapReversed = False
        obj.Support = [FreeCAD.ActiveDocument.getObject(orig_obj.Name)]
        obj.MapPathParameter = 0.000000
        obj.MapMode = 'ObjectXY'
        """
        obj.Proxy = self

        obj.RawPath = inner_path
        obj.Shape = PathToShape(obj.RawPath)

    def execute(self, fp):
        pass
        # handle attatchment
        #fp.positionBySupport()
        

class ShapePath:
    def __init__(self, obj, selObj):
        obj.addProperty('App::PropertyString',
                        'ShapeName',
                        'Path Data').ShapeName = selObj.Name
        """
        obj.addProperty('App::PropertyInteger',
                         'FoamIndex',
                         'Foam Settings').FoamIndex = 0
        """
        obj.addProperty('App::PropertyPythonObject',
                        'RawPath',
                        'Path Data')
        
        obj.addProperty('App::PropertyFloat',
                        'PathALength',
                        'Path Settings').PathALength = 0.0
        
        obj.addProperty('App::PropertyFloat',
                        'PathBLength',
                        'Path Settings').PathBLength = 0.0
        """
        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 2.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 50.0
        """
        obj.addProperty('App::PropertyFloat',
                        'PointDensity',
                        'Path Settings',
                        'Path density in mm/point').PointDensity = 5.0

        obj.addProperty('App::PropertyBool',
                        'Reverse',
                        'Path Settings',
                        'Reverses the cut direction of this path').Reverse = False
        
        obj.addProperty('App::PropertyBool',
                        'ShowMachinePath',
                        'Visualization',
                        'Shows the path projected to the machine sides')

        obj.Proxy = self
        
        shape = FreeCAD.ActiveDocument.getObject(obj.ShapeName)

        obj_parts = []
        inner_parts_Path_AB = []
        obj_parts, inner_parts_Path_AB = ShapeToHWSPath(shape, obj.PointDensity, reverse=obj.Reverse)
        
        obj.RawPath = obj_parts[0]
        obj.Shape = PathToShape(obj.RawPath)

        #add inner parts
        if len(obj_parts) > 1:
            inner_shapepathobj = []
            for i in range(1, len(obj_parts)):
                inner_PartName = 'ShapePath_' + selObj.Name+"_" + str(i-1)
                inner_part_obj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', inner_PartName)
                inner_part_obj.Label = inner_part_obj.Name
                inner_shapepathobj.append( inner_part_obj )
                
                # initialize python object
                InnerPath(inner_shapepathobj[i-1], obj_parts[i], selObj)
                InnerPathViewProvider(inner_shapepathobj[i-1].ViewObject)
                # modify color
                inner_shapepathobj[i-1].ViewObject.ShapeColor = (1.0, 1.0, 1.0)
                inner_shapepathobj[i-1].ViewObject.LineWidth = 1.0
                
                inner_shapepathobj[i-1].PathALength = inner_parts_Path_AB[i][0]
                inner_shapepathobj[i-1].PathBLength = inner_parts_Path_AB[i][1]
                # ToDo add margins to bounding box in XY plane
                
                WPFolder = FreeCAD.ActiveDocument.WirePath
                WPFolder.addObject(inner_shapepathobj[i-1])

        # hide original shape
        FreeCAD.ActiveDocument.getObject(obj.ShapeName).ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def execute(self, fp):
        
        shape = FreeCAD.ActiveDocument.getObject(fp.ShapeName)
        
        fp_parts = []
        fs_inner_parts_Path_AB = []
        fp_parts, fs_inner_parts_Path_AB  = ShapeToHWSPath(shape, fp.PointDensity, reverse=fp.Reverse)
        fp.RawPath = fp_parts[0]
        fp.Shape = PathToShape(fp.RawPath)

        # remove child and parent link objects (they need to be re-defined)
        for obj in FreeCAD.ActiveDocument.WirePath.Group:
            try:
                if obj.PathName == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
            except AttributeError:
                pass

            try:
                if obj.PathNameA == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
            except AttributeError:
                pass

            try:
                if obj.PathNameB == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
            except AttributeError:
                pass
            
            try:
                obj_split = obj.PathNameA.split('_')
                #print(obj.PathNameA, len(obj_split), obj_split[0]+'_'+obj_split[1] , fp.Name)
                if len(obj_split) > 2 and obj_split[0]+'_'+obj_split[1] == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
            except AttributeError:
                pass
            """
            try:
                obj_split = obj.PathNameB.split('_')
                if len(obj_split) > 2 and obj_split[0]+'_'+obj_split[1] == fp.Name:
                    FreeCAD.ActiveDocument.removeObject(obj.Name)
            except AttributeError:
                pass
            """

        # rename remove and add new inner part
        if len(fp_parts) > 1:
            inner_shapepathobj = []
            for i in range(1, len(fp_parts)):
                #print(fp.Name)
                tmp_obj = FreeCAD.ActiveDocument.getObjectsByLabel(fp.Name+"_" + str(i-1))[0]
                tmp_obj.Label = "tmp_" + str(i-1)
                FreeCAD.ActiveDocument.removeObject(tmp_obj.Name)

                inner_part_obj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', fp.Name+"_" + str(i-1))
                inner_part_obj.Label = fp.Name+"_" + str(i-1)
                inner_shapepathobj.append( inner_part_obj )
                # initialize python object
                InnerPath(inner_shapepathobj[i-1], fp_parts[i], shape)
                InnerPathViewProvider(inner_shapepathobj[i-1].ViewObject)
                # modify color
                inner_shapepathobj[i-1].ViewObject.ShapeColor = (1.0, 1.0, 1.0)
                inner_shapepathobj[i-1].ViewObject.LineWidth = 1.0
                
                inner_shapepathobj[i-1].PathALength = fs_inner_parts_Path_AB[i][0]
                inner_shapepathobj[i-1].PathBLength = fs_inner_parts_Path_AB[i][1]

                WPFolder = FreeCAD.ActiveDocument.WirePath
                WPFolder.addObject(inner_shapepathobj[i-1])
            #tree view
        HWS_SM.clearWireTrack()


class ShapePathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/ShapePath.svg'


class LinkPath:
    def __init__(self, obj, selA, selB, sel_point_AB = None):
        obj.addProperty('App::PropertyString',
                        'PathNameA',
                        'Link Data').PathNameA = selA.Object.Name

        obj.addProperty('App::PropertyString',
                        'PathNameB',
                        'Link Data').PathNameB = selB.Object.Name
                                                                #sel_point_AB[0]
        obj.addProperty('App::PropertyInteger',
                        'PathIndexA',                   
                        'Link Data').PathIndexA = pointFromPath(sel_point_AB[0], selA.Object.RawPath)
                                                                #sel_point_AB[1]
        obj.addProperty('App::PropertyInteger',
                        'PathIndexB',
                        'Link Data').PathIndexB = pointFromPath(sel_point_AB[1], selB.Object.RawPath)
        
        obj.addProperty('App::PropertyFloat',
                        'PathALength',
                        'Link Data').PathALength = 0.0
        
        obj.addProperty('App::PropertyFloat',
                        'PathBLength',
                        'Link Data').PathBLength = 0.0
        """
        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 2.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 50.0
        """
        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        # Fix for xrossing initpath and endpath 0 - 1
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathNameA).RawPath[0][obj.PathIndexA])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathNameA).RawPath[1][obj.PathIndexA])
        # append destination point in pathshape B
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathNameB).RawPath[0][obj.PathIndexB])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathNameB).RawPath[1][obj.PathIndexB])

        #print(lp_A)
        #print(lp_B)
        #print(str(FreeCAD.Vector(lp_B[0]).distanceToPoint(FreeCAD.Vector(lp_A[1]))))
        #print(str(FreeCAD.Vector(lp_B[1]).distanceToPoint(FreeCAD.Vector(lp_A[0]))))
        obj.PathALength = FreeCAD.Vector(lp_A[0]).distanceToPoint(FreeCAD.Vector(lp_A[1]))
        obj.PathBLength = FreeCAD.Vector(lp_B[1]).distanceToPoint(FreeCAD.Vector(lp_B[0]))
        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)


    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        #HWS_Machine_z = FreeCAD.ActiveDocument.HWS_Machine.ZLength
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_B (machine side B = ZLength)
        lp_A_len = 0
        lp_B_len = 0
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathNameA).RawPath[0][fp.PathIndexA])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathNameA).RawPath[1][fp.PathIndexA])

        # append aux control points
        has_c_points = False
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, lp_A[0][2]])
                lp_B.append([aux_p.x, aux_p.y, lp_B[0][2]])
                has_c_points = True
        # append destination point in pathshape B
        if has_c_points:
            lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[0][fp.PathIndexB])
            lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[1][fp.PathIndexB])
        else:
            lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[0][fp.PathIndexB])
            lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathNameB).RawPath[1][fp.PathIndexB])
        
        for i in range(len(lp_A)):
            if i < len(lp_A) - 1:
                lp_A_len += FreeCAD.Vector(lp_B[i][0],lp_B[i][1],lp_B[0][2]).distanceToPoint(FreeCAD.Vector(lp_B[i + 1][0],lp_B[i + 1][1],lp_B[0][2]))
                lp_B_len += FreeCAD.Vector(lp_A[i][0],lp_A[i][1],lp_A[0][2]).distanceToPoint(FreeCAD.Vector(lp_A[i + 1][0],lp_A[i + 1][1],lp_A[0][2]))
        fp.PathALength = lp_A_len
        fp.PathBLength = lp_B_len

        # joint both lists
        lp = (lp_A, lp_B)

        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)
        fp.update = False


class LinkPathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self

    def getIcon(self):
        import os
        __dir__ = os.path.dirname(__file__)
        return __dir__ + '/icons/PathLink.svg'


class InitialPath:
    def __init__(self, obj, selObj, sel_point = None):
        obj.addProperty('App::PropertyString',
                        'PathName',
                        'Link Data').PathName = selObj.Object.Name

        obj.addProperty('App::PropertyInteger', 
                        'PathIndex', 
                        'Link Data').PathIndex = pointFromPath(sel_point, 
                                                               selObj.Object.RawPath)
        """
        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 2.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 50.0
        """
        obj.addProperty('App::PropertyFloat',
                        'PathALength',
                        'Link Data').PathALength = 0.0
        
        obj.addProperty('App::PropertyFloat',
                        'PathBLength',
                        'Link Data').PathBLength = 0.0

        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        HWS_Machine = FreeCAD.ActiveDocument.HWS_Machine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex][2]))
        lp_B.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex][2]))
        # append destination point in pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex])
        
        obj.PathALength = FreeCAD.Vector(lp_A[0]).distanceToPoint(FreeCAD.Vector(lp_A[1]))
        obj.PathBLength = FreeCAD.Vector(lp_B[1]).distanceToPoint(FreeCAD.Vector(lp_B[0]))

        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)

    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        HWS_Machine = FreeCAD.ActiveDocument.HWS_Machine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        lp_A_len = 0
        lp_B_len = 0
        # append initial point from pathshape A
        lp_A.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[0][fp.PathIndex][2]))
        lp_B.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[1][fp.PathIndex][2]))
        # append aux control points
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, lp_A[0][2]])
                lp_B.append([aux_p.x, aux_p.y, lp_B[0][2]])

        # append destination point in pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[0][fp.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[1][fp.PathIndex])

        for i in range(len(lp_A)):
            if i < len(lp_A) - 1:
                lp_A_len += FreeCAD.Vector(lp_B[i][0],lp_B[i][1],lp_B[0][2]).distanceToPoint(FreeCAD.Vector(lp_B[i + 1][0],lp_B[i + 1][1],lp_B[0][2]))
                lp_B_len += FreeCAD.Vector(lp_A[i][0],lp_A[i][1],lp_A[0][2]).distanceToPoint(FreeCAD.Vector(lp_A[i + 1][0],lp_A[i + 1][1],lp_A[0][2]))
        fp.PathALength = lp_A_len
        fp.PathBLength = lp_B_len

        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)


class InitialPathViewProvider:
    def __init__(self,obj):
        obj.Proxy = self


class FinalPath:
    def __init__(self, obj, selObj, sel_point = None):
        obj.addProperty('App::PropertyString',
                        'PathName',
                        'Link Data').PathName = selObj.Object.Name

        obj.addProperty('App::PropertyInteger',
                        'PathIndex',
                        'Link Data').PathIndex = pointFromPath(sel_point, selObj.Object.RawPath)
        
        """
        obj.addProperty('App::PropertyFloat',
                        'CutSpeed',
                        'Path Settings').CutSpeed = 2.0

        obj.addProperty('App::PropertyFloat',
                        'WireTemperature',
                        'Path Settings').WireTemperature = 50.0
        """

        obj.addProperty('App::PropertyFloat',
                        'PathALength',
                        'Link Data').PathALength = 0.0
        
        obj.addProperty('App::PropertyFloat',
                        'PathBLength',
                        'Link Data').PathBLength = 0.0

        # add 5 control points
        for i in range(5):
            obj.addProperty('App::PropertyVector',
                            'ControlPoint' + str(i),
                            'Path Control Points')

        obj.addProperty('App::PropertyBool',
                        'PowerOffMachine',
                        'Path Settings').PowerOffMachine = True

        obj.addProperty('App::PropertyBool',
                        'EnableReturnPath',
                        'Path Settings').EnableReturnPath = True

        obj.addProperty('App::PropertyBool',
                        'update').update = False

        obj.Proxy = self
        # create for the first time
        HWS_Machine = FreeCAD.ActiveDocument.HWS_Machine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex])
        # append destination point in pathshape A
        lp_A.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[0][obj.PathIndex][2]))
        lp_B.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, FreeCAD.ActiveDocument.getObject(obj.PathName).RawPath[1][obj.PathIndex][2]))

        obj.PathALength = FreeCAD.Vector(lp_A[0]).distanceToPoint(FreeCAD.Vector(lp_A[1]))
        obj.PathBLength = FreeCAD.Vector(lp_B[1]).distanceToPoint(FreeCAD.Vector(lp_B[0]))

        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        obj.Shape = PathToShape(lp)

    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        HWS_Machine = FreeCAD.ActiveDocument.HWS_Machine
        lp_A = []  # link_path_A (machine side A = lower Z)
        lp_B = []  # link_path_A (machine side A = lower Z)
        lp_A_len = 0
        lp_B_len = 0
        # append initial point from pathshape A
        lp_A.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[0][fp.PathIndex])
        lp_B.append(FreeCAD.ActiveDocument.getObject(fp.PathName).RawPath[1][fp.PathIndex])
        # append aux control points
        for i in range(5):
            aux_p = fp.getPropertyByName('ControlPoint' + str(i))
            if ( aux_p.x > 0 or aux_p.y > 0 ) and aux_p.z == 0:
                # draw aux point if it has been modified
                lp_A.append([aux_p.x, aux_p.y, lp_A[0][2]])
                lp_B.append([aux_p.x, aux_p.y, lp_B[0][2]])

        # append destination point in pathshape A
        lp_A.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, lp_A[0][2]))
        lp_B.append(HWS_Machine.VirtualMachineZero + FreeCAD.Vector(0, 0, lp_B[0][2]))

        for i in range(len(lp_A)):
            if i < len(lp_A) - 1:
                lp_A_len += FreeCAD.Vector(lp_B[i][0],lp_B[i][1],lp_B[0][2]).distanceToPoint(FreeCAD.Vector(lp_B[i + 1][0],lp_B[i + 1][1],lp_B[0][2]))
                lp_B_len += FreeCAD.Vector(lp_A[i][0],lp_A[i][1],lp_A[0][2]).distanceToPoint(FreeCAD.Vector(lp_A[i + 1][0],lp_A[i + 1][1],lp_A[0][2]))
        fp.PathALength = lp_A_len
        fp.PathBLength = lp_B_len

        # joint both lists
        lp = (lp_A, lp_B)
        # create the shape to representate link in 3d space
        fp.Shape = PathToShape(lp)


class FinalPathViewProvider:
    def __init__(self, obj):
        obj.Proxy = self

def explore_lnk(dest_obj_name, prev_used_lnk, G93, len_pr_A = 0): 
    n = 0
    
    #i_next = 0
    add_last_point = False
    used_links = []
    ex_A = []
    ex_B = []
    rc = []
    #exit_rc = []
    HWS_M = FreeCAD.ActiveDocument.HWS_Machine
    #link = False
    

    #print("len pr_A",len_pr_A)

    used_links.extend(prev_used_lnk)

    #add destination firstPath from obj_name
    thisLink = FreeCAD.ActiveDocument.getObject(dest_obj_name)
    #firstPath temperature and speed commands
    

    
    #print(thisLink.Length)
    rc.append([len(ex_A) + len_pr_A, 
               None, #thisLink.CutSpeed, 
               None, #thisLink.WireTemperature, 
               thisLink.Name, 
               [thisLink.PathALength, thisLink.PathBLength]])

    for i in range(5):
        aux_p = thisLink.getPropertyByName('ControlPoint' + str(i))
        if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
            # draw aux point if it has been modified
            ex_A.append((aux_p.x, aux_p.y, 0))
            ex_B.append((aux_p.x, aux_p.y, HWS_M.ZLength))
            rc.append([len(ex_A) + len_pr_A, 
                       None, #thisLink.CutSpeed, 
                       None, #thisLink.WireTemperature, 
                       thisLink.Name, 
                       [thisLink.PathALength, thisLink.PathBLength]])

    
    #fix pathname, store name not label
    #add destination firstPath from obj_name
    try:
        thisPath = FreeCAD.ActiveDocument.getObject(thisLink.PathName)
    except:
        thisPath = FreeCAD.ActiveDocument.getObject(thisLink.PathNameB)  #redo wiregroup parts
    

    #detect if firstPath have links to innerparts and do them first
    #then detect if firstPath have links to other object
    
    def is_link_used(lnk_name):
        for LN in used_links:
            if LN == lnk_name:
                return True
        return False

    try:
        pI = thisLink.PathIndex
    except:
        pI = thisLink.PathIndexB

    pI_passes = 0
    num_link_at_pI = 0

    

    for obj in FreeCAD.ActiveDocument.findObjects('Part::FeaturePython','Link_'):
        if obj.PathIndexA == pI:
            num_link_at_pI += 1
    #print("\nnumber of links from point", pI, " is ", num_link_at_pI) 

    #print("length of path: ",len(thisPath.RawPath[0]))
        
    current_path_points_left = len(thisPath.RawPath[0])
        
    for i in range(len(thisPath.RawPath[0])):
        #start at point firstPath of where initialpath ends
        n = i + pI

        #if firstPath is out of points break out and exit to finalpath

        #do not exit from current obj until on last point
        #


        if n >= len(thisPath.RawPath[0]):
            n = i + 1 + pI - len(thisPath.RawPath[0])



        #detect if link is on last point to be able to follow through to next object
        #print("point: ",n)
        #print("index of points ", i)
        #print("number of ponts", len(thisPath.RawPath[0]))
        
         

        if n == pI:
            pI_passes += 1
        
        #print('\n')
        #input("Press Enter to continue...\n")

        #print("current_path_points_left: ",current_path_points_left)
        


        """
        if(n == pI):
            print(num_link_at_pI, ' links at point: ', n)
            print(pI_passes - 1, ' passes of point')
        else:
            print(n)   
            print(pI_passes - 1, ' passes of point')
        """
        

        """
        if n == pI:
            print('at path start:',pI)    
        
        #print('at last point')

        print("at shape: ", thisPath.Name)
        print("used links: ", used_links)
        """

        #    add_last_point = True
        """
        
        print("last link: ", used_links[len(used_links) - 1])
        print("links to path:", thisPath.Name)
        print("link to check if to follow: ", obj.Name)
        """

        for obj in FreeCAD.ActiveDocument.findObjects('Part::FeaturePython','Link_'):
            
            #if is_link_used(obj.Name):
            #    continue
            
            link_lable_split = obj.Label.split("_")

            if len(link_lable_split) > 4:
                name_to_dest = link_lable_split[3]
            else:
                name_to_dest = link_lable_split[2]

            links_to_inner_part = False

            #print('checking link: ',obj.Name)
            


            try:
                if len(link_lable_split) > 3 and name_to_dest == thisPath.ShapeName:
                    links_to_inner_part = True
                    #print(obj.Name, ' links to inner part')
                else:
                    links_to_inner_part = False
                    #print('at link: ',obj.Name)
            except:
                links_to_inner_part = False

            if obj.PathIndexA == n and current_path_points_left >= 1 and links_to_inner_part and obj.PathNameA ==  thisPath.Name and not(is_link_used(obj.Name)):
                #print("go to inner part")
                #print(obj.PathIndexA)
                #print('enter point:', obj.PathIndexA,' current point:', n)
                ex_A.append(thisPath.RawPath[0][n])
                ex_B.append(thisPath.RawPath[1][n])
                
                used_links.append(obj.Name)
                used_links, ex_ln_A, ex_ln_B, ex_rc = explore_lnk(obj.Name, used_links, G93, len(ex_A) + len_pr_A)
                            
                ex_A.extend(ex_ln_A)
                ex_B.extend(ex_ln_B)
                rc.extend(ex_rc)
                rc[len(rc) - 1] = [len(ex_A) + len_pr_A, 
                                   None, #obj.CutSpeed, 
                                   None, #obj.WireTemperature, 
                                   obj.Name, 
                                   [obj.PathALength, obj.PathBLength]]
                 

            elif current_path_points_left <= 1 and not(links_to_inner_part) and obj.PathNameA ==  thisPath.Name and not(is_link_used(obj.Name)):
                #print('go to next part')
                ex_A.append(thisPath.RawPath[0][n])
                ex_B.append(thisPath.RawPath[1][n])

                used_links.append(obj.Name)
                used_links, ex_ln_A, ex_ln_B, ex_rc = explore_lnk(obj.Name, used_links, G93, len(ex_A) + len_pr_A)
                ex_A.extend(ex_ln_A)
                ex_B.extend(ex_ln_B)
                rc.extend(ex_rc)
                
                
                #print(len(rc))
            
            

            """
            add_last_point = False
            
            if not(is_link_used(obj.Name)) and not(links_to_inner_part) and n == obj.PathIndexA and pI_passes >= num_link_at_pI:
                add_last_point = True
                #              
                #print(n, "link name: ",obj.Name)
                #print(used_links)
                #print("is link used :",is_link_used(obj.Name))
                #print("number of used links: ", len(used_links))
                #print("number of links att current point: ", num_link_at_pI)
                #print("number off passes of point", n, pI_passes)

                
                #print("current shape/link: ",thisPath.Label)
                #print("links from: ", obj.PathNameA)
                #print("Current point nr.:", n)
                #print("is last point: ", add_last_point)
                #print("current point vector: ", thisPath.RawPath[1][n])
                #print("links from point nr.: ",obj.PathIndexA)
                
                
                #print("used links:")
                #print(used_links)
                #print(" ")
                #
            
            

            if links_to_inner_part and obj.PathIndexA == n and obj.PathNameA ==  thisPath.Name and not(is_link_used(obj.Name)):
                #innerpart temperature and speed commands
                print('is folowing to inner part')
                ex_A.append(thisPath.RawPath[0][n])
                ex_B.append(thisPath.RawPath[1][n])
                #print("inner part",obj.Label)
                #rc.append([len(ex_A), thisPath.CutSpeed, thisPath.WireTemperature])
                
                used_links.append(obj.Name)
                #print("into inner part explore_lnk", obj.Label)
                #print("first point: ",ex_B[len(ex_B) - 1])
                used_links, ex_ln_A, ex_ln_B, ex_rc = explore_lnk(obj.Name, used_links, G93, len(ex_A) + len_pr_A)
                #print("out from inner part explore_lnk", obj.Label)
                #
                #print("last point: ",ex_ln_B[len(ex_ln_B) - 1])
                #print("current pathName:", thisPath.Label)
                #print("current linkName:", obj.Label)
                            
                ex_A.extend(ex_ln_A)
                ex_B.extend(ex_ln_B)
                rc.extend(ex_rc)
                #print(rc[len(rc) - 1])
                rc[len(rc) - 1] = [len(ex_A) + len_pr_A, 
                                   None, #obj.CutSpeed, 
                                   None, #obj.WireTemperature, 
                                   obj.Name, 
                                   [obj.PathALength, obj.PathBLength]]   

            elif not(links_to_inner_part) and add_last_point and obj.PathIndexA == n and obj.PathNameA ==  thisPath.Name and not(is_link_used(obj.Name)):
                # obj temperature and speed commands
                print('is folowing to new path')
                ex_A.append(thisPath.RawPath[0][n])
                ex_B.append(thisPath.RawPath[1][n])
                #print("object: ",obj.Label)
                #print("last point", thisPath.Label,len(ex_A) + len_pr_A)
                #rc.append([len(ex_A) + len_pr_A, thisPath.CutSpeed, thisPath.WireTemperature])

                used_links.append(obj.Name)
                #print("into obj part explore_lnk", obj.Label)
                #print("first point: ",ex_B[len(ex_B) - 1])
                used_links, ex_ln_A, ex_ln_B, ex_rc = explore_lnk(obj.Name, used_links, G93, len(ex_A) + len_pr_A)
                #print("out obj part explore_lnk", obj.Label)
                #print("last point: ",ex_ln_B[len(ex_ln_B) - 1])
                #print("current pathName:", thisPath.Name)
                #print("current linkName:", obj.Label)
                ex_A.extend(ex_ln_A)
                ex_B.extend(ex_ln_B)
                rc.extend(ex_rc)

                #exit_rc = [len(ex_A) + len_pr_A, 
                #           obj.CutSpeed, 
                #           obj.WireTemperature, 
                #           obj.Name, 
                #           [obj.PathALength, obj.PathBLength]]   

            """ 
        
        #print(i, n, current_path_points_left, current_path_points_left)

        if i == len(thisPath.RawPath[0]) and dest_obj_name == "InitialPath":
            pass
        else:
            #print('adding last point')
            #TODO: when add last point of shape use thisLink instead
            
            #if not(add_last_point):# and (len(ex_A) + len_pr_A) < len(thisPath.RawPath[0]):
            
            
                
            
            ex_A.append(thisPath.RawPath[0][n])
            ex_B.append(thisPath.RawPath[1][n])
            
            rc.append([len(ex_A) + len_pr_A, 
                        None, #thisPath.CutSpeed, 
                        None, #thisPath.WireTemperature, 
                        thisPath.Name, 
                        [thisPath.PathALength, thisPath.PathBLength]])
                
                #if len(rc) > 0 and rc[len(rc) - 1][3] != rc[len(rc) - 2][3]:
                #    print("going back to shape, use link properties from link")
                #    print("got to:",rc[len(rc) - 1][3])
                #    print("go to point:", ex_B[len(ex_B) - 1])
                    #print("exit rc command:",exit_rc)
            
                

        current_path_points_left -= 1
        #print('\n')
        
    return [used_links, ex_A, ex_B, rc]


def traceObjectsAndLinksForRawPath(G93 = False):
    HWS_M = FreeCAD.ActiveDocument.HWS_Machine
    pr_A = []  # partial route A
    pr_B = []  # partial route B
    route_commands = [] # stores commands issued along the route(speed, temp..)
    used_links = [] # just a dummie

    #TODO find out the order of shapes and links
    """
    for test_obj in FreeCAD.ActiveDocument.findObjects('Part::FeaturePython','Link_'):
        print('Link: ', test_obj.Name)
    for test_obj in FreeCAD.ActiveDocument.findObjects('Part::FeaturePython','ShapePath_'):
        print('Shape: ', test_obj.Name)
    """
    #TODO: Add length between points in A and B to route_commands[2][i][4]
    
    # start explore at initialpath
    iphobj = FreeCAD.ActiveDocument.InitialPath

    used_links, pr_A, pr_B, route_commands = explore_lnk(iphobj.Name, [iphobj.Name], G93)
    route_commands.pop()

    #uggly fix to remove unnecesary points last points when cutting more than one shape
    #TODO count only number of shapes in cut path
    num_of_shapes = 0
    for shape_obj in FreeCAD.ActiveDocument.findObjects('Part::FeaturePython','ShapePath_'):
        shape_obj_split = shape_obj.Label.split("_")
        if len(shape_obj_split) < 3:
            num_of_shapes += 1
    
    #print(num_of_shapes)
    if num_of_shapes > 1:
        for s_i in range(num_of_shapes-1):
            #print('pop')
            pr_A.pop()
            pr_B.pop()
            route_commands.pop()
        
    #pr_A.extend(exp_lnk_A)
    #pr_B.extend(exp_lnk_B)
    #route_commands.extend(exp_rc)

    #end with finalpath
    fphobj = FreeCAD.ActiveDocument.FinalPath

    route_commands.append([len(pr_A), 
                           None, #fphobj.CutSpeed, 
                           None, #fphobj.WireTemperature, 
                           fphobj.Name, 
                           [fphobj.PathALength, fphobj.PathBLength]])   

    for i in range(0, 5):
        aux_p = fphobj.getPropertyByName('ControlPoint' + str(i))
        if (aux_p.x > 0 or aux_p.y > 0) and aux_p.z == 0:
            # draw aux point if it has been modified
            pr_A.append((aux_p.x, aux_p.y, 0))
            pr_B.append((aux_p.x, aux_p.y, HWS_M.ZLength))
            route_commands.append([len(pr_A), 
                                   None, #fphobj.CutSpeed, 
                                   None, #fphobj.WireTemperature, 
                                   fphobj.Name, 
                                   [fphobj.PathALength, fphobj.PathBLength]])
    
    pr_A.append([HWS_M.VirtualMachineZero.x, HWS_M.VirtualMachineZero.y, HWS_M.VirtualMachineZero.z])
    pr_B.append([HWS_M.VirtualMachineZero.x, HWS_M.VirtualMachineZero.y, HWS_M.VirtualMachineZero.z + HWS_M.ZLength])

    complete_raw_path = (pr_A, pr_B, route_commands)
    return complete_raw_path

def addKerf2Faces(points, sel_obj, inner_part_index, foam_type=None, inner_part=False):
    #print(foam_type)
    if foam_type == None:
        foam_type = ["Default", 1.6, 4.0, 1.9, 75] #[0, 'EXP Wire 0.5', True, [4.5, 20], [2, 20], 0.6, 0.8]
        #"Default", 1.6, 4.0, 1.9, 75
    
    speed = float(foam_type[2])
    kerf1 = float(foam_type[1])
    kerf2 = float(foam_type[3])   #kerf at profile 2/5 length of big profile length


    w_list0 = []
    w_list1 = []

    for p_i in range(len(points)):
        for i in range(len(points[p_i][0])):  # 0 = side A, 1 = side B            
            w_list0.append(points[p_i][0][i])
            w_list1.append(points[p_i][1][i])

    wire0 = Part.makePolygon(w_list0)
    wire1 = Part.makePolygon(w_list1)

    length1 = wire0.Length
    length2 = wire1.Length

    #kerf1 length is at 100% of profile A length
    #kerf2 length is at  40% of profile A length
    #what is kerf at a given length diffrence?

    if kerf1 != 0 or kerf2 != 0:

        kerf_one = kerf1 / 2
        kerf_two = kerf2 / 2
        #print('kerf1:', kerf_one)
        #print('kerf2:', kerf_two)



        #x1 = kerf1 0,450
        #y1 = length1 
        
        #x2 = kerf2 0,449
        #y2 = length2

        #k = (y2 - y1)  / (x2 - x1)



        #y = k*x + m (svensk)   #y = m*x + b (internationell)

        #k = (m-y)/x
        #m = y-(k*x)
        #m-y =-(k*x)
        #m-y =k*x
        #k = (m-y)/x
        #(m-y)/k = x

        k = -0.6/(kerf_two - kerf_one) 
        #print("K:",k)
        m = 1-(k*kerf_one) 
        #print("M:",m)
        if(length1 <= length2):
            tip_kerf = ((length1/length2) - m)/k
        else:
            tip_kerf = ((length2/length1) - m)/k
    else:
        root_kerf = 0
        tip_kerf = 0
    
    #print(tip_kerf)

    
    inner_paths_AB = []

    if not(inner_part):
        current_obj = FreeCAD.ActiveDocument.getObjectsByLabel("ShapePath_"+sel_obj.Name)[0]
        current_obj.PathALength = length1
        current_obj.PathBLength = length2
        inner_paths_AB = None
    else:
        
        #TODO:add profile A and B lengths to inner parts
        #inner parts not added until later
        #pass A and B length to when inner parts are added?
        #maybe store innerparts profile lengths i outer part?

        #print("ShapePath_"+sel_obj.Name+"_"+str(inner_part_index - 1))
        #current_obj = FreeCAD.ActiveDocument.getObjectsByLabel("ShapePath_"+sel_obj.Name+"_"+str(inner_part_index - 1))[0]
        inner_paths_AB = [length1,length2]
        #print("PathA length= ",length1)
        #current_obj.PathALength = length1
        #print("PathB length= ",length2)
        #current_obj.PathBLength = length2

    

    #makeoffset2d settings
    join = 2
    join_on_fail = 1
    fill = False
    openResult = False
    intersection = False
    
    #add kerf negative to inner part
    if inner_part:
        root_kerf = kerf_one * -1
        tip_kerf = tip_kerf * -1
    else:
        root_kerf = kerf_one

    #print('root kerf:', root_kerf)
    #print('tip kerf:', tip_kerf)
    #print('length1:', length1)
    #print('length2:', length2)

    try:                        
        if length1 > length2:
            offset2d_face0 = wire0.makeOffset2D(root_kerf,join,fill,openResult,intersection) # root
            offset2d_face1 = wire1.makeOffset2D(tip_kerf,join,fill,openResult,intersection) # tip
        elif length2 > length1:
            offset2d_face0 = wire0.makeOffset2D(tip_kerf,join,fill,openResult,intersection) # tip
            offset2d_face1 = wire1.makeOffset2D(root_kerf,join,fill,openResult,intersection) # root
        else:
            offset2d_face0 = wire0.makeOffset2D(root_kerf,join,fill,openResult,intersection)#,join,fill,openResult,intersection) # go fast as root on both with same kerf
            offset2d_face1 = wire1.makeOffset2D(root_kerf,join,fill,openResult,intersection)#,join,fill,openResult,intersection)
    except:
        try:
            if length1 > length2:
                offset2d_face0 = wire0.makeOffset2D(root_kerf,join_on_fail,fill,openResult,intersection) # root
                offset2d_face1 = wire1.makeOffset2D(tip_kerf,join_on_fail,fill,openResult,intersection) # tip
            elif length2 > length1:
                offset2d_face0 = wire0.makeOffset2D(tip_kerf,join_on_fail,fill,openResult,intersection) # tip
                offset2d_face1 = wire1.makeOffset2D(root_kerf,join_on_fail,fill,openResult,intersection) # root
            else:
                offset2d_face0 = wire0.makeOffset2D(root_kerf,join_on_fail,fill,openResult,intersection)#,join,fill,openResult,intersection) # go fast as root on both with same kerf
                offset2d_face1 = wire1.makeOffset2D(root_kerf,join_on_fail,fill,openResult,intersection)#,join,fill,openResult,intersection)
        except:
            print('Error, Check for points to close to each other!')
            return
     
    kerf_points = []

    for i in range(len(offset2d_face0.Edges)):
        kerf0_points = []
        kerf1_points = []
        for v_i in range(len(offset2d_face0.Edges[i].Vertexes)):
            kerf0_points.append(offset2d_face0.Edges[i].Vertexes[v_i].Point)
            kerf1_points.append(offset2d_face1.Edges[i].Vertexes[v_i].Point)
        kerf_points.append([kerf0_points, kerf1_points])
  
    return kerf_points, inner_paths_AB

def ShapeToHWSPath(selected_object, precision, reverse=False): #, inner_shape=False):

    # Creates the wire path for an input shape. Returns a list of points with
    # a structure: trajectory_list[machine_side][xyz]
    # precision -> distance between discrete points of the trajectory (mm/point)
    #------------------------------------------------------------------------- 0
    # split faces in reference to XY plane
    
    transversal_faces = []
    parallel_faces = []
    inner_part_AB_length = []

    def find_tf_n_pf(refine_shapes = False):

        if not(refine_shapes):
            shapes = selected_object.Shape
        else:
            shapes = refine_shapes

        for face in shapes.Faces:
            if (face.normalAt(0, 0).cross(FreeCAD.Vector(0, 0, 1))).Length > 0.001:
                transversal_faces.append(face)
            else:
                parallel_faces.append(face)


    #done - todo add support for hollow objects, spars, ribbs and cut outs

    #if parallel_faces > 2 do refine: shape.removeSplitter()
    
    #def recreate_parallel_faces(t_faces):
        #todo get originial edges from original object, have original edges stored in inner_part when created
        #return None

    find_tf_n_pf()

    def doFacesTouch(face_A, face_B, show_edge = False):
        # auxiliar function to test if two faces share and edge
        for edge_A in face_A.Edges:
            for edge_B in face_B.Edges:
                v_AB = (edge_A.CenterOfMass - edge_B.CenterOfMass).Length
                if v_AB < 0.001:
                    return True
        return False

    #------------------------------------------------------------------------- 1
    # order transversal faces to be consecutive
    consecutive_faces = []
    consecutive_faces.append(transversal_faces[0])
    
    #reverse = True  # reverse the tool trajectory with this boolean
    
    #todo fix reverse 
    #if reverse:
    #    transversal_faces.reverse()

    num_parts = 0

    parts = []
    parts.append(0)
   
    for i in range( len( transversal_faces ) ):
      
        

        if i == len(consecutive_faces):
            consecutive_faces.append( transversal_faces[i] )
            parts.append(i)
            num_parts += 1

        face_A = consecutive_faces[i]
        for face_B in transversal_faces[1:]:
            v_AB = (face_A.CenterOfMass - face_B.CenterOfMass).Length
            if v_AB > 0.001:
                if doFacesTouch( face_A, face_B ):
                    appended = False
                    for face_C in consecutive_faces:
                        if (face_B.CenterOfMass - face_C.CenterOfMass).Length < 0.001:
                            appended = True
                        else:
                            pass

                    if not(appended):
                        consecutive_faces.append( face_B )
                        break
                else:
                    pass

    #------------------------------------------------------------------------- 2
    # project path vertexes to a XY plane placed at wire start and end so they form
    # the toolpath
    def vertexesInCommon( face_a, face_b ):
        # aux function to find the vertexes shared by two connected rectangles
        a_i = 0
        b_i = 0
        cm_a_found = False
        cm_b_found = False
        for a_i in range(len(face_a.Vertexes)):
            
            for b_i in range(len(face_b.Vertexes)):
                if not(cm_a_found) and (face_a.Vertexes[a_i].Point - face_b.Vertexes[b_i].Point).Length < 0.001:
                    cm_a = face_a.Vertexes[a_i]
                    cm_a_found = True

                if not(cm_b_found) and cm_a_found: 
                    if (cm_a.Point - face_a.Vertexes[a_i].Point).Length > 0.001 and (face_a.Vertexes[a_i].Point - face_b.Vertexes[b_i].Point).Length < 0.001:
                        cm_b = face_b.Vertexes[b_i]
                        cm_b_found = True
                
                if cm_a_found and cm_b_found:
                    cm = [cm_a, cm_b]
                    return cm
 
    def last_part_of_ToHWSPath(c_faces, p_faces, resoluiton, inner_part_index, is_inner_part):

        # discretize length
        #discrete_length = 20 # mm/point
        discrete_length = resoluiton
        c_faces.append(c_faces[0])
        trajectory = []
        part_AB_length = []
        wirepath = []
        for i in range(len(c_faces)-1): # xrange -> range ok?
            face_a = c_faces[i]
            face_b = c_faces[i+1]

            cm = vertexesInCommon( face_a, face_b)
            #print(cm)
            cm_a = cm[0]
            cm_b = cm[1]

            CG0 = p_faces[0].CenterOfMass
            CG1 = p_faces[1].CenterOfMass
            edge_list = []
            edge_list_0 = []
            edge_list_1 = []
            for edge in face_a.Edges:
                if abs(edge.CenterOfMass.z-CG0.z) < 0.01:
                    edge_list_0.append( edge )

                if abs(edge.CenterOfMass.z-CG1.z)< 0.01:
                    edge_list_1.append( edge )
            
            edge_list = edge_list_0 + edge_list_1
            tr_edge = []
            
            for edge in edge_list:
                p1,p2 = edge.discretize(2)
                if (p2-cm_a.Point).Length < 0.01:
                    data = [ edge, False ] # 0 or 1 means normal or reverse edge
                    tr_edge.append( data )

                elif (p1-cm_a.Point).Length < 0.01:
                    data = [ edge, True ]
                    tr_edge.append( data )

                if (p2-cm_b.Point).Length < 0.01:
                    data = [ edge, False ] # 0 or 1 means normal or reverse edge
                    tr_edge.append( data )

                elif (p1-cm_b.Point).Length < 0.01:
                    data = [ edge, True ]
                    tr_edge.append( data )

            if str(edge_list[0].Curve)[1:5] == 'Line' and str(edge_list[1].Curve)[1:5] == 'Line':
                TA = tr_edge[0][0].discretize(2)
                if tr_edge[0][1]:
                    TA.reverse()

                TB = tr_edge[1][0].discretize(2)
                if tr_edge[1][1]:
                    TB.reverse()

            else:
                #print(tr_edge)
                n_discretize = max( tr_edge[0][0].Length/discrete_length, tr_edge[1][0].Length/discrete_length )
                n_discretize = max( 2, n_discretize)
                TA = tr_edge[0][0].discretize( int(n_discretize) )
                if tr_edge[0][1]:
                    TA.reverse()

                TB = tr_edge[1][0].discretize( int(n_discretize) )
                if tr_edge[1][1]:
                    TB.reverse()
            
            traj_data = [ TA, TB ]
            #print(i, traj_data)
            trajectory.append(traj_data)

            new_i = len(trajectory) - 1
            
            if (trajectory[new_i][0][0] - trajectory[new_i][0][1]).Length < 0.01:
                print('Line is to short at side A')
                print('Remove this line and previus and creating new merged')
                prev_line_point1_A = trajectory[new_i-1][0][0] 
                this_line_point2_A = trajectory[new_i][0][1]
                prev_line_point1_B = trajectory[new_i-1][1][0] 
                this_line_point2_B = trajectory[new_i][1][1]

                new_line_point1_A = prev_line_point1_A
                new_line_point2_A = this_line_point2_A
                new_line_point1_B = prev_line_point1_B
                new_line_point2_B = this_line_point2_B

                trajectory.pop()
                trajectory.pop()
                new_data = [[new_line_point1_A,new_line_point2_A],[new_line_point1_B,new_line_point2_B]]
                trajectory.append(new_data)

            elif (trajectory[new_i][1][0] - trajectory[new_i][1][1]).Length < 0.01:
                print('Line is to short at side B')
                print('Removing this line and previus and creating new merged')
                prev_line_point1_A = trajectory[new_i-1][0][0] 
                this_line_point2_A = trajectory[new_i][0][1]
                prev_line_point1_B = trajectory[new_i-1][1][0] 
                this_line_point2_B = trajectory[new_i][1][1]

                new_line_point1_A = prev_line_point1_A
                new_line_point2_A = this_line_point2_A
                new_line_point1_B = prev_line_point1_B
                new_line_point2_B = this_line_point2_B
                
                trajectory.pop()
                trajectory.pop()
                new_data = [[new_line_point1_A,new_line_point2_A],[new_line_point1_B,new_line_point2_B]]
                trajectory.append(new_data) 

            #print(i, (trajectory[i][0][0] - trajectory[i][0][1]).Length)
     
        #todo add negative kerf to inner shape, done

        #TODO get foam setting from UI

        foam_cfg = FreeCAD.ActiveDocument.HWS_Machine.FoamConfig
        foam_index = FreeCAD.ActiveDocument.WirePath.FoamIndex

        #print(foam_cfg[foam_index])

        #foam = ["Default", 1.6, 4.0, 1.9, 75] #[0, 'EXP Wire 0.5', True, [4.5, 20], [2, 20], 0.6, 0.8]
        
        foam =  json.JSONDecoder().decode(foam_cfg[foam_index])

        trajectory, part_AB_length = addKerf2Faces(trajectory, selected_object, inner_part_index, foam, is_inner_part)
        
        # ------------------------------------------------------------------------ 3
        # trajectory structure
        # trajectory [ faces ] [ sideA, sideB ], [TrajectoryPoints (min of 2) ], [X,Y,Z]
        # -> clean trajectory list from repeated elements:
        clean_list_A = []
        clean_list_B = []
        for pt in trajectory:
            for i in range( len( pt[0] ) -1):
                PA_0 = pt[0][i]
                PA_1 = pt[0][i+1]
                #print(PA_0, " - ",PA_1)
                if (PA_0 - PA_1).Length > 0.001:
                    clean_list_A.append( pt[0][i] )
                    clean_list_B.append( pt[1][i] )
                else:
                    pass
        clt = [ clean_list_A, clean_list_B ] # clt -> clean trajectory
        
        # -> transform trajectory to a simple list to allow JSON serialization (save list)
        Tr_list_A = []
        Tr_list_B = []
        for i in range( len( clt[0] ) ): # xrange -> range ok?
            PA = [ clt[0][i].x, clt[0][i].y, clt[0][i].z ]
            PB = [ clt[1][i].x, clt[1][i].y, clt[1][i].z ]
            #print(PA)
            #print(PB)
            #print(' ')
            Tr_list_A.append( PA )
            Tr_list_B.append( PB )

        Tr_list_A.append( Tr_list_A[0] )
        Tr_list_B.append( Tr_list_B[0] )

        #print(Tr_list_B)
        
        wirepath = [ Tr_list_A, Tr_list_B ]
        # check that sideA  has the lower z value:
        if Tr_list_A[0][2] > Tr_list_B[0][2]:
            wirepath = [ Tr_list_B, Tr_list_A ]

        return wirepath, part_AB_length
    
    # itare through consecutive_faces splitt up by parts[]
    wirepath_return = []
    inner_part_AB_length = []
    
    #handle each part separat in last part
    r_cf = []
    lpa = []
    wpa = []
    parts_i = 0
    n = 0

    if num_parts > 0:
        for parts_i in range(len(parts)):
            n = parts_i + 1
            if n >= len(parts):
                r_cf = consecutive_faces[parts[parts_i]*1:]
                
                #add reverse to r_cf ?
                if not reverse:
                    r_cf.reverse()

                #wirepath_return.append(last_part_of_ToNiCrPath(r_cf, parallel_faces, precision, parts_i, True))
                wpa, lpa = last_part_of_ToHWSPath(r_cf, parallel_faces, precision, parts_i, True)
                wirepath_return.append(wpa)
                inner_part_AB_length.append(lpa)
            else:
                r_cf = consecutive_faces[parts[parts_i]*1:parts[parts_i+1]]
                
                #add reverse to r_cf ?
                if not reverse:
                    r_cf.reverse()

                if parts_i > 0:
                    #wirepath_return.append(last_part_of_ToNiCrPath(r_cf, parallel_faces, precision, parts_i, True))
                    wpa, lpa = last_part_of_ToHWSPath(r_cf, parallel_faces, precision, parts_i, True)
                    wirepath_return.append(wpa)
                    inner_part_AB_length.append(lpa)
                else:
                    #wirepath_return.append(last_part_of_ToHWSPath(r_cf, parallel_faces, precision, parts_i, False))
                    wpa, lpa = last_part_of_ToHWSPath(r_cf, parallel_faces, precision, parts_i, False)
                    wirepath_return.append(wpa)
                    inner_part_AB_length.append(lpa)
    else:
        r_cf = consecutive_faces
        
        #add reverse to r_cf ?
        if not reverse:
            r_cf.reverse()
        
        #wirepath_return.append(last_part_of_ToNiCrPath(r_cf, parallel_faces, precision, parts_i, False))
        wpa, lpa = last_part_of_ToHWSPath(r_cf, parallel_faces, precision, parts_i, False)
        wirepath_return.append(wpa)
        inner_part_AB_length.append(lpa)
    
    return wirepath_return, inner_part_AB_length

def PathToShape(point_list):
    # creates a compound of faces from a HWS point list to representate the wire
    # trajectory
    comp = []
    for i in range(len(point_list[0])-1):
        temp_list0 = list(point_list[0][i])
        temp_list0_i = list(point_list[0][i+1])
        temp_list1 = list(point_list[1][i])
        temp_list1_i = list(point_list[1][i+1])

        l0 = Part.LineSegment()
        l1 = Part.LineSegment()

        l0.StartPoint = (temp_list0[0], temp_list0[1], temp_list0[2])
        l0.EndPoint = (temp_list0_i[0], temp_list0_i[1], temp_list0_i[2])
        
        l1.StartPoint = (temp_list1[0], temp_list1[1], temp_list1[2])
        l1.EndPoint = (temp_list1_i[0], temp_list1_i[1], temp_list1_i[2])
        
        s0 = l0.toShape()
        s1 = l1.toShape()
 
        f = Part.makeLoft([s0, s1])
        comp.append(f)

    return Part.makeCompound(comp)

def pointFromPath(vector, raw_path):
    # returns the position of vector in raw_path list
    for side in raw_path:
        for i in range(len(side)):
            v = side[i]
            Fv = FreeCAD.Vector(v[0], v[1], v[2])
            if (Fv - vector).Length < 0.001:
                return i

def writeGCodeFile(wirepath, directory, G93):
    HWS_Machine = FreeCAD.ActiveDocument.HWS_Machine
    tr_A = []
    tr_B = []

    """
    This functions creates a file containing the G-Code instructions that can be
    read by GRBL.
    wirepath[0],wirepath[1] > trajectory points
    wirepath[2] -> wire speed and temperature
    directory = '/home/user/whatever...''
    
    """
    if G93:
        GCode_init = 'G21\nG17\nG90\nG93\n'
        #Gcode_final = 'M5\nG94'
    else:
        GCode_init = 'G21\nG17\nG90\nG94\n'
        #Gcode_final = 'M5'

    Gcode_final = 'M5\nG94'
    
    zeroPoint = FreeCAD.ActiveDocument.HWS_Machine.VirtualMachineZero
    ins = GCode_init
    f = ''
    f_G93 = ''
    axis_name = ['X','Y','A','Z'] #Make axis name changable from freecad

    #get selected foam type 
    heat, speed  = HWS_Foam.getFoamProperties(FreeCAD.ActiveDocument.WirePath)

    for i in range(len(wirepath[0])):

        #heat = 500 #heat = wirepath[2][i][2] * 10

        #speed = 4 #wirepath[2][i][1]

        #translate path to steppermotor positions
        tr_A, tr_B = HWS_SM.projectEdgeToTrajectory(wirepath[0][i],wirepath[1][i],0,HWS_Machine.ZLength)
        
        if tr_A[0] < 0:
            print("Waring "+axis_name[0]+" is out of range", tr_A[0])
        if tr_A[1] < 0:
            print("Waring "+axis_name[1]+" is out of range", tr_A[1])
        if tr_B[0] < 0:
            print("Waring "+axis_name[2]+" is out of range", tr_B[0])
        if tr_B[1] < 0:
            print("Waring "+axis_name[3]+" is out of range", tr_B[1])

        if tr_A[0] > HWS_Machine.XLength:
            print("Waring "+axis_name[0]+" is out of range", tr_A[0])
        if tr_A[1] > HWS_Machine.YLength:
            print("Waring "+axis_name[1]+" is out of range", tr_A[1])
        if tr_B[0] > HWS_Machine.XLength:
            print("Waring "+axis_name[2]+" is out of range", tr_B[0])
        if tr_B[1] > HWS_Machine.YLength:
            print("Waring "+axis_name[3]+" is out of range", tr_B[1])

        if not(G93) and wirepath[2][i][3] != wirepath[2][i - 1][3] and i > 0:
            h = 'M3 S' + str(heat) + '\n'
            f = 'G1 F '+str(speed) + '\n'
        elif not(G93) and i < 1:
            h = 'M3 S' + str(heat) + '\n'
            f = 'G1 F '+str(speed) + '\n'
        elif G93:
            dA = 0
            dB = 0
            vA1 = 0
            vA2 = 0
            vB1 = 0
            vB2 = 0
            i_next = i - 1

            if i_next < len(wirepath[0]) and i > 0:
                vA1 = FreeCAD.Vector(wirepath[0][i_next][0], wirepath[0][i_next][1], wirepath[0][i_next][2])
                vA2 = FreeCAD.Vector(wirepath[0][i][0], wirepath[0][i][1], wirepath[0][i_next][2])
                dA = vA1.distanceToPoint(vA2)

                vB1 = FreeCAD.Vector(wirepath[1][i_next][0], wirepath[1][i_next][1], wirepath[1][i_next][2])
                vB2 = FreeCAD.Vector(wirepath[1][i][0], wirepath[1][i][1], wirepath[1][i_next][2])
                dB = vB1.distanceToPoint(vB2)

            elif i == 0:
                vA1 = FreeCAD.Vector(zeroPoint.x, zeroPoint.y, wirepath[0][i][2])
                vA2 = FreeCAD.Vector(wirepath[0][i][0], wirepath[0][i][1], wirepath[0][i][2])
                dA = vA1.distanceToPoint(vA2)

                vB1 = FreeCAD.Vector(zeroPoint.x, zeroPoint.y, wirepath[1][i][2])
                vB2 = FreeCAD.Vector(wirepath[1][i][0], wirepath[1][i][1], wirepath[1][i][2])
                dB = vB1.distanceToPoint(vB2)
           
            profileALength = float(FreeCAD.ActiveDocument.getObject(wirepath[2][i][3]).PathALength)
            profileBLength = float(FreeCAD.ActiveDocument.getObject(wirepath[2][i][3]).PathBLength)
            
            #print(dA, dB)
            #print(speed)

            if profileALength >= profileBLength:
                f_G93 = ' F '+str(1 / ((dA / speed) / 60))
            else:
                f_G93 = ' F '+str(1 / ((dB / speed) / 60))
            
            if i_next < len(wirepath[0]) and i > 0:
                if wirepath[2][i][2] == wirepath[2][i_next][2]:
                    h = ''
                else:
                    h = 'M3 S' + str(heat) + '\n'
            else:
                h = 'M3 S' + str(heat) + '\n'

        else:
            h = ''
            f = ''
            f_G93 = ''

        AX = axis_name[0]+' '+str(round(tr_A.x, 6)) + ' '
        AY = axis_name[1]+' '+str(round(tr_A.y, 6)) + ' '
        BX = axis_name[2]+' '+str(round(tr_B.x, 6)) + ' '
        BY = axis_name[3]+' '+str(round(tr_B.y, 6))
        
        ins += h + f + 'G1 ' + AX + AY + BX + BY + f_G93 + '\n'
    
    ins += Gcode_final
    gcode_file = open(directory, 'w')    
    gcode_file.write(ins)
    gcode_file.close()

    #FreeCAD.Console.PrintMessage('G-Code generated succesfully\n')


def saveGCodeFile():
    #print("Write Gcode")
    HWS_Mch = FreeCAD.ActiveDocument.HWS_Machine
    G93 = HWS_Mch.G93
    #if false use G94
    
    #print(FreeCAD.ConfigGet('UserHomePath'))
    
    #save_directory = [FreeCAD.ConfigGet('UserHomePath')+"/Skrivbord/testG93", ".nc"]
    if HWS_Mch.SaveFilePath != '':
        directory = HWS_Mch.SaveFilePath
    else:
        directory = FreeCAD.ConfigGet("UserHomePath") #directory = FreeCAD.ConfigGet("UserAppData")
        HWS_Mch.SaveFilePath = FreeCAD.ConfigGet("UserHomePath") #directory = FreeCAD.ConfigGet("UserAppData")
    
    FCW = FreeCADGui.getMainWindow()
  
    save_directory = QtGui.QFileDialog.getSaveFileName(FCW,
                                                    'Save G-Code as:',
                                                    directory,
                                                    'All files  (*.*);;GCode files (*.nc)')
        
    full_path = traceObjectsAndLinksForRawPath(G93)

    writeGCodeFile(full_path, str(save_directory[0]), G93)
    FreeCAD.Console.PrintMessage('G-Code code saved to: ' + str(save_directory[0]) + '\n')


def importNiCrFile():
    FCW = FreeCADGui.getMainWindow()
    file_dir = QtGui.QFileDialog.getOpenFileName(FCW,
                                                 'Load .nicr file:',
                                                 '/home')
    readNiCrFile(file_dir[0])
    FreeCAD.Console.PrintMessage('Path succesfully imported\n')


def readNiCrFile(file_dir):
    nicr_file = open(file_dir, 'r')
    path_A = []
    path_B = []
    zlength = 0
    for line in nicr_file:
        line = line.split(' ')
        if line[0] == 'Z':
            zlength = float(line[3])

        if zlength != 0 and line[0] == 'MOVE':
            path_A.append((float(line[1]), float(line[2]), 0))
            path_B.append((float(line[3]), float(line[4]), zlength))

    complete_path = (path_A, path_B)
    obj = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Imported')
    obj.Shape = PathToShape(complete_path)
    

