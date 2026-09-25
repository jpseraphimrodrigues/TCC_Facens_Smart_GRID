"""Modelo discreto de entrega de mensagens para experimentos de consenso.

Este módulo não altera o baseline determinístico. Ele fornece a camada de
comunicação que deve ser conectada ao controlador quando o experimento
probabilístico/temporal for habilitado.
"""

import random
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    """Mensagem publicada por um agente para um vizinho."""

    origin: int
    destination: int
    content: dict
    send_step: int
    delivery_step: int | None = None


class CommunicationChannel:
    """Canal discreto com perda Bernoulli, atraso inteiro e fila FIFO."""

    def __init__(self, loss_probability: float = 0.0, delay_steps: int = 0, seed: int | None = None):
        if not 0.0 <= loss_probability <= 1.0:
            raise ValueError("loss_probability deve estar entre 0 e 1")
        if delay_steps < 0:
            raise ValueError("delay_steps não pode ser negativo")
        self.loss_probability = loss_probability
        self.delay_steps = delay_steps
        self.random = random.Random(seed)
        self.queue: deque[Message] = deque()
        self.last_received: dict[tuple[int, int], Message] = {}
        self.attempted = 0
        self.delivered = 0
        self.lost = 0
        self.events: list[dict] = []

    def transmit(self, origin: int, destination: int, content: dict, step: int) -> bool:
        """Tenta publicar uma mensagem e retorna se ela entrou na fila."""
        self.attempted += 1
        if self.random.random() < self.loss_probability:
            self.lost += 1
            self.events.append({
                "origin": origin,
                "destination": destination,
                "send_step": step,
                "delivery_step": None,
                "status": "lost",
                "delay_steps": self.delay_steps,
            })
            return False
        message = Message(origin, destination, dict(content), step, step + self.delay_steps)
        self.queue.append(message)
        self.events.append({
            "origin": origin,
            "destination": destination,
            "send_step": step,
            "delivery_step": message.delivery_step,
            "status": "queued",
            "delay_steps": self.delay_steps,
        })
        return True

    def deliver_until(self, step: int) -> list[Message]:
        """Entrega mensagens cujo instante de entrega já foi alcançado."""
        delivered: list[Message] = []
        while self.queue and self.queue[0].delivery_step <= step:
            message = self.queue.popleft()
            delivered.append(message)
            self.last_received[(message.origin, message.destination)] = message
            self.delivered += 1
            for event in reversed(self.events):
                if event["status"] == "queued" and event["origin"] == message.origin and event["destination"] == message.destination and event["send_step"] == message.send_step:
                    event["status"] = "delivered"
                    break
        return delivered

    def current_state(self, origin: int, destination: int) -> Message | None:
        """Retorna a última mensagem válida de uma origem para um destino."""
        return self.last_received.get((origin, destination))

    def metrics(self) -> dict[str, int | float]:
        """Retorna contadores serializáveis do canal."""
        return {
            "messages_attempted": self.attempted,
            "messages_delivered": self.delivered,
            "messages_lost": self.lost,
            "loss_rate_percent": 100.0 * self.lost / max(self.attempted, 1),
            "messages_pending": len(self.queue),
        }
