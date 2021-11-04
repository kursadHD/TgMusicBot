import asyncio
import random

class Queue(asyncio.Queue):
    def __init__(self) -> None:
        super().__init__()
    
    def clear(self) -> None:
        self._queue.clear()
        self._init(0)

    def shuffle(self) -> 'Queue':
        copy = list(self._queue.copy())
        copy.sort(key=lambda _: random.randint(0, 999999999))
        self.clear()
        self._queue.extend(copy)
        return self

    def __iter__(self):
        self.__index = 0
        return self
    
    def __next__(self):
        if self.__index < len(self):
            item = self._queue[self.__index]
            self.__index += 1
            return item
        else:
            raise StopIteration
    
    def __len__(self):
        return len(self._queue)
    
    def __getitem__(self, index):
        return self._queue[index]

    def __str__(self):
        queue = list(self._queue)
        string = ''
        for x, item in enumerate(queue):
            if x < 10:
                string += f'**{x+1}. [{item.title}]({item.yt_url})** ({item.requested_by.mention})\n'
            else:
                string += f'`\n...{len(queue)-10}`'
                return string
        return string


