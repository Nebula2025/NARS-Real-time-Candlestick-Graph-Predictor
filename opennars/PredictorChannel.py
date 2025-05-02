import random
import socket

from pynars.NARS import Reasoner
from pynars.NARS.DataStructures.MC.SensorimotorChannel import SensorimotorChannel
from pynars.Narsese import parser

nars_address = ("127.0.0.1", 54321)
predict_address = ("127.0.0.1", 12345)


class PredictorChannel(SensorimotorChannel):

    def __init__(
        self,
        ID,
        num_slot,
        num_events,
        num_anticipations,
        num_operations,
        num_predictive_implications,
        num_reactions,
        N=1,
    ):
        super().__init__(
            ID,
            num_slot,
            num_events,
            num_anticipations,
            num_operations,
            num_predictive_implications,
            num_reactions,
            N,
        )

        """
        Babbling is a lightweight fallback mechanism: if the current channel can’t derive an operation from a reaction, 
        there’s a small chance that babbling will step in and generate one instead. Note that, for now, each channel 
        may perform only one operation per cycle—this restriction can be relaxed in future releases once we define 
        mutual exclusivity rules between operations.
        
        Babbling is consumable: it can only be used a limited number of times and does not replenish.
        """

        self.num_babbling = 1000
        self.babbling_chance = 1

    def information_gathering(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(nars_address)
        data, _ = sock.recvfrom(1024)
        status = data.decode()
        if status != "CONNECTION FAILED":
            try:
                return [parser.parse(each) for each in status.split("|")]
            except:
                print(status)
                exit()
        else:
            return []

    def babbling(self):
        """
        Based on the probability and remaining counts.
        """
        if random.random() < self.babbling_chance and self.num_babbling > 0:
            self.num_babbling -= 1
            return random.choice(list(self.operations.keys()))


def execute_Mup():
    """
    All channels need to register for its own operations. It is recommended to list them in the channel created.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto("^up".encode(), predict_address)


def execute_Mdown():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto("^down".encode(), predict_address)


def execute_Hold():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto("^hold".encode(), predict_address)


if __name__ == "__main__":
    r = Reasoner(100, 100)
    pc = PredictorChannel("Predictor", 2, 5, 20, 5, 50, 50, 1)
    pc.register_operation("^up", execute_Mup, ["^up", "up"])
    pc.register_operation("^down", execute_Mdown, ["^down", "down"])
    pc.register_operation("^hold", execute_Hold, ["^hold", "hold"])

    while True:
        pc.channel_cycle(r.memory)
        pc.input_buffer.predictive_implications.show(lambda x: x.task.sentence)
