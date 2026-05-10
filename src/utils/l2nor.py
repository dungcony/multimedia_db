
import math


def l2nor(vec):
    #sum = sqrt(pixeli * pixeli) i = {0->n)
    tmp = 0.0
    for val in vec:
        tmp += val * val

    tmp = math.sqrt(tmp)
    if tmp != 0:
        vec /= tmp
    return vec