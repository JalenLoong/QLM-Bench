"""Physical axial displacement and 50Hz hold logic; no pair-contact success gate."""
import math

class PressSuccessHold:
    def __init__(self, threshold=.012, required=3):
        if not math.isfinite(threshold) or threshold<=0 or required!=3:
            raise ValueError('Approved positive threshold and3 ticks required')
        self.threshold=threshold;self.required=required;self.reset()
    def reset(self):
        self.count=0;self.last_tick=None;self.first_pressed_ns=None
    def update(self,tick,displacement,not_fallen):
        if not math.isfinite(displacement):raise ValueError('Nonfinite displacement')
        if not not_fallen:self.count=0
        if tick%10 or tick==self.last_tick:return self.count>=self.required and not_fallen
        if self.last_tick is not None and tick!=self.last_tick+10:self.count=0
        self.last_tick=tick
        pressed=displacement>=self.threshold
        if pressed and self.first_pressed_ns is None:self.first_pressed_ns=tick*2_000_000
        self.count=self.count+1 if pressed and not_fallen else 0
        return self.count>=self.required and not_fallen
