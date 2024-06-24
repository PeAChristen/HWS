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

#  root kerf foam_cfg[selected_foam][1] and tip kerf foam_cfg[selected_foam][3] at 0,4 length diffrence

import FreeCAD
import json

def getFoamProperties(obj):
    foam_from_machine = FreeCAD.ActiveDocument.HWS_Machine.FoamConfig 
    foam_cfg = json.JSONDecoder().decode(foam_from_machine[obj.FoamIndex])

    heat = foam_cfg[4] * 10 
    speed = foam_cfg[2]
    return heat, speed
