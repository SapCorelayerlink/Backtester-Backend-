from core.base import StrategyBase
from core.registry import StrategyRegistry

@StrategyRegistry.register("SampleStrategy")
class SampleStrategy(StrategyBase):
    def on_data(self, data):
        print(f"{self.name}: Received data: {data}")

    def on_order(self, order):
        print(f"{self.name}: Order update: {order}")

    def start(self):
        print(f"{self.name}: Strategy started")

    def stop(self):
        print(f"{self.name}: Strategy stopped") 