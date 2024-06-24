# -*- coding: utf-8 -*-
# HWS (Hot Wire Slicer) workbench for FreeCAD
# https://github.com/PeAChristen/HotWireSlicer
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

import os
import FreeCAD
import FreeCADGui
import Part
import HWS_SimMachine as HWS_SM
import HWS_Path
import json

#todo find and use a pyside converter for qtdesign .ui file

from PySide import QtCore, QtGui, QtWidgets
import initTableSettingDialog as cfg_Dialog
import selectFoam as select_foam_Dialog
import Cut_GCode

__dir__ = os.path.dirname(__file__)

#TODO add align tools

def move_correct_obj(obj):
    str_pieces = obj.split("_")

    if "Link_" in obj or "InitialPath" in obj or "FinalPath" in obj:
        return False
    
    if not "ShapePath_" in obj:
        #print(FreeCAD.ActiveDocument.getObjectsByLabel(obj))
        return FreeCAD.ActiveDocument.getObjectsByLabel(obj)[0]


    if len(str_pieces) <= 1:
        for o in FreeCAD.ActiveDocument.Objects:
            if str_pieces[0] in o.Label:
                o.touch()  
        return FreeCAD.ActiveDocument.getObject(str_pieces[0])
    
    for o in FreeCAD.ActiveDocument.Objects:
        #print(str_pieces[0])
        #print(o.Label, o.InList)
        if str_pieces[1] in o.Label:
            o.touch()
            
    return FreeCAD.ActiveDocument.getObject(str_pieces[1])

    #print("can't locate correct object, try to create the wire path first")
    #return   
    
    """
    for obj in FreeCAD.ActiveDocument.Objects:
        obj.touch()
    FreeCAD.ActiveDocument.recompute()
    """

    """
    #How to add undo
    FreeCAD.ActiveDocument.openTransaction("My operation name")
    # do your undoable stuff here
    FreeCAD.ActiveDocument.commitTransaction()
    """

    """
    for i in App.ActiveDocument.Objects:
        print i.Label
        print i.InList  #if empty i is top object
        print i.OutList #if empty i is bottom object
    """
    

def adjusted_Global_Placement(obj, locVector):
    '''find global placement to make locVector the local origin with the correct orientation'''
    try:
        objectPlacement = obj.Shape.Placement
        objectGlobalPlacement = obj.getGlobalPlacement()
        locPlacement = FreeCAD.Placement(locVector, FreeCAD.Rotation(FreeCAD.Vector(0,0,-1),90))
        return objectGlobalPlacement.multiply(objectPlacement.inverse()).multiply(locPlacement)
    except Exception:
        locPlacement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,0,-1),90), FreeCAD.Vector(0,0,0))
        return locPlacement

class cutGCode():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/cutGCode.svg',
                'MenuText': 'Cutting block',
                'ToolTip': 'Generate gcode for cutting block'}
        
    def IsActive(self):
        try:
            self.a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        self.cut_Dialog = QtGui.QWidget()
        self.cut_ui = Cut_GCode.Ui_Dialog()
        self.cut_ui.setupUi(self.cut_Dialog)

        os =  FreeCAD.Gui.Selection.getSelectionEx()
        objs  = [selobj.Object for selobj in os]

        self.base = FreeCAD.ActiveDocument.Base
        
        self.bBox = None
        
        

        if len(objs) > 1:
            print("Select one or no objects")
            return
        elif len(objs) > 0:
            for obj in objs:
                
                correct_obj = move_correct_obj(obj.Label)
                if correct_obj != False:
                    obj = correct_obj
                    #print(correct_obj.Name)
                else:
                    return

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                else:
                    print("Can't recordnice selected object")
                    return

                self.bBox = s.BoundBox

                self.cut_ui.radioButton.toggled.connect(self.handleRadioButton_X)
                self.cut_ui.radioButton_Y.toggled.connect(self.handleRadioButton_Y)
                self.cut_ui.radioButton_Z.toggled.connect(self.handleRadioButton_Z)
                
        else:
            self.cut_ui.radioButton.setEnabled(False)
            self.cut_ui.radioButton_Y.setEnabled(False)
            self.cut_ui.radioButton_Z.setEnabled(False)
            
        table_from_machine = self.a.TableConfig 
        self.table_cfg = json.JSONDecoder().decode(table_from_machine[self.a.TableIndex])

        self.cut_cfg = json.JSONDecoder().decode(self.a.CutConfig[0])
        self.cut_ui.position.setText(str(self.cut_cfg[0]))
        self.cut_ui.block_height.setText(str(self.cut_cfg[1]))
        self.cut_ui.block_depth.setText(str(self.cut_cfg[2]))
        self.cut_ui.clearance.setText(str(self.cut_cfg[3]))

        self.cut_ui.cutAtBase.stateChanged.connect(self.use_base_end_to_cut)
        self.cut_ui.position.editingFinished.connect(self.update_cut_data)
        self.cut_ui.block_height.editingFinished.connect(self.update_cut_data)
        self.cut_ui.block_depth.editingFinished.connect(self.update_cut_data)
        self.cut_ui.clearance.editingFinished.connect(self.update_cut_data)

        def handleButtonClick(button):
            role = self.cut_ui.buttonBox.buttonRole(button)
            if str(role) == "PySide2.QtWidgets.QDialogButtonBox.ButtonRole.RejectRole":
                self.cut_Dialog.close()
            elif str(role)== "PySide2.QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole":
                self.saveCutGCode()
                self.cut_Dialog.close()

        self.cut_ui.buttonBox.clicked.connect(handleButtonClick)
        self.cut_Dialog.show()
    
    def handleRadioButton_X(self,selected):
        if selected:
            #print('X')
            table_from_machine = self.a.TableConfig 
            #table_cfg = json.JSONDecoder().decode(table_from_machine[self.a.TableIndex])
            self.cut_ui.block_depth.setText(str(round(self.bBox.XMax - self.bBox.XMin + (self.table_cfg[11]*2) ,2)))
    def handleRadioButton_Y(self,selected):
        if selected:
            #print('Y')
            table_from_machine = self.a.TableConfig 
            #table_cfg = json.JSONDecoder().decode(table_from_machine[self.a.TableIndex])
            self.cut_ui.block_depth.setText(str(round(self.bBox.YMax - self.bBox.YMin + (self.table_cfg[6]*2) ,2)))
    def handleRadioButton_Z(self,selected):
        if selected:
            #print('Z')
            #table_from_machine = self.a.TableConfig 
            #table_cfg = json.JSONDecoder().decode(table_from_machine[self.a.TableIndex])
            self.cut_ui.block_depth.setText(str(round(self.bBox.ZMax - self.bBox.ZMin,2)))

    def use_base_end_to_cut(self):
        if self.cut_ui.cutAtBase.isChecked():
            self.cut_ui.position.setEnabled(False)
            base_x = self.base.Shape.BoundBox.XMax - self.base.Shape.BoundBox.XMin + self.table_cfg[10]
            self.cut_ui.position.setText(str(base_x))
        else:
            self.cut_ui.position.setEnabled(True)
            self.cut_ui.position.setText(str(self.cut_cfg[0]))

    def update_cut_data(self):
        
        data = [float(self.cut_ui.position.text()), 
                float(self.cut_ui.block_height.text()), 
                float(self.cut_ui.block_depth.text()), 
                float(self.cut_ui.clearance.text())]
        
        tmp_json_data = []
        tmp_json_data.append(json.JSONEncoder().encode(data))
        self.a.CutConfig = tmp_json_data

    def saveCutGCode(self):
        
        wP = FreeCAD.ActiveDocument.WirePath
        foam_from_machine = self.a.FoamConfig        
        foam_cfg = json.JSONDecoder().decode(foam_from_machine[wP.FoamIndex])
        table_from_machine = self.a.TableConfig 
        table_cfg = json.JSONDecoder().decode(table_from_machine[self.a.TableIndex])
        kerf = foam_cfg[1]
        heat = foam_cfg[4] * 10
        data = [float(self.cut_ui.position.text()), 
                float(self.cut_ui.block_height.text()), 
                float(self.cut_ui.block_depth.text()), 
                float(self.cut_ui.clearance.text())]
        
        cut_distans = data[1]+(data[3]*2)
        cut_speed = foam_cfg[2]
        time_sec = cut_distans / cut_speed
        time_min = time_sec / 60
        time_g93 = 1 / time_min
        f = str(time_g93)
        
        lines = 'G21'
        lines += '\nG17'
        lines += '\nG91'
        lines += '\nG93'
        #move y to tabel top (30)
        lines += '\nG0 X0 Y'+str(table_cfg[8]+data[3])+' A0 Z'+str(table_cfg[8]+data[3]) 
        #move x to posistion+depth 
        lines += '\nG0 X'+str(data[0] + data[2])+' Y0 A'+str(data[0] + data[2])+' Z0'
        lines += '\nM0 (Place block against wire)'
        #move x clearance
        lines += '\nG0 X'+str(data[3])+' Y0 A'+str(data[3])+' Z0'
        #move y block height (130)
        lines += '\nG0 X0 Y'+str(data[1])+' A0 Z'+str(data[1])
        #move x back block depth + 1/2 kerf
        lines += '\nG0 X-'+str(data[2]+(kerf/2))+' Y0 A-'+str(data[2]+(kerf/2))+' Z0'
        lines += '\nM3 S'+str(heat)
        #move y down block height + clearance * 2 (10)
        lines += '\nG1 X0 Y-'+str(cut_distans)+' A0 Z-'+str(cut_distans)+' F'+f
        lines += '\nM5'
        lines += '\nM0 (Remove block)'
        #move y clearans * 2 (30)
        lines += '\nG0 X0 Y'+str(data[3]*2)+' A0 Z'+str(data[3]*2)        
        #move x back to 0
        lines += '\nG0 X-'+str(data[0]-(kerf/2)+data[3])+' Y0 A-'+str(data[0]-(kerf/2)+data[3])+' Z0'
        lines += '\nG90'
        #move to 0
        lines += '\nG0 X0 Y0 A0 Z0'
        lines += '\nG94'
        
        if self.a.SaveFilePath != '':
            directory = self.a.SaveFilePath
        else:
            directory = FreeCAD.ConfigGet("UserHomePath")
            self.a.SaveFilePath = directory
            
        FCW = FreeCADGui.getMainWindow()
        save_directory = QtGui.QFileDialog.getSaveFileName(FCW,
                                                        'Save G-Code as:',
                                                        directory,
                                                        'All files  (*.*);;GCode files (*.nc)')
        gcode_file = open(save_directory[0], 'w')    
        gcode_file.write(lines)
        gcode_file.close()
        
        #print(lines)
        FreeCAD.Console.PrintMessage('Cut file saved')

        #print('save to file')


class DistAlongY():
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/DistAlongY.svg',
                'MenuText': 'Distribute objects along Y',
                'ToolTip': 'Distribute objects along Y according to margins in config'}
    
        
    def IsActive(self):
        try:
            self.m = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        table = self.m.TableConfig[self.m.TableIndex]
        current_table_cfg = json.JSONDecoder().decode(table)
        Y_margin = current_table_cfg[6] # margin in mm from first selection (from base, if obj on base) up next to object, no kerf added to margin
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 1:
            print("Select one or more objects to arange them along Y according to margins in config")
            return
        
        
        FreeCAD.ActiveDocument.openTransaction("Distribute objects along Y")
        prev_obj_top = 0
        
        for i, obj in enumerate(objs):
            
            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
                #print(correct_obj.Name)
            else:
                return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return

            bBox = s.BoundBox
            
            if i == 0:

                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                obj.Placement.Base.y = null_placement.Base.y

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                
                bBox = s.BoundBox
                base_top = base.Shape.BoundBox.YMax

                new_y = bBox.YMin * -1 + base_top + Y_margin
                
                obj.Placement.Base.y = new_y

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                
                bBox = s.BoundBox
                prev_obj_top = bBox.YMax
                    
                #print('shape ',bBox.YMin,' == base ',base.Shape.BoundBox.YMax)
                #base_top = base.Shape.BoundBox.YMax
                #new_y = bBox.YMin * -1 + base_top
                #obj.Placement.Base.y = new_y + Y_margin
                
                """
                if round(bBox.YMin, 6) == base.Shape.BoundBox.YMax:
                    obj.Placement.Base.y += Y_margin
                        
                    if hasattr(obj, "Shape"):
                        s = obj.Shape
                    elif hasattr(obj, "Mesh"):
                        s = obj.Mesh 
                    elif hasattr(obj, "Points"):
                        s = obj.Points
                    
                    bBox = s.BoundBox
                    prev_obj_top = bBox.YMax
                """


            
            if i > 0:    
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                obj.Placement.Base.y = null_placement.Base.y

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                bBox = s.BoundBox
                new_y = (bBox.YMin * -1) + prev_obj_top + (Y_margin * 2)
 
                obj.Placement.Base.y = new_y

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                bBox = s.BoundBox
                
                prev_obj_top = bBox.YMax

            else:
                prev_obj_top = bBox.YMax
        print("Distribute objects along Y")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

class DistAlongX():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/DistAlongX.svg',
                'MenuText': 'Distribute objects along X',
                'ToolTip': 'Distribute objects along X according to margins in config'}
        
    def IsActive(self):
        try:
            self.m = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        table = self.m.TableConfig[self.m.TableIndex]
        current_table_cfg = json.JSONDecoder().decode(table)
        X_margin = current_table_cfg[11] # margin in mm from first selection (from base, if obj on base) up next to object, no kerf added to margin
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 1:
            print("Select one or more objects to arange them along X according to margins in config")
            return
        
        
        FreeCAD.ActiveDocument.openTransaction("Distribute objects along X")
        prev_obj_top = 0
        
        for i, obj in enumerate(objs):
            
            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
                #print(correct_obj.Name)
            else:
                return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return

            bBox = s.BoundBox
            
            if i == 0:
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                obj.Placement.Base.x = null_placement.Base.x

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                
                bBox = s.BoundBox
                base_front = base.Shape.BoundBox.XMin

                new_x = bBox.XMin * -1 + base_front + X_margin
                
                obj.Placement.Base.x = new_x

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                
                bBox = s.BoundBox
                prev_obj_top = bBox.XMax
                """
                if round(bBox.XMin, 6) == base.Shape.BoundBox.XMin:
                    obj.Placement.Base.x += X_margin
                        
                    if hasattr(obj, "Shape"):
                        s = obj.Shape
                    elif hasattr(obj, "Mesh"):
                        s = obj.Mesh 
                    elif hasattr(obj, "Points"):
                        s = obj.Points
                    
                    bBox = s.BoundBox
                    prev_obj_top = bBox.XMax
                """
            if i > 0:    
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                obj.Placement.Base.x = null_placement.Base.x

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                bBox = s.BoundBox
                new_x = (bBox.XMin * -1) + prev_obj_top + (X_margin * 2)
 
                obj.Placement.Base.x = new_x

                if hasattr(obj, "Shape"):
                    s = obj.Shape
                elif hasattr(obj, "Mesh"):
                    s = obj.Mesh 
                elif hasattr(obj, "Points"):
                    s = obj.Points
                bBox = s.BoundBox
                
                prev_obj_top = bBox.XMax

            else:
                prev_obj_top = bBox.XMax
        print("Distribute objects along X")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()



class AlignToBaseBack():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToBaseBack.svg',
                'MenuText': 'Align objects to base back',
                'ToolTip': 'Move selected objects to base back'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        #if len(objs) < 1:
        #    print("Select one or more objects to move on to base top")
        #    return
        
        
        FreeCAD.ActiveDocument.openTransaction("Align object to base back")
        for obj in objs:

            correct_obj = move_correct_obj(obj.Label)
            #print(correct_obj)
            if correct_obj != False:
                obj = correct_obj
                #print(correct_obj.Name)
            else:
                return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.x = null_placement.Base.x

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            base_back = base.Shape.BoundBox.XMax
            #print(base_front)
            #print(bBox.XMin)
            new_x = bBox.XMax * -1 + base_back
            
            obj.Placement.Base.x = new_x
        print("Align object to base back")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

            
class AlignToBaseZMin():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToBaseZMin.svg',
                'MenuText': 'Align objects to left on base',
                'ToolTip': 'Move selected objects to left on base'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        #if len(objs) < 1:
        #    print("Select one or more objects to move on to base top")
        #    return
        
        
        FreeCAD.ActiveDocument.openTransaction("Align object to left on base")
        for obj in objs:

            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
                #print(correct_obj.Name)
            else:
                return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.z = null_placement.Base.z

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            base_left = base.Shape.BoundBox.ZMin
            #print(base_front)
            #print(bBox.XMin)
            new_z = bBox.ZMin * -1 + base_left
            
            obj.Placement.Base.z = new_z
        print("Align object to left on base")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()


class AlignToBaseZMax():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToBaseZMax.svg',
                'MenuText': 'Align objects to right on base',
                'ToolTip': 'Move selected objects to right on base'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        #if len(objs) < 1:
        #    print("Select one or more objects to move on to base top")
        #    return
        
        
        FreeCAD.ActiveDocument.openTransaction("Align object to right on base")
        for obj in objs:

            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
                #print(correct_obj.Name)
            else:
                return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.z = null_placement.Base.z

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            base_right = base.Shape.BoundBox.ZMax
            #print(base_front)
            #print(bBox.XMin)
            new_z = bBox.ZMax * -1 + base_right
            
            obj.Placement.Base.z = new_z
        print("Align object to right on base")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

class AlignToBaseFront():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToBaseFront.svg',
                'MenuText': 'Align objects to base front',
                'ToolTip': 'Move selected objects to base front'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()
        
        objs  = [selobj.Object for selobj in os]
        #if len(objs) < 1:
        #    print("Select one or more objects to move on to base top")
        #    return
        
        #print(objs[0].Name)
        
        FreeCAD.ActiveDocument.openTransaction("Align object to base front")
        for obj in objs:

            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
            else:
                return
            
            #print(obj.Name)

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.x = null_placement.Base.x

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            base_front = base.Shape.BoundBox.XMin
            #print(base_front)
            #print(bBox.XMin)
            new_x = bBox.XMin * -1 + base_front
            
            obj.Placement.Base.x = new_x
        print("Align object to base front")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

class AlignToBase():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToBase.svg',
                'MenuText': 'Align objects on to base top',
                'ToolTip': 'Move selected objects on to base top'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        base = FreeCAD.ActiveDocument.Base
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        #if len(objs) < 1:
        #    print("Select one or more objects to move on to base top")
        #    return
        
        
        FreeCAD.ActiveDocument.openTransaction("Align object on to base top")
        for obj in objs:

            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
            else:
                return #if correct obj not found return

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.y = null_placement.Base.y

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            base_top = base.Shape.BoundBox.YMax

            new_y = bBox.YMin * -1 + base_top
            
            obj.Placement.Base.y = new_y
        print("Align object on to base top")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()        

class AlignToCenterZ():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToCenter.svg',
                'MenuText': 'Align to table center',
                'ToolTip': 'Move selected objects to center of table along Z axis'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True
        except:
            return False
        
    def Activated(self):
        
        m = FreeCAD.ActiveDocument.HWS_Machine
        
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 1:
            print("Select one or more objects to center")
            return
        
        
        FreeCAD.ActiveDocument.openTransaction("Align object to machine center")
        for obj in objs:
            #print(obj.Label)
            correct_obj = move_correct_obj(obj.Label)
            if correct_obj != False:
                obj = correct_obj
            else:
                return #if correct obj not found return
            #print(obj.Label)

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            else:
                print("Can't recordnice selected object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            obj.Placement.Base.z = null_placement.Base.z

            if hasattr(obj, "Shape"):
                s = obj.Shape
            elif hasattr(obj, "Mesh"):
                s = obj.Mesh 
            elif hasattr(obj, "Points"):
                s = obj.Points
            
            bBox = s.BoundBox
            m_z_center = m.ZLength / 2
            new_z = (m_z_center - (bBox.ZLength / 2)) - bBox.ZMin
            
            obj.Placement.Base.z = new_z
        print("Align object to machine center")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

        

class AlignToObjCenterZ():    
    def __init__(self):
        pass
    
    def GetResources(self):
        pass
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        pass
        
class AlignToObjCenterX():    
    def __init__(self):
        pass
    
    def GetResources(self):
        pass
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        pass

class AlignToObjCenterY():    
    def __init__(self):
        pass
    
    def GetResources(self):
        pass
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        pass

class AlignToObjZMin():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToObjZMin.svg',
                'MenuText': 'Align to onject z min',
                'ToolTip': 'Move selected objects to z min of first selection'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):   
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 2:
            print("Select two or more objects to align")
            return
              
        z_dest = 0
        FreeCAD.ActiveDocument.openTransaction("Align object to object z min (left)")
        for i in range(0,len(objs)):

            correct_obj = move_correct_obj(objs[i].Label)
            if correct_obj != False:
                objs[i] = correct_obj
            else:
                return #if correct obj not found return

            if hasattr(objs[i], "Shape"):
                s = objs[i].Shape
            elif hasattr(objs[i], "Mesh"):
                s = objs[i].Mesh 
            elif hasattr(objs[i], "Points"):
                s = objs[i].Points
            else:
                print("Can't recordnice selected object")
                return
            
            #find z destination
            if i == 0:
                z_dest = s.BoundBox.ZMin
            elif i > 0:
                #applay z destination
                bBox = s.BoundBox
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                objs[i].Placement.Base.z = null_placement.Base.z

                if hasattr(objs[i], "Shape"):
                    s = objs[i].Shape
                elif hasattr(objs[i], "Mesh"):
                    s = objs[i].Mesh 
                elif hasattr(objs[i], "Points"):
                    s = objs[i].Points               
                
                bBox = s.BoundBox
                z_obj = bBox.ZMin
                new_z = z_dest - z_obj

                objs[i].Placement.Base.z = new_z
        print("Align object to object z min (left)")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()


class AlignToObjZMax():    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToObjZMax.svg',
                'MenuText': 'Align to onject z max',
                'ToolTip': 'Move selected objects to z max of first selection'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 2:
            print("Select two or more objects to align")
            return
        
        
        z_dest = 0
        FreeCAD.ActiveDocument.openTransaction("Align object to object z max (right)")
        for i in range(0,len(objs)):

            correct_obj = move_correct_obj(objs[i].Label)
            if correct_obj != False:
                objs[i] = correct_obj
            else:
                return #if correct obj not found return

            if hasattr(objs[i], "Shape"):
                s = objs[i].Shape
            elif hasattr(objs[i], "Mesh"):
                s = objs[i].Mesh 
            elif hasattr(objs[i], "Points"):
                s = objs[i].Points
            else:
                print("Can't recordnice selected object")
                return
            
            #find z destination
            if i == 0:
                z_dest = s.BoundBox.ZMax
            elif i > 0:
                #applay z destination
                bBox = s.BoundBox
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                objs[i].Placement.Base.z = null_placement.Base.z

                if hasattr(objs[i], "Shape"):
                    s = objs[i].Shape
                elif hasattr(objs[i], "Mesh"):
                    s = objs[i].Mesh 
                elif hasattr(objs[i], "Points"):
                    s = objs[i].Points               
                
                bBox = s.BoundBox
                z_obj_l = bBox.ZLength
                z_obj_m = bBox.ZMin
                new_z = z_dest - z_obj_l - z_obj_m 

                objs[i].Placement.Base.z = new_z
        print("Align object to object z max (right)")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

    
class AlignToObjXmin():
    def __init__(self):
        pass
    
    def GetResources(self):
        pass
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        pass

class AlignToObjXmax():
    def __init__(self):
        pass
    
    def GetResources(self):
        pass
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        pass
    
class AlignToObjYMin():
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToObjYMin.svg',
                'MenuText': 'Align to onject y min',
                'ToolTip': 'Move selected objects to y min of first selection'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 2:
            print("Select two or more objects to align")
            return
        

        
        y_dest = 0
        FreeCAD.ActiveDocument.openTransaction("Align object to object y min (down)")
        for i in range(0,len(objs)):

            correct_obj = move_correct_obj(objs[i].Label)
            if correct_obj != False:
                objs[i] = correct_obj
            else:
                return #if correct obj not found return


            if hasattr(objs[i], "Shape"):
                s = objs[i].Shape
            elif hasattr(objs[i], "Mesh"):
                s = objs[i].Mesh 
            elif hasattr(objs[i], "Points"):
                s = objs[i].Points
            else:
                print("Can't recordnice selected object")
                return
            
            #find z destination
            if i == 0:
                y_dest = s.BoundBox.YMin
            elif i > 0:
                #applay z destination
                bBox = s.BoundBox
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                objs[i].Placement.Base.y = null_placement.Base.y

                if hasattr(objs[i], "Shape"):
                    s = objs[i].Shape
                elif hasattr(objs[i], "Mesh"):
                    s = objs[i].Mesh 
                elif hasattr(objs[i], "Points"):
                    s = objs[i].Points               
                
                bBox = s.BoundBox
                #z_obj_l = bBox.ZLength
                y_obj_m = bBox.YMin
                new_y = y_dest - y_obj_m 

                objs[i].Placement.Base.y = new_y
        print("Align object to object y min (down)")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()


class AlignToObjYMax():
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AlignToObjYMax.svg',
                'MenuText': 'Align to onject y max',
                'ToolTip': 'Move selected objects to y max of first selection'}
        
    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
    
    def Activated(self):
        os =  FreeCAD.Gui.Selection.getSelectionEx()

        objs  = [selobj.Object for selobj in os]
        if len(objs) < 2:
            print("Select two or more objects to align")
            return
        

        
        y_dest = 0
        FreeCAD.ActiveDocument.openTransaction("Align object to object y max (up)")
        for i in range(0,len(objs)):

            correct_obj = move_correct_obj(objs[i].Label)
            if correct_obj != False:
                objs[i] = correct_obj
            else:
                return #if correct obj not found return

            if hasattr(objs[i], "Shape"):
                s = objs[i].Shape
            elif hasattr(objs[i], "Mesh"):
                s = objs[i].Mesh 
            elif hasattr(objs[i], "Points"):
                s = objs[i].Points
            else:
                print("Can't recordnice selected object")
                return
            
            #find z destination
            if i == 0:
                y_dest = s.BoundBox.YMax
            elif i > 0:
                #applay z destination
                bBox = s.BoundBox
                boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
                null_placement = adjusted_Global_Placement(s, boundBoxVector)
                objs[i].Placement.Base.y = null_placement.Base.y

                if hasattr(objs[i], "Shape"):
                    s = objs[i].Shape
                elif hasattr(objs[i], "Mesh"):
                    s = objs[i].Mesh 
                elif hasattr(objs[i], "Points"):
                    s = objs[i].Points               
                
                bBox = s.BoundBox
                z_obj_l = bBox.YLength
                y_obj_m = bBox.YMin
                new_y = y_dest - y_obj_m - z_obj_l

                objs[i].Placement.Base.y = new_y
        print("Align object to object y max (up)")
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.ActiveDocument.commitTransaction()

class ClearWireTraces:
    
    def __init__(self):
        pass
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/ClearWireTraces.svg',
                'MenuText': 'Clear wire trace',
                'ToolTip': 'Removes wire traces from simulation'}
    
    def IsActive(self):
        try:
            a  = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False
        
    def Activated(self):
        HWS_SM.clearWireTrack()
        print("Wire traces removed")

def open_chose_foam_dialog(s, o):
    s.foam_Dialog = QtGui.QWidget()
    s.foam_ui = select_foam_Dialog.Ui_Dialog()
    s.foam_ui.setupUi(s.foam_Dialog)

    for fm in s.foam_cfg:
        s.foam_ui.Foam.addItem(fm[0])
    s.foam_ui.Foam.setCurrentIndex(o.FoamIndex)

    def handleButtonClick(button):
        role = s.foam_ui.buttonBox.buttonRole(button)
        if str(role) == "PySide2.QtWidgets.QDialogButtonBox.ButtonRole.RejectRole":
            s.foam_Dialog.close()

    def foam_activated(index):
        o.FoamIndex = s.foam_ui.Foam.currentIndex()

    s.foam_ui.buttonBox.clicked.connect(handleButtonClick)
    s.foam_ui.Foam.activated.connect(foam_activated)
    
    s.foam_Dialog.show()

class ConfigureTableNFoam:
    #TODO Add Foam cut speed properties
    def __init__(self):
        
        pass
        
        

       


    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/ConfigureTableNFoam.svg',
                'MenuText': 'Configure table and foam',
                'ToolTip': 'Set table specs and foam settings\nIf outer shape is selected foam can be chosen'}
    
    def IsActive(self):
        try:
            self.m = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            self.m = None
            return False
        
    def Activated(self):
        # todo
        #if not part selected open machine config dialog DONE
        #if part selected open part config dialog DONE
        #if innner part selected select outer and open part config dialog DONE
        
        #TODO if no HWS.cfg file, creat new
        #TODO load HWS.cfg into machine when loading ui for cfg of table and foam
        #TODO alwase update HWS.cfg file when cfg of table and foam changes
        
        dir_sep = os.sep
        
        if self.m.PathToHWS_cfg != '':
            self.cfg_file_dir = self.m.PathToHWS_cfg+'HWS.cfg'
        else:
            #linux -> 
            self.cfg_file_dir = FreeCAD.getUserAppDataDir()+'Mod'+dir_sep+'HotWireSlicer'+dir_sep+'HWS.cfg'
            self.m.PathToHWS_cfg =FreeCAD.getUserAppDataDir()+'Mod'+dir_sep+'HotWireSlicer'+dir_sep
            #windows -> 
            #self.cfg_file_dir = FreeCAD.getHomePath()+'Mod'+dir_sep+'HotWireSlicer'+dir_sep+'HWS.cfg'
            #self.m.PathToHWS_cfg = FreeCAD.getHomePath()+'Mod'+dir_sep+'HotWireSlicer'+dir_sep
            
        

        #print(FreeCAD.getHomePath())
        #print(FreeCAD.getHomePath()+'Mod'+dir_sep+'HotWireSlicer'+dir_sep+'HWS.cfg')    

                
        #HWS_SM.default_table_cfg = data[0]
        #self.table_and_foam_config = data
        

        self.sel = FreeCAD.Gui.Selection.getSelectionEx()
        
        if len(self.sel) > 0:
            for s in self.sel:
                o = s.Object
                if o.Label[:10] == "ShapePath_" and o.Label[10:] == o.ShapeName:
                    print("Select WirePath foam type")
                    wp = FreeCAD.ActiveDocument.WirePath
                    open_chose_foam_dialog(self, wp)
                    return
        
        self.Dialog = QtGui.QWidget()
        self.ui = cfg_Dialog.Ui_Dialog()
        self.ui.setupUi(self.Dialog)

        self.table_cfg = [] #self.table_and_foam_config[0]
        for t_cfg in self.m.TableConfig:
            self.table_cfg.append(json.JSONDecoder().decode(t_cfg))

        self.foam_cfg = [] #self.table_and_foam_config[1]
        for f_cfg in self.m.FoamConfig:
            self.foam_cfg.append(json.JSONDecoder().decode(f_cfg))


        if os.path.isfile(self.cfg_file_dir):
            HWS_file = open(self.cfg_file_dir, 'r')
            data = []
            for line in HWS_file:
                data = json.JSONDecoder().decode(line)
            HWS_file.close()
            #print(data[0])
            #print(self.table_cfg)
            self.table_cfg = data[0] 
            #print(data[1])
            #print(self.foam_cfg)
            self.foam_cfg = data[1]
            #print("cfg file exist")
        else:
            #data = [[["Default", 738.0, 450.0, 450.0, 10.0, 50.0, 5.0, 200.0, 40.0, 200.0, 85.0, 5.0]], [["Default", 1.6, 4.0, 1.9, 75]]]
            cfg_data = json.JSONEncoder().encode([self.table_cfg] + [self.foam_cfg])
            cfg_file = open(self.cfg_file_dir, 'w')
            cfg_file.write(cfg_data)
            cfg_file.close()
            #print("no cfg file")

        self.update_cfg_dialog(self.m.TableIndex + 1, 1)

        """
        self.insertpolicy = QtWidgets.QComboBox()
        self.insertpolicy.addItems([
            'NoInsert',
            'InsertAtTop',
            'InsertAtCurrent',
            'InsertAtBottom',
            'InsertAfterCurrent',
            'InsertBeforeCUrrent',
            'InsertAlphabetically'
        ])
        """

        # The index in the insertpolicy combobox (0-6) is the correct flag value to set
        # to enable that insert policy.
        
        self.ui.Foam.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom )
        self.ui.Foam.setEditable(False)
        self.ui.Foam.activated.connect(self.foam_activated)
        self.ui.Foam.editTextChanged.connect(self.foam_change_text)

        self.ui.Root_Kerf.editingFinished.connect(self.update_foam_data)
        self.ui.Root_Speed.editingFinished.connect(self.update_foam_data)
        self.ui.Tip_Kerf.editingFinished.connect(self.update_foam_data)
        self.ui.Foam_Heat.editingFinished.connect(self.update_foam_data)

        self.ui.Table.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom)
        self.ui.Table.setEditable(False)
        self.ui.Table.activated.connect(self.table_activated)
        self.ui.Table.editTextChanged.connect(self.table_change_text)

        self.ui.Wire_Z.editingFinished.connect(self.update_table_data)
        self.ui.Table_XMax.editingFinished.connect(self.update_table_data)
        self.ui.Table_YMax.editingFinished.connect(self.update_table_data)
        self.ui.Speed_Max.editingFinished.connect(self.update_table_data)
        self.ui.Heat_Max.editingFinished.connect(self.update_table_data)
        self.ui.Y_margin.editingFinished.connect(self.update_table_data)
        self.ui.Base_X.editingFinished.connect(self.update_table_data)
        self.ui.Base_Y.editingFinished.connect(self.update_table_data)
        self.ui.Base_Z.editingFinished.connect(self.update_table_data)
        self.ui.Base_XOffset.editingFinished.connect(self.update_table_data)
        self.ui.X_margin.editingFinished.connect(self.update_table_data)

        self.ui.buttonBox.clicked.connect(self.handleButtonClick)

        self.Dialog.show()

        #print("Open cfg dialog")
    
    def update_cfg_dialog(self, t_index, f_index):
        self.ui.Foam.clear()
        self.ui.Foam.addItem("New")
        for fm in self.foam_cfg:
            self.ui.Foam.addItem(fm[0])
        self.ui.Foam.setCurrentIndex(f_index)

        self.ui.Root_Kerf.setText(str(float(self.foam_cfg[f_index - 1][1])))
        self.ui.Root_Speed.setText(str(self.foam_cfg[f_index - 1][2]))
        self.ui.Tip_Kerf.setText(str(self.foam_cfg[f_index - 1][3]))
        self.ui.Foam_Heat.setText(str(self.foam_cfg[f_index - 1][4]))
        
        self.ui.Table.clear()
        self.ui.Table.addItem("New")
        for tbl in self.table_cfg:
            self.ui.Table.addItem(tbl[0])
        self.ui.Table.setCurrentIndex(t_index)

        self.ui.Wire_Z.setText(str(self.table_cfg[t_index - 1][1]))
        self.ui.Table_XMax.setText(str(self.table_cfg[t_index - 1][2]))
        self.ui.Table_YMax.setText(str(self.table_cfg[t_index - 1][3]))
        self.ui.Speed_Max.setText(str(self.table_cfg[t_index - 1][4]))
        self.ui.Heat_Max.setText(str(self.table_cfg[t_index - 1][5]))
        self.ui.Y_margin.setText(str(self.table_cfg[t_index - 1][6]))
        self.ui.Base_X.setText(str(self.table_cfg[t_index - 1][7]))
        self.ui.Base_Y.setText(str(self.table_cfg[t_index - 1][8]))
        self.ui.Base_Z.setText(str(self.table_cfg[t_index - 1][9]))
        self.ui.Base_XOffset.setText(str(self.table_cfg[t_index - 1][10]))
        self.ui.X_margin.setText(str(self.table_cfg[t_index - 1][11]))

    def add_foam_data(self, foam_index, foam_name):
        self.foam_cfg.append([foam_name, 
                              float(self.ui.Root_Kerf.text()), 
                              float(self.ui.Root_Speed.text()), 
                              float(self.ui.Tip_Kerf.text()), 
                              float(self.ui.Foam_Heat.text())])
        
        self.replace_foam_cfg_in_machine(self.foam_cfg)

    def add_table_data(self, table_index, table_name):
        self.table_cfg.append([table_name,
                              float(self.ui.Wire_Z.text()),
                              float(self.ui.Table_XMax.text()),
                              float(self.ui.Table_YMax.text()),
                              float(self.ui.Speed_Max.text()),
                              float(self.ui.Heat_Max.text()),
                              float(self.ui.Y_margin.text()),
                              float(self.ui.Base_X.text()),
                              float(self.ui.Base_Y.text()),
                              float(self.ui.Base_Z.text()),
                              float(self.ui.Base_XOffset.text()),
                              float(self.ui.X_margin.text())])
        
        self.replace_table_cfg_in_machine(self.table_cfg)

    def update_foam_data(self):
        f_index = self.ui.Foam.currentIndex() - 1
        f_name = self.ui.Foam.currentText()

        self.foam_cfg[f_index] = [f_name, 
                              float(self.ui.Root_Kerf.text()), 
                              float(self.ui.Root_Speed.text()), 
                              float(self.ui.Tip_Kerf.text()), 
                              float(self.ui.Foam_Heat.text())]
        
        self.replace_foam_cfg_in_machine(self.foam_cfg)      
    
    def update_table_data(self):
        t_index = self.ui.Table.currentIndex() - 1
        t_name = self.ui.Table.currentText()

        self.table_cfg[t_index] = [t_name, 
                              float(self.ui.Wire_Z.text()), 
                              float(self.ui.Table_XMax.text()), 
                              float(self.ui.Table_YMax.text()), 
                              float(self.ui.Speed_Max.text()), 
                              float(self.ui.Heat_Max.text()), 
                              float(self.ui.Y_margin.text()), 
                              float(self.ui.Base_X.text()), 
                              float(self.ui.Base_Y.text()), 
                              float(self.ui.Base_Z.text()), 
                              float(self.ui.Base_XOffset.text()),
                              float(self.ui.X_margin.text())]
        
        self.replace_table_cfg_in_machine(self.table_cfg)

    def remove_foam_data(self, foam_index):
        U_I = self.ui

        new_foam_data = []

    def replace_foam_cfg_in_machine(self, data):
        
        tmp_json_data = []
        for fm in data:
            tmp_json_data.append(json.JSONEncoder().encode(fm))
        self.m.FoamConfig = tmp_json_data

        #update relevent data to freecad objects and recomputer
        #pass
    
    def replace_table_cfg_in_machine(self, data):
        
        tmp_json_data = []
        for fm in data:
            tmp_json_data.append(json.JSONEncoder().encode(fm))
        self.m.TableConfig = tmp_json_data
        
        #update relevent data to freecad objects
        #tabel
        i = self.m.TableIndex
        #current_table = json.JSONDecoder().decode(self.m.TableConfig[i])
        #print(data)
        

        self.m.ZLength = data[i][1]
        self.m.XLength = data[i][2]
        self.m.YLength = data[i][3]


        #wire
        Z0 = self.m.FrameDiameter*1.1*0
        ZL = self.m.ZLength
        Z1 = ZL + Z0 - self.m.FrameDiameter*0.2
        wire = FreeCAD.ActiveDocument.Wire
        wire.Shape = Part.makeLine((0,0,Z0), (0,0,Z1))
        
        #base #TODO Recenter after change
        b = FreeCAD.ActiveDocument.Base
        if(data[i][9] != b.Width):
            center_base_z = True
        else:
            center_base_z = False
        
        b.Length = data[i][7]
        b.Width = data[i][8]
        b.Height = data[i][9]
        b.Placement.Base.x = data[i][10]


       
        if(center_base_z):
            if hasattr(b, "Shape"):
                s = b.Shape
            elif hasattr(b, "Mesh"):
                s = b.Mesh 
            elif hasattr(b, "Points"):
                s = b.Points
            else:
                print("Can't recordnice base object")
                return
            
            bBox = s.BoundBox
            boundBoxVector = FreeCAD.Vector(bBox.XMin,bBox.YMin,bBox.ZMin)
            null_placement = adjusted_Global_Placement(s, boundBoxVector)
            b.Placement.Base.z = null_placement.Base.z

            if hasattr(b, "Shape"):
                s = b.Shape
            elif hasattr(b, "Mesh"):
                s = b.Mesh 
            elif hasattr(obj, "Points"):
                s = b.Points
            
            bBox = s.BoundBox
            m_z_center = self.m.ZLength / 2
            new_z = (m_z_center - (bBox.ZLength / 2)) - bBox.ZMin
            
            b.Placement.Base.z = new_z
        

    def save_HWS_cfg_to_file(self):
        #tmp_data = [self.table_cfg,self.foam_cfg]
        #tmp_json_data = []
        #for fm in tmp_data:
        #    tmp_json_data.append(json.JSONEncoder().encode(fm))
        #TODO only save uniqe configs with doc id

        FCW = FreeCADGui.getMainWindow()
        save_directory = QtGui.QFileDialog.getSaveFileName(FCW,
                                                           'Save config file as:',
                                                           '/home',
                                                           '.cfg')
        #print(save_directory)
        cfg_file = open(save_directory[0] + '.cfg', 'w')
        w = json.JSONEncoder().encode([self.table_cfg] + [self.foam_cfg])#)+"\n"+json.JSONEncoder().encode(self.foam_cfg)
        #print(w)
        cfg_file.write(w)
        cfg_file.close()
        print('Tabel and Foam config saved to: ' + save_directory[0] + '.cfg')

    #foam drop list handling
    def foam_clear_text(self, str):
        if self.ui.Foam.currentIndex() < 1:
            self.ui.Foam.clearEditText()

    def foam_change_text(self, str):
        if self.ui.Foam.currentIndex() > 0 and str != self.foam_cfg[self.ui.Foam.currentIndex() - 1][0]:
            #print(str," != ", self.foam_cfg[self.ui.Foam.currentIndex() - 1][0])
            self.ui.Foam.setItemText(self.ui.Foam.currentIndex(), str)
            self.update_foam_data()
            #print("update foam name: ", str)

    def foam_activated(self, index):
        if index < 1:
            self.ui.Foam.setEditable(True)
            self.ui.Foam.clearEditText()
            self.ui.Foam.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom)
        elif index == 1:
            self.ui.Foam.setEditable(False)
            self.ui.Foam.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
            if self.ui.Foam.count() > len(self.foam_cfg) + 1:
                self.add_foam_data(self.ui.Foam.currentIndex(), self.ui.Foam.currentText())
            #print("update foam : ", index)
            self.update_cfg_dialog(self.ui.Table.currentIndex(), index)
        else:
            self.ui.Foam.setEditable(True)
            self.ui.Foam.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
            if self.ui.Foam.count() > len(self.foam_cfg) + 1:
                self.add_foam_data(self.ui.Foam.currentIndex(), self.ui.Foam.currentText())
            #print("update foam : ", index)
            self.update_cfg_dialog(self.ui.Table.currentIndex(), index)

        

    #table drop list handling
    def table_clear_text(self, str):
        if self.ui.Table.currentIndex() < 1:
            self.ui.Table.clearEditText()

    def table_change_text(self, str):
        if self.ui.Table.currentIndex() > 0 and str != self.table_cfg[self.ui.Table.currentIndex() - 1][0]:
            self.ui.Table.setItemText(self.ui.Table.currentIndex(), str)
            self.update_table_data()
            #print("update table name: ", str)

    def table_activated(self, index):
        if index < 1:
            self.ui.Table.setEditable(True)
            self.ui.Table.clearEditText()
            self.ui.Table.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom)
        elif index == 1:
            self.ui.Table.setEditable(False)
            self.ui.Table.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
            if self.ui.Table.count() > len(self.table_cfg) + 1:
                self.add_table_data(self.ui.Table.currentIndex(), self.ui.Table.currentText())
            #print("update table : ", index)
            self.update_cfg_dialog(index, self.ui.Foam.currentIndex())
            self.m.TableIndex = self.ui.Table.currentIndex() - 1
        else:
            self.ui.Table.setEditable(True)
            self.ui.Table.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
            if self.ui.Table.count() > len(self.table_cfg) + 1:
                self.add_table_data(self.ui.Table.currentIndex(), self.ui.Table.currentText())
            #print("update table : ", index)
            self.update_cfg_dialog(index, self.ui.Foam.currentIndex())
            self.m.TableIndex = self.ui.Table.currentIndex() - 1

        

    
    def handleButtonClick(self, button):
        role = self.ui.buttonBox.buttonRole(button)
        if str(role) == "PySide2.QtWidgets.QDialogButtonBox.ButtonRole.ApplyRole":
            ##TODO Upadte to Machine and HWS.cfg file
            self.replace_table_cfg_in_machine(self.table_cfg)
            self.replace_foam_cfg_in_machine(self.foam_cfg)
            
            cfg_data = json.JSONEncoder().encode([self.table_cfg] + [self.foam_cfg])
            cfg_file = open(self.cfg_file_dir, 'w')
            cfg_file.write(cfg_data)
            cfg_file.close()
            
            for obj in FreeCAD.ActiveDocument.WirePath.Group:
                obj.touch()
            FreeCAD.ActiveDocument.recompute()
            
            self.Dialog.close()

        
        elif str(role)== "PySide2.QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole":
            self.save_HWS_cfg_to_file()
            #self.Dialog.close()


class CreateHWSMachine:
    
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/CreateMachine.svg',
                'MenuText': 'Add Simulation cutting table',
                'ToolTip': 'Places one foam cutting table in the active document'}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            try:
                a=FreeCAD.ActiveDocument.HWS_Machine.Name
                return False
            except:
                return True

    def Activated(self):
        # check for already existing machines:
        m_created = False
        if FreeCAD.ActiveDocument.getObject('HWS_Machine'):
            # yes, this is stupid
            m_created = True

        if not(m_created):
            # workaround
            m = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'HWS_Machine')
            HWS_SM.HWS_Machine(m)
            HWS_SM.HWS_MachineViewProvider(m.ViewObject)
            FreeCAD.Gui.SendMsgToActiveView('ViewFit')
            FreeCAD.ActiveDocument.recompute()
        
        try:
            wire = FreeCAD.ActiveDocument.Wire
        except:
            wire = FreeCAD.ActiveDocument.addObject('Part::Feature', 'Wire')
            m.addObject(wire)

        # create WirePath folder if it does not exist
        try:
            WPFolder = FreeCAD.ActiveDocument.WirePath

        except:
            WPFolder = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'WirePath')
            HWS_Path.WirePathFolder(WPFolder)
            HWS_Path.WirePathViewProvider(WPFolder)
            FreeCAD.ActiveDocument.HWS_Machine.addObject(WPFolder)

        Z0 = m.FrameDiameter*1.1*0
        #print("Z0:",Z0)
        ZL = m.ZLength
        Z1 = ZL + Z0 - m.FrameDiameter*0.2

        w = Part.makeLine((0,0,Z0), (0,0,Z1))
        wire.Shape = w
        wire.ViewObject.LineColor = (0,51,254)
"""
def createExtraShapePath(org_obj_name, ext_path=[0,None]):
    #ext_path[0] = index of ext_path, [1] = path
    selObj = selection[i].Object
    shapepath_name = 'ShapePath_' + selObj.Name + "_" + ext_path[0]
    shapepathobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', shapepath_name)
    # initialize python object
    # todo make skipp to where extra path need to continue after created
    NiCrPath.ShapePath(shapepathobj, selObj, True)
    NiCrPath.ShapePathViewProvider(shapepathobj.ViewObject)
    # modify color
    shapepathobj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
    shapepathobj.ViewObject.LineWidth = 1.0
    # ToDo add margins to bounding box in XY plane
    shapepathobj.ViewObject.BoundingBox = True
    WPFolder.addObject(shapepathobj)
"""
class CreateShapePath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/ShapePath.svg',
                'MenuText': 'Route',
                'ToolTip': 'Create the wirepaths for the selected objects'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False


    def Activated(self):
        # retrieve Selection
        selection = FreeCAD.Gui.Selection.getSelectionEx()
        for i in range(len(selection)):
            """
            # create WirePath folder if it does not exist
            try:
                WPFolder = FreeCAD.ActiveDocument.WirePath

            except:
                WPFolder = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'WirePath')
                HWS_Path.WirePathFolder(WPFolder)
                HWS_Path.WirePathViewProvider(WPFolder)
                FreeCAD.ActiveDocument.HWS_Machine.addObject(WPFolder)
            """

            WPFolder = FreeCAD.ActiveDocument.WirePath

            # create shapepath object
            selObj = selection[i].Object
            #if part is part of body select top body
            if len(selObj.InListRecursive) > 0:
                for il in selObj.InListRecursive:
                    selObj = il
            
            shapepath_name = 'ShapePath_' + selObj.Name
            #print(shapepath_name)
            shapepathobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', shapepath_name)
            #print(shapepathobj.Name)
            # initialize python object
            HWS_Path.ShapePath(shapepathobj, selObj)
            HWS_Path.ShapePathViewProvider(shapepathobj.ViewObject)
            # modify color
            shapepathobj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
            shapepathobj.ViewObject.LineWidth = 1.0
            # ToDo add margins to bounding box in XY plane
            #shapepathobj.ViewObject.BoundingBox = True
            WPFolder.addObject(shapepathobj)



class CreatePathLink:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/PathLink.svg',
                'MenuText': 'Link Path',
                'ToolTip': 'Create a link between selected paths'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.HWS_Machine
            return True

        except:
            return False


    def Activated(self):
        # retrieve selection
        selection = FreeCAD.Gui.Selection.getSelectionEx()
        n_obj = len(selection)
        
        
        for objs in selection:
            #print(objs.Label[:9])
            for subobj in objs.SubObjects:
                #todo handle when selecting one point and one edge                
                if str(type(subobj)) == "<class 'Part.Edge'>":
                    if abs(subobj.Vertexes[0].Point[2] - subobj.Vertexes[1].Point[2]) >= 0.001:
                        if n_obj <= 1:
                            self.start_initiate_path(subobj.Vertexes[0].Point, selection, n_obj)
                            break
                        elif n_obj <= 2:
                            self.start_initiate_path(subobj.Vertexes[0].Point, selection, n_obj, 
                                                    [selection[0].SubObjects[0].Vertexes[0].Point, 
                                                    selection[1].SubObjects[0].Vertexes[0].Point])
                            break
                        else:
                            break

                    else:
                        print("Select an horisontal edge!")
                    break
                elif str(type(subobj)) == "<class 'Part.Vertex'>":
                    #print(str(selection[0].SubObjects[0].Point))
                    if n_obj <= 1:
                        self.start_initiate_path(subobj.Point, selection, n_obj)
                        break
                    elif n_obj <= 2:
                        self.start_initiate_path(subobj.Point, selection, n_obj, 
                                                [selection[0].SubObjects[0].Point, 
                                                selection[1].SubObjects[0].Point])
                        break
                    else:
                        break
                else:
                    print("Select 1 or 2 Edges or 1 or 2 Points!")
            break

        
    def start_initiate_path(self, sel_point, sel_obj, num_obj, sel_point_AB = None):    
       
        if num_obj == 1:
            # Create initial/end path if length of sel_obj == 1
            selObj = sel_obj[0]
            try:
                a = FreeCAD.ActiveDocument.InitialPath
                try:
                    a = FreeCAD.ActiveDocument.FinalPath

                except:
                    # create final path, because initial path already exists
                    finalobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','FinalPath')
                    HWS_Path.FinalPath(finalobj, selObj, sel_point)
                    HWS_Path.FinalPathViewProvider(finalobj.ViewObject)
                    finalobj.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
                    finalobj.ViewObject.Transparency = 15
                    finalobj.ViewObject.DisplayMode = 'Shaded'
                    FreeCAD.ActiveDocument.WirePath.addObject(finalobj)

            except:
                # create initial path object
                initialobj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','InitialPath')
                HWS_Path.InitialPath(initialobj, selObj, sel_point)
                HWS_Path.InitialPathViewProvider(initialobj.ViewObject)
                # initial trajectory is red
                initialobj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
                initialobj.ViewObject.Transparency = 15
                initialobj.ViewObject.DisplayMode = 'Shaded'
                FreeCAD.ActiveDocument.WirePath.addObject(initialobj)

        if num_obj == 2:
            # Create link between paths if len(sel_obj) = 2
            selA = sel_obj[0]
            selB = sel_obj[1]
            SelObjA = selA.Object
            SelObjB = selB.Object
            # Link object
            link_name = 'Link_' + SelObjA.Label[10:] + '_' + SelObjB.Label[10:]
            LinkObj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', link_name)
            # initialize link object
            HWS_Path.LinkPath(LinkObj, selA, selB, sel_point_AB)
            HWS_Path.LinkPathViewProvider(LinkObj.ViewObject)
            # link representation
            # LinkObj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)
            LinkObj.ViewObject.Transparency = 15
            # LinkObj.ViewObject.LineColor = (1.0, 0.0, 0.0)
            LinkObj.ViewObject.DisplayMode = "Shaded"
            # add to folder
            FreeCAD.ActiveDocument.WirePath.addObject(LinkObj)


class SaveGCode:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/SaveGCode.svg',
                'MenuText': 'Save G-Code for GRBL micro controler',
                'ToolTip': 'Export G-Code as a .ncfile'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.FinalPath
            return True
        except:
            return False

    def Activated(self):
        HWS_Path.saveGCodeFile()

"""
class ImportWirePath:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/LoadPath.svg',
                'MenuText': 'Import WirePath',
                'ToolTip': 'Import a .nc file'}

    def IsActive(self):
        return True

    def Activated(self):
        HWS_Path.importHWSFile()
"""
# Animation classes
class RunPathSimulation:
    def GetResources(self):
        return {'Pixmap': __dir__ + '/icons/AnimateMachine.svg',
                'MenuText': 'Start Animation',
                'ToolTip': 'Start animation of the current toolpath'}

    def IsActive(self):
        try:
            a = FreeCAD.ActiveDocument.FinalPath
            return True
        except:
            return False

    def Activated(self):
        full_path = HWS_Path.traceObjectsAndLinksForRawPath() #CreateCompleteRawPath()
        HWS_SM.runSimulation(full_path)
        FreeCAD.Console.PrintMessage('Simulation finished\n')
        HWS_SM.returnHome()

if FreeCAD.GuiUp:
    FreeCAD.Gui.addCommand('CreateHWSMachine', CreateHWSMachine())
    FreeCAD.Gui.addCommand('CreateToolPath', CreateShapePath())
    FreeCAD.Gui.addCommand('CreatePathLink', CreatePathLink())
    FreeCAD.Gui.addCommand('SaveGCode', SaveGCode())
    FreeCAD.Gui.addCommand('CutGCode', cutGCode())
    FreeCAD.Gui.addCommand('RunPathSimulation', RunPathSimulation())
    FreeCAD.Gui.addCommand('ConfigureTableNFoam', ConfigureTableNFoam())
    FreeCAD.Gui.addCommand('ClearWireTraces', ClearWireTraces())
    FreeCAD.Gui.addCommand('AlignToCenterZ', AlignToCenterZ())
    FreeCAD.Gui.addCommand('AlignToObjZMin', AlignToObjZMin())
    FreeCAD.Gui.addCommand('AlignToObjZMax', AlignToObjZMax())
    FreeCAD.Gui.addCommand('AlignToObjYMin', AlignToObjYMin())
    FreeCAD.Gui.addCommand('AlignToObjYMax', AlignToObjYMax())
    FreeCAD.Gui.addCommand('AlignToBase', AlignToBase())
    FreeCAD.Gui.addCommand('AlignToBaseZMin', AlignToBaseZMin())
    FreeCAD.Gui.addCommand('AlignToBaseZMax', AlignToBaseZMax())
    FreeCAD.Gui.addCommand('AlignToBaseFront', AlignToBaseFront())
    FreeCAD.Gui.addCommand('AlignToBaseBack', AlignToBaseBack())
    FreeCAD.Gui.addCommand('DistAlongY', DistAlongY())
    FreeCAD.Gui.addCommand('DistAlongX', DistAlongX())
