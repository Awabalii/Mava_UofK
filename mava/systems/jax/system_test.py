# python3
# Copyright 2021 InstaDeep Ltd. All rights reserved.
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


"""Tests for Jax-based Mava system implementation."""
from dataclasses import dataclass, field
from typing import List

import pytest

from mava.components.jax import Component
from mava.core_jax import SystemBuilder
from mava.specs import DesignSpec
from mava.systems.jax.system import System


# Mock components
class MainComponent(Component):
    @property
    def name(self) -> str:
        """Component type name, e.g. 'dataset' or 'executor'.

        Returns:
            Component type name
        """
        return "main_component"


class SubComponent(Component):
    @property
    def name(self) -> str:
        """Component type name, e.g. 'dataset' or 'executor'.

        Returns:
            Component type name
        """
        return "sub_component"


@dataclass
class ComponentZeroDefaultConfig:
    param_0: int = 1
    param_1: str = "1"


class ComponentZero(MainComponent):
    def __init__(
        self, config: ComponentZeroDefaultConfig = ComponentZeroDefaultConfig()
    ) -> None:
        """Mock system component.

        Args:
            config : dataclass configuration for setting component hyperparameters
        """
        self.config = config

    def on_building_start(self, builder: SystemBuilder) -> None:
        """Dummy component function.

        Returns:
            config int plus string cast to int
        """
        builder.config.int_plus_str = self.config.param_0 + int(self.config.param_1)


@dataclass
class ComponentOneDefaultConfig:
    param_2: float = 1.2
    param_3: bool = True


class ComponentOne(SubComponent):
    def __init__(
        self, config: ComponentOneDefaultConfig = ComponentOneDefaultConfig()
    ) -> None:
        """Mock system component.

        Args:
            config : dataclass configuration for setting component hyperparameters
        """
        self.config = config

    def on_building_start(self, builder: SystemBuilder) -> None:
        """Dummy component function.

        Returns:
            float plus boolean cast as float
        """
        builder.config.float_plus_bool = self.config.param_2 + float(
            self.config.param_3
        )


@dataclass
class ComponentTwoDefaultConfig:
    param_4: str = "2"
    param_5: bool = True


class ComponentTwo(MainComponent):
    def __init__(
        self, config: ComponentTwoDefaultConfig = ComponentTwoDefaultConfig()
    ) -> None:
        """Mock system component.

        Args:
            config : dataclass configuration for setting component hyperparameters
        """
        self.config = config

    def on_building_start(self, builder: SystemBuilder) -> None:
        """Dummy component function.

        Returns:
            string cast as int plus boolean cast as in
        """
        builder.config.str_plus_bool = int(self.config.param_4) + int(
            self.config.param_5
        )


@dataclass
class DistributorDefaultConfig:
    num_executors: int = 1
    nodes_on_gpu: List[str] = field(default_factory=list)
    multi_process: bool = True
    name: str = "system"


class MockDistributorComponent(Component):
    def __init__(
        self, config: DistributorDefaultConfig = DistributorDefaultConfig()
    ) -> None:
        """Mock system distributor component.

        Args:
            config : dataclass configuration for setting component hyperparameters
        """
        self.config = config

    @property
    def name(self) -> str:
        """Component type name, e.g. 'dataset' or 'executor'.

        Returns:
            Component type name
        """
        return "distributor"


class TestSystemWithZeroComponents(System):
    def design(self) -> DesignSpec:
        """Mock system design with zero components.

        Returns:
            system callback components
        """
        components = DesignSpec(distributor=MockDistributorComponent)
        return components


class TestSystemWithOneComponent(System):
    def design(self) -> DesignSpec:
        """Mock system design with one component.

        Returns:
            system callback components
        """
        components = DesignSpec(
            main_component=ComponentZero, distributor=MockDistributorComponent
        )
        return components


class TestSystemWithTwoComponents(System):
    def design(self) -> DesignSpec:
        """Mock system design with two components.

        Returns:
            system callback components
        """
        components = DesignSpec(
            main_component=ComponentZero,
            sub_component=ComponentOne,
            distributor=MockDistributorComponent,
        )
        return components


# Test fixtures
@pytest.fixture
def system_with_zero_components() -> System:
    """Dummy system with zero components.

    Returns:
        mock system
    """
    return TestSystemWithZeroComponents()


@pytest.fixture
def system_with_one_component() -> System:
    """Dummy system with one component.

    Returns:
        mock system
    """
    return TestSystemWithOneComponent()


@pytest.fixture
def system_with_two_components() -> System:
    """Dummy system with two components.

    Returns:
        mock system
    """
    return TestSystemWithTwoComponents()


# Tests
def test_system_launch_with_build(
    system_with_two_components: System,
) -> None:
    """Test if system can launch having had changed (buildd) the default \
        config.

    Args:
        system_with_two_components : mock system
    """
    system_with_two_components.build(param_0=2, param_3=False)
    assert system_with_two_components._builder.config.int_plus_str == 3
    assert system_with_two_components._builder.config.float_plus_bool == 1.2
    system_with_two_components.launch()


def test_system_update_with_existing_component(
    system_with_two_components: System,
) -> None:
    """Test if system can update existing component.

    Args:
        system_with_two_components : mock system
    """
    system_with_two_components.update(ComponentTwo)
    system_with_two_components.build()
    assert system_with_two_components._builder.config.float_plus_bool == 2.2
    assert system_with_two_components._builder.config.str_plus_bool == 3


def test_system_update_with_non_existing_component(
    system_with_one_component: System,
) -> None:
    """Test if system raises an error when trying to update a component that has not \
        yet been added to the system.

    Args:
        system_with_one_component : mock system
    """
    with pytest.raises(Exception):
        system_with_one_component.update(ComponentOne)


def test_system_add_with_existing_component(system_with_one_component: System) -> None:
    """Test if system raises an error when trying to add a component that has already \
        been added to the system, i.e. we don't want to overwrite a component by \
        mistake.

    Args:
        system_with_one_component : mock system
    """
    with pytest.raises(Exception):
        system_with_one_component.add(ComponentTwo)


def test_system_add_with_non_existing_component(
    system_with_one_component: System,
) -> None:
    """Test if system can add a new component.

    Args:
        system_with_one_component : mock system
    """
    system_with_one_component.add(ComponentOne)
    system_with_one_component.build()
    assert system_with_one_component._builder.config.int_plus_str == 2
    assert system_with_one_component._builder.config.float_plus_bool == 2.2


def test_system_update_twice(system_with_two_components: System) -> None:
    """Test if system can update a component twice.

    Args:
        system_with_two_components : mock system
    """
    system_with_two_components.update(ComponentTwo)
    system_with_two_components.update(ComponentZero)
    system_with_two_components.build()
    assert system_with_two_components._builder.config.int_plus_str == 2
    assert system_with_two_components._builder.config.float_plus_bool == 2.2


def test_system_add_twice(system_with_zero_components: System) -> None:
    """Test if system can add two components.

    Args:
        system_with_zero_components : mock system
    """
    system_with_zero_components.add(ComponentOne)
    system_with_zero_components.add(ComponentTwo)
    system_with_zero_components.build()
    assert system_with_zero_components._builder.config.float_plus_bool == 2.2
    assert system_with_zero_components._builder.config.str_plus_bool == 3


def test_system_add_and_update(system_with_zero_components: System) -> None:
    """Test if system can add and then update a component.

    Args:
        system_with_zero_components : mock system
    """
    system_with_zero_components.add(ComponentZero)
    system_with_zero_components.update(ComponentTwo)
    system_with_zero_components.build()
    assert system_with_zero_components._builder.config.str_plus_bool == 3


def test_system_build_one_component_params(
    system_with_two_components: System,
) -> None:
    """Test if system can build a single component's parameters.

    Args:
        system_with_two_components : mock system
    """
    system_with_two_components.build(param_0=2, param_1="2")
    assert system_with_two_components._builder.config.int_plus_str == 4
    assert system_with_two_components._builder.config.float_plus_bool == 2.2


def test_system_build_two_component_params(
    system_with_two_components: System,
) -> None:
    """Test if system can build multiple component parameters.

    Args:
        system_with_two_components : mock system
    """
    system_with_two_components.build(param_0=2, param_3=False)
    assert system_with_two_components._builder.config.int_plus_str == 3
    assert system_with_two_components._builder.config.float_plus_bool == 1.2
