from typing import Type, Dict, List
from core.base import StrategyBase, BrokerBase

class StrategyRegistry:
    _strategies: Dict[str, Type[StrategyBase]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(strategy_cls: Type[StrategyBase]):
            cls._strategies[name] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Type[StrategyBase]:
        return cls._strategies[name]

    @classmethod
    def list(cls) -> List[str]:
        return list(cls._strategies.keys())

class BrokerRegistry:
    _brokers: Dict[str, Type[BrokerBase]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(broker_cls: Type[BrokerBase]):
            cls._brokers[name] = broker_cls
            return broker_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Type[BrokerBase]:
        return cls._brokers[name]

    @classmethod
    def list(cls) -> List[str]:
        return list(cls._brokers.keys()) 