import krpc
import time

#Conexão com o KSP
conn = krpc.connect(name='Controle de Foguete')
vessel = conn.space_center.active_vessel

#Ligar motores e decolar
vessel.control.throttle = 1.0
vessel.control.activate_next_stage()
print('Decolando!')

#Monitorar altitude
while vessel.flight().mean_altitude < 10000:
    print(f'Altitude: {vessel.flight().mean_altitude:.2f}m')
    time.sleep(0.5)

#Desligar motores
vessel.control.throttle = 0.0
print('Motores desligados ao atingir 10km!')