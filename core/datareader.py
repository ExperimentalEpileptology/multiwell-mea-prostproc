import pyabf
from dataclasses import dataclass
import numpy as np
from typing import Dict, List
import os

@dataclass
class sweep:
    x: np.array
    y: np.array
    s: np.array

    x_label: str
    y_label: str
    s_label: str



@dataclass
class sweep_data:
    filename: str
    filepath: str
    protocol: str
    timestamp: str

    channel_names: List[str]

    sweep_count: int
    channel_count: int

    sweeps: Dict[int, Dict[int, sweep]]

class abf_data():
    def __init__(self, filename):
        self.abf = pyabf.ABF(filename)

        self.filepath = os.path.abspath(filename)
        self.filename = os.path.basename(filename)

        # Try to gather the most important information
        self.protocol = self.abf.protocolPath
        self.timestamp = self.abf.abfDateTimeString
        self.channel_count = self.abf.channelCount
        self.sweep_count = self.abf.sweepCount


    def get_data(self):
        sweeps = dict()
        for c in range(self.channel_count):
            sweeps[c] = dict()
            for s in range(self.sweep_count):
                self.abf.setSweep(channel=c, sweepNumber=s)
                sweeps[c][s] = sweep(x=self.abf.sweepX, 
                                     y=self.abf.sweepY,
                                     s=self.abf.sweepC,
                                     x_label=self.abf.sweepLabelX,
                                     y_label=self.abf.sweepLabelY,
                                     s_label=self.abf.sweepLabelC,)
        
        return sweep_data(filepath = self.filepath,
                          filename=self.filename,
                          protocol=self.protocol,
                          timestamp=self.timestamp,
                          channel_names=self.abf.dacNames,
                          sweeps=sweeps,
                          sweep_count=self.sweep_count,
                          channel_count=self.channel_count)
        


        print(self.abf.getAllYs())