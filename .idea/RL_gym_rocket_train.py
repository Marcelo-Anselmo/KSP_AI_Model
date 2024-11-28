import krpc
import time
import gym
from gym import spaces
import numpy as np
from stable_baselines3 import PPO

# Conectar ao servidor KRPC
conn = krpc.connect(name='Voo_Suborbital')

# Obter a espaçonave ativa
vessel = conn.space_center.active_vessel
control = vessel.control
flight = vessel.flight()
orbit = vessel.orbit

class KSPSuborbitalEnv(gym.Env):
    def __init__(self):
        super(KSPSuborbitalEnv, self).__init__()
        self.action_space = spaces.Box(low=np.array([0.0, -1.0, 0.0]), high=np.array([1.0, 1.0, 1.0]), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=np.array([0.0, -500.0, 0.0, -90.0]),
            high=np.array([1e6, 500.0, 1.0, 90.0]),
            dtype=np.float32
        )
        self.conn = krpc.connect(name='KSP Suborbital')
        self.vessel = self.conn.space_center.active_vessel
        self.control = self.vessel.control
        self.flight = self.vessel.flight()
        self.orbit = self.vessel.orbit

    def reset(self):
        # Verificar se o foguete foi destruído ou está inoperante
        if not self.vessel or self.vessel.situation.name in ['destroyed', 'dead']:
            print("Foguete destruído! Reiniciando o voo.")
            # Implementar o método de reinício, por exemplo, carregando o quicksave
            # self._reload_quick_save()


        # Configurar o foguete para o estado inicial
        self.control.throttle = 1.0  # Garantir que o throttle esteja 100% para a decolagem
        self.control.activate_next_stage()  # Liga os motores
        self.vessel.auto_pilot.engage()
        #self.vessel.auto_pilot.target_pitch_and_heading(90, 90)  # Direção vertical

        # Verificar combustível antes de prosseguir
        #max_fuel = self.vessel.resources.max('LiquidFuel')
        #if max_fuel == 0:
        #    raise RuntimeError("O foguete não possui combustível suficiente para reiniciar.")

        return self._get_obs()

    def step(self, action):
        throttle, pitch, activate_stage = action  # Adicionando o comando para ativar estágio

        # Forçar o throttle para 100% se o foguete ainda estiver decolando
        altitude = self.flight.mean_altitude  # Altura acima do solo
        if altitude < 30000:  # Durante a decolagem, forçar throttle a 100%
            self.control.throttle = 1.0
        else:
            self.control.throttle = np.clip(throttle, 0.0, 1.0)  # Caso contrário, usar o throttle da ação

        if self.flight.mean_altitude <= 1000:
            self.vessel.auto_pilot.target_pitch_and_heading(35, 90)
        elif altitude >= 70000:
            self.vessel.auto_pilot.target_pitch = np.clip(pitch * 90.0, -90.0, 90.0)
        # Aplicando pitch
        #self.vessel.auto_pilot.target_pitch = np.clip(pitch * 90.0, -90.0, 90.0)

        # Variáveis de estado do foguete
        vertical_speed = self.flight.vertical_speed  # Velocidade vertical
        situation = self.vessel.situation.name  # Situação do foguete (ex.: "flying", "landed")

        reward = 0  # Inicializando recompensa

        # Verificar se o paraquedas pode ser ativado
        if activate_stage > 0.5:  # Tentativa de ativar estágio
            if situation == 'flying' and altitude < 5000 and vertical_speed < -50:
                self.control.activate_next_stage()  # Ativa o paraquedas
                reward += 10  # Recompensa por ativar no momento correto
            else:
                reward -= 10  # Penalidade por ativar em momento errado

        # Observar estado atual
        obs = self._get_obs()

        # Calcular a recompensa
        reward = obs[0] * 0.01 - abs(obs[3]) * 0.1 - (1 - obs[2]) * 0.5  # Ajuste a recompensa conforme necessário

        # Determinar se o episódio termina
        done = obs[0] > 70000 or self.vessel.situation.name in ['landed', 'destroyed']

        return obs, reward, done, {}

    def _get_obs(self):
        # Obter os valores relevantes
        altitude = self.flight.mean_altitude
        #apoapsis = self.vessel.orbit.apoapsis_altitude
        vertical_speed = self.flight.vertical_speed
        max_fuel = self.vessel.resources.max('LiquidFuel')
        current_fuel = self.vessel.resources.amount('LiquidFuel')

        # Evitar divisão por zero
        fuel_ratio = current_fuel / max_fuel if max_fuel > 0 else 0.0

        pitch = self.flight.pitch

        # Retornar o vetor de observação
        return np.array([altitude, vertical_speed, fuel_ratio, pitch])

    def render(self, mode='human'):
        print(f"Altitude: {self.flight.mean_altitude:.2f}, Velocidade: {self.flight.vertical_speed:.2f}, Combustível: {self.vessel.resources.amount('LiquidFuel'):.2f}")



# Criar o ambiente
env = KSPSuborbitalEnv()

# Treinar o agente
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)  # Reinicia sozinho após explosões

# Salvar o modelo
model.save("ksp_suborbital_agent")

# Carregar o modelo
model = PPO.load("ksp_suborbital_agent")

# Testar o agente
obs = env.reset()

for _ in range(1000):  # Executar 1000 passos
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, info = env.step(action)
    env.render()

    if done:
        print("Missão concluída!")
        break
