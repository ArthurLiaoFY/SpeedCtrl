from collections import defaultdict

import numpy as np
import plotly
import plotly.graph_objects as go
from agent import Agent
from config import eqp_kwargs, q_learning_kwargs
from eqp_env import EqpEnv
from plotly.subplots import make_subplots

env = EqpEnv(eqp_idx=0, **eqp_kwargs)
agent = Agent(**eqp_kwargs, **q_learning_kwargs)

n_episodes = 10000

rewards = []

max_total_reward = -np.inf

max_step = 500

for episode in range(n_episodes):
    step_cnt = 0
    env.reset()
    total_reward = 0
    while (
        env.current_unprocessed_amount + env.current_head_queued > 0
        and step_cnt <= max_step
    ):

        state = env.eqp_state.copy()
        action_idx = agent.select_action_idx(
            state_tuple=tuple(v for v in state.values())
        )
        action = agent.action_idx_to_action(action_idx=action_idx)
        reward, depart_actual, depart_ability = env.step(action=action)

        agent.update_policy(
            state_tuple=tuple(v for v in state.values()),
            action_idx=action_idx,
            reward=reward,
            next_state_tuple=tuple(v for v in env.eqp_state.values()),
        )

        total_reward += reward
        step_cnt += 1
    agent.update_lr_er(episode=episode)
    rewards.append(total_reward)
    if total_reward > max_total_reward:
        # print
        max_total_reward = total_reward
        print(
            f"Episode {episode}/{n_episodes}: Total reward : {total_reward}, Step: {step_cnt}"
        )


agent.save_table(
    prefix="single_machine_v2"
    + f"_feeding_speed_{eqp_kwargs.get('feeding_speed')}"
    + f"_shipping_speed_{eqp_kwargs.get('shipping_speed')}"
    + "_"
)

fig = go.Figure()
fig.add_trace(go.Scatter(x=np.arange(len(rewards)), y=rewards, mode="lines+markers"))
plotly.offline.plot(figure_or_data=fig, filename="reward_trend.html")
