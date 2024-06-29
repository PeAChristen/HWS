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


class HWS_Workbench(Workbench):
    import HWS_Init  # this is needed to load the workbench icon
    # __dir__ = os.path.dirname( __file__ ) # __file__ is not working
    Icon = HWS_Init.__dir__ + '/icons/WorkbenchIcon.svg'
    MenuText = 'HWS'
    ToolTip = 'Workbench for to generate G-Code for grbl based 4 axis foam cutters'

    def GetClassName(self):
        return 'Gui::PythonWorkbench'

    def Initialize(self):
        import HWS_Init
        self.tools = ['CreateHWSMachine',
                      'CreateToolPath',
                      'CreatePathLink',
                      'SaveGCode',
                      'CutGCode',
                      'RunPathSimulation',
                      'ConfigureTableNFoam',
                      'ClearWireTraces',
                      'AlignToCenterZ',
                      'AlignToObjZMin',
                      'AlignToObjZMax',
                      'AlignToObjYMin',
                      'AlignToObjYMax',
                      'AlignToBase',
                      'AlignToBaseZMin',
                      'AlignToBaseZMax',
                      'AlignToBaseFront',
                      'AlignToBaseBack',
                      'DistAlongY',
                      'DistAlongX']

        FreeCAD.t = self.appendToolbar('HWS_Workbench', self.tools)
        self.appendMenu('HWS', self.tools)
        #TODO load config table n foam when WB loads
        HWS_Init.load_hws_cfg()
        FreeCAD.Console.PrintMessage('HWS workbench loaded\n')
        
    def Activated(self):
        pass


FreeCADGui.addWorkbench(HWS_Workbench)
