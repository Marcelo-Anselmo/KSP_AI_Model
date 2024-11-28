from stable_baselines3 import PPO

env = KSPEngineEnv()
model = PPO('MlpPolicy', env, verbose=1)

# Treinar por 100 mil passos
model.learn(total_timesteps=100000)

# Salvar o modelo
model.save("ksp_agent")

