# Copyright 2021 The Brax Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# python3
"""Network definitions."""

from typing import Any, Callable, Sequence, Tuple

import dataclasses
from flax import linen
import jax
import jax.numpy as jnp


@dataclasses.dataclass
class FeedForwardModel:
  init: Any
  apply: Any


class MLP(linen.Module):
  """MLP module."""
  layer_sizes: Sequence[int]
  activation: Callable[[jnp.ndarray], jnp.ndarray] = linen.relu
  kernel_init: Callable[..., Any] = jax.nn.initializers.lecun_uniform()
  activate_final: bool = False
  bias: bool = True

  @linen.compact
  def __call__(self, data: jnp.ndarray):
    hidden = data
    for i, hidden_size in enumerate(self.layer_sizes):
      hidden = linen.Dense(
          hidden_size,
          name=f'hidden_{i}',
          kernel_init=self.kernel_init,
          use_bias=self.bias)(
              hidden)
      if i != len(self.layer_sizes) - 1 or self.activate_final:
        hidden = self.activation(hidden)
    return hidden


def make_model(layer_sizes: Sequence[int],
               obs_size: int,
               activation: Callable[[jnp.ndarray], jnp.ndarray] = linen.swish,
               ) -> FeedForwardModel:
  """Creates a model.

  Args:
    layer_sizes: layers
    obs_size: size of an observation
    activation: activation

  Returns:
    a model
  """
  module = MLP(layer_sizes=layer_sizes, activation=activation)
  dummy_obs = jnp.zeros((1, obs_size))
  return FeedForwardModel(
      init=lambda rng: module.init(rng, dummy_obs), apply=module.apply)


def make_models(policy_params_size: int,
                obs_size: int) -> Tuple[FeedForwardModel, FeedForwardModel]:
  """Creates models for policy and value functions.

  Args:
    policy_params_size: number of params that a policy network should generate
    obs_size: size of an observation

  Returns:
    a model for policy and a model for value function
  """
  policy_model = make_model([32, 32, 32, 32, policy_params_size], obs_size)
  value_model = make_model([256, 256, 256, 256, 256, 1], obs_size)
  return policy_model, value_model

def make_multiagent_models(policy_params_sizes: list,
                           num_agents: int,
                           obs_size: int) -> Tuple[FeedForwardModel, FeedForwardModel]:
  """Creates models for policy and value functions.

  Args:
    policy_params_size: number of params that a policy network should generate
    obs_size: size of an observation

  Returns:
    a model for policy and a model for value function
  """
  # TODO: modify obs_size to be a list
  policy_models = [make_model([32, 32, 32, 32, policy_params_sizes[i]], obs_size) for i in range(num_agents)]
  value_model = make_model([256, 256, 256, 256, 256, num_agents], obs_size * num_agents)
  return policy_models, value_model
