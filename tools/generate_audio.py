"""Gera paisagens sonoras originais e em loop para cada missão de Turnos Zero.

Usa somente a biblioteca padrão do Python. Os WAVs são 16-bit, mono e 22.050 Hz,
para funcionarem com winsound no Windows sem dependências de áudio adicionais.
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "som"
RATE = 22050
SECONDS = 10
MISSIONS = ("loja_24h", "edificio_9", "cinema_vazio", "laboratorio")


def _smooth_loop(samples: list[float]) -> list[float]:
    """Aplica crossfade cíclico curto para evitar estalo no ponto de repetição."""
    length = len(samples)
    fade = min(int(RATE * 0.18), length // 8)
    if fade <= 0:
        return samples
    result = samples[:]
    for i in range(fade):
        t = i / max(1, fade - 1)
        # Une o fim ao início sem criar uma pausa longa.
        blend = (1.0 - math.cos(math.pi * t)) / 2.0
        start = samples[i]
        end = samples[length - fade + i]
        joined = start * (1.0 - blend) + end * blend
        result[i] = joined
        result[length - fade + i] = joined
    return result


def _sample(kind: str, t: float, rng: random.Random, noise_state: list[float]) -> float:
    white = rng.uniform(-1.0, 1.0)
    noise_state[0] += 0.018 * (white - noise_state[0])
    low_noise = noise_state[0]
    high_noise = white - low_noise

    if kind == "loja_24h":
        # Reator fluorescente, compressor de geladeira e ruído distante de loja.
        hum = 0.075 * math.sin(2 * math.pi * 60.0 * t)
        hum += 0.027 * math.sin(2 * math.pi * 120.0 * t)
        compressor = (0.072 + 0.018 * math.sin(2 * math.pi * 0.19 * t)) * math.sin(2 * math.pi * 43.0 * t)
        compressor += 0.018 * math.sin(2 * math.pi * 86.0 * t)
        ventilation = 0.05 * low_noise + 0.012 * high_noise
        door_sensor = 0.11 * math.exp(-((t % 7.3) / 0.025) ** 2)
        return hum + compressor + ventilation + door_sensor

    if kind == "edificio_9":
        # Vento em dutos, vibração de elevador e estalos de tubulação.
        wind = 0.15 * low_noise + 0.025 * high_noise
        elevator = 0.07 * math.sin(2 * math.pi * 27.0 * t)
        elevator += 0.035 * math.sin(2 * math.pi * 41.0 * t + 0.4)
        pipe = 0.105 * math.exp(-(((t % 5.6) - 2.1) / 0.035) ** 2)
        pipe += 0.06 * math.exp(-(((t % 8.1) - 6.4) / 0.06) ** 2)
        return wind + elevator + pipe

    if kind == "cinema_vazio":
        # Projetor 24 fps estilizado, correia mecânica e sala ampla vazia.
        flutter = 0.72 + 0.28 * math.sin(2 * math.pi * 0.73 * t)
        projector = 0.055 * flutter * math.sin(2 * math.pi * 24.0 * t)
        projector += 0.025 * math.sin(2 * math.pi * 48.0 * t)
        room = 0.10 * low_noise + 0.018 * high_noise
        distant = 0.035 * math.sin(2 * math.pi * 18.0 * t)
        clap = 0.08 * math.exp(-(((t % 9.0) - 4.4) / 0.04) ** 2)
        return projector + room + distant + clap

    if kind == "laboratorio":
        # Ventilação de contenção, fonte elétrica e pulsos de monitor.
        ventilation = 0.085 * math.sin(2 * math.pi * 38.0 * t)
        ventilation += 0.035 * math.sin(2 * math.pi * 76.0 * t)
        electrical = 0.045 * math.sin(2 * math.pi * 50.0 * t + 0.15)
        room = 0.055 * low_noise + 0.014 * high_noise
        pulse = 0.095 * math.exp(-((t % 3.2) / 0.035) ** 2)
        pulse += 0.05 * math.exp(-(((t % 3.2) - 0.21) / 0.045) ** 2)
        return ventilation + electrical + room + pulse

    raise ValueError(f"Missão de áudio desconhecida: {kind}")


def generate_one(kind: str) -> Path:
    rng = random.Random(90210 + MISSIONS.index(kind))
    noise_state = [0.0]
    count = RATE * SECONDS
    samples = [
        _sample(kind, index / RATE, rng, noise_state)
        for index in range(count)
    ]
    samples = _smooth_loop(samples)
    peak = max(abs(value) for value in samples) or 1.0
    gain = 0.34 / peak

    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / f"{kind}.wav"
    with wave.open(str(destination), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(RATE)
        stream.writeframes(b"".join(
            struct.pack("<h", max(-32767, min(32767, int(value * gain * 32767))))
            for value in samples
        ))
    return destination


def generate() -> list[Path]:
    generated = [generate_one(kind) for kind in MISSIONS]
    for path in generated:
        print(f"Áudio gerado: {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    return generated


if __name__ == "__main__":
    generate()
