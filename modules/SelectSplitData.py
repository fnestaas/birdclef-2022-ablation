import torch.nn as nn 
from numpy.random import uniform
import torch

class SelectSplitData(nn.Module):
    def __init__(
        self, 
        duration: int, 
        n_splits: int, 
        offset=None, 
        sr=16000
    ):

        """
        Select a chunk of size duration and split it into n_splits
        Parameters:
            duration:
                time in seconds to extract from data
            n_splits:
                number of splits to make 
            offset:
                when to start loading. If None, we choose a random offset each time
        """  
        super().__init__()
        self.duration = duration 
        self.n_splits = n_splits
        self.offset = offset
        self.sr = sr

    def forward(self, x):
        if isinstance(x, tuple):
            return self.forward_x(x[0]), x[1]
        else:
            return self.forward_x(x)
    
    def forward_x(self, x: torch.Tensor):
        """
        Select for a duration and split the data. If the duration is too short, we pad with 0's
        Parameters:
            x:
                array or tensor from which to select and to split
            sr:
                sampling rate at which x was recorded
        Returns:
            processed version of x with shape (n_splits, ..., x.shape[-1]//n_folds)
        """
        sr = self.sr
        total_duration = x.shape[-1] / sr
        if total_duration < self.duration:
            x = torch.concat([x, torch.zeros((*x.shape[:-1], self.duration * sr - x.shape[-1]), device = x.device)], axis=-1)
            total_duration = self.duration
        max_offset = total_duration - self.duration 
        if self.offset is None:
            offset = uniform(low=0.0, high=max_offset)
        else:
            offset = min(self.offset, max_offset)
        start = int(offset*sr)
        stop = min([int((offset + self.duration)*sr), x.shape[-1]])
        x = x[..., start:stop]
        # x = x.reshape((1, *x.shape))

        # return x.reshape((self.n_splits, *x.shape[1:-1], -1))
        return x.reshape((x.shape[0]*self.n_splits, *x.shape[1:-1], -1))

class RejoinSplitData(SelectSplitData):
    def forward(self, x: torch.Tensor):
        """
        Does the reverse operation of what SelectSplitData does.
        """
        assert x.shape[0] % self.n_splits == 0, 'invalid shape of x!'
        return x.reshape((x.shape[0]//self.n_splits, *x.shape[1:-1], -1))
        