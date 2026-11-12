import random
import colorsys


def make_color() -> list:
    return [random.randrange(0, 256) for _ in range(3)]


def is_red_orange_or_black(c: list) -> bool:
    r, g, b = c
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360

    black = v < 0.25                                   # preto / quase preto
    red_orange = (h <= 45 or h >= 345) and s > 0.4 and v >= 0.25  # vermelho..laranja
    return black or red_orange


def color() -> list:
    c = make_color()
    if is_red_orange_or_black(c):
        return color()  # gera de novo ate nao cair nessas condicoes
    return c