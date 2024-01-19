from tqdm import tqdm
import time
import random


class MultiProgressBar:
    def __init__(self, *bars):
        self.bars = {desc: tqdm(total=total, desc=desc) for desc, total in bars}

    def update(self, bar_id, amount):
        if bar_id in self.bars:
            self.bars[bar_id].update(amount)

    def set_total(self, bar_id, new_total):
        if bar_id in self.bars:
            self.bars[bar_id].total = new_total
            self.bars[bar_id].refresh()  # Refresh to display the new total immediately

    def close(self):
        for bar in self.bars.values():
            bar.close()


# Example usage
if __name__ == "__main__":
    progress_bars = MultiProgressBar(("test", 100), ("test2", 100))

    for _ in range(50):
        i = random.randint(0, 2)
        if i == 0:
            progress_bars.update("test", 1)
            progress_bars.update("test2", random.randint(0, 3))
        else:
            progress_bars.update("test", random.randint(0, 3))
            progress_bars.update("test2", 1)

        # Example of changing the total on the fly
        if _ == 25:
            progress_bars.set_total("test", 150)

        time.sleep(1)
    progress_bars.close()
