#Name: Pause at height
#Info: Pause the printer at a certain height
#Depend: GCode
#Type: postprocess
#Param: pauseLevel(float:5.0) Pause height (mm)
#Param: parkX(float:190) Head park X (mm)
#Param: parkY(float:190) Head park Y (mm)
#Param: moveZ(float:0) Head move Z (mm)
#Param: retractAmount(float:5) Retraction amount (mm)

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import re
from Cura.util import profile

def getValue(line, key, default = None):
	if not key in line or (';' in line and line.find(key) > line.find(';')):
		return default
	subPart = line[line.find(key) + 1:]
	m = re.search('^[0-9]+\.?[0-9]*', subPart)
	if m is None:
		return default
	try:
		return float(m.group(0))
	except:
		return default

with open(filename, "r") as f:
	lines = f.readlines()

z = 0.
x = 0.
y = 0.
pauseState = 0
currentSectionType = 'STARTOFFILE'
with open(filename, "w") as f:
	for line in lines:
		if line.startswith(';'):
			if line.startswith(';TYPE:'):
				currentSectionType = line[6:].strip()
			f.write(line)
			continue
		if getValue(line, 'G', None) == 1 or getValue(line, 'G', None) == 0:
			newZ = getValue(line, 'Z', z)
			x = getValue(line, 'X', x)
			y = getValue(line, 'Y', y)
			if newZ != z and currentSectionType != 'CUSTOM':
				z = newZ
				if z < pauseLevel and (pauseState == 0 or pauseState == 2): #pauseState going from 2 to 1 mean we can support print one at a time mode.
					pauseState = 1
				if z >= pauseLevel and pauseState == 1:
					pauseState = 2
					f.write(";TYPE:CUSTOM\n")
					#Retract
					f.write("M83\n")
					f.write("G1 E-%f F6000\n" % (retractAmount))

					zChanged = False
					#Change z before doing the move because the nozzle can hit the glass lock on the UM2
					if z + moveZ < 15:
						zChanged = True
						f.write("G1 Z15 F300\n")

					elif moveZ > 0:
						newZ = z + moveZ
						maxZ = profile.getMachineSettingFloat('machine_height') - 10 #For Safety Leave a 10mm space (endstop)
						if maxZ < newZ:
							newZ = maxZ

						if newZ > z:
							zChanged = True
							f.write("G1 Z%f F300\n" % (newZ))

					#Move the head away
					f.write("G1 X%f Y%f F9000\n" % (parkX, parkY))

					#Disable the E steppers
					f.write("M84 E0\n")
					#Wait till the user continues printing
					f.write("M0\n")
					#Push the filament back, and retract again, the properly primes the nozzle when changing filament.
					f.write("G1 E%f F6000\n" % (retractAmount))
					f.write("G1 E-%f F6000\n" % (retractAmount))

					#Move the head back. Move Z at the same time to prevent hitting the glass locks on the UM2
					if zChanged :
						f.write("G1 X%f Y%f Z%f F9000\n" % (x, y, z+1))
					else:
						f.write("G1 X%f Y%f F9000\n" % (x, y))

					f.write("G1 E%f F6000\n" % (retractAmount))
					f.write("G1 F9000\n")
					f.write("M82\n")
		f.write(line)