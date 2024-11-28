import krpc
import time

conn = krpc.connect(name='Sub_Orbital_AI ;D')
vessel = conn.space_center.active_vessel

#Inicia os motores e mira o foguete a 90 graus
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.auto.pilot.engage()
vessel.control.throttle = 1.0
time.sleep(1)
print('Decolando!!')
vessel.control.activate_next_stage()