import gym
import matplotlib.pyplot as plt

env = gym.make("Image84PointmassUWallTrainEnvHard-v1")

env.reset()
frame = env.render(mode="rgb_array")

fig = plt.figure()
plt.imshow(frame)

plt.savefig("env_image.png")