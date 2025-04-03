import string
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Rotor:
    def __init__(self, wiring: str, notch: str, position: str = 'A'):
        self.wiring = wiring
        self.notch = notch
        self.position = position

    def encode_forward(self, c: str) -> str:
        pos_offset = string.ascii_uppercase.index(self.position)
        input_index = (string.ascii_uppercase.index(c) + pos_offset) % 26
        wired_letter = self.wiring[input_index]
        output_index = (string.ascii_uppercase.index(wired_letter) - pos_offset) % 26
        result = string.ascii_uppercase[output_index]
        logger.debug(f"  Rotor {self.wiring[:4]} (fwd): {c} -> {result} [pos {self.position}]")
        return result

    def encode_backward(self, c: str) -> str:
        pos_offset = string.ascii_uppercase.index(self.position)
        for i in range(26):
            shifted_index = (i + pos_offset) % 26
            if self.wiring[shifted_index] == c:
                result = string.ascii_uppercase[i]
                logger.debug(f"  Rotor {self.wiring[:4]} (bwd): {c} -> {result} [pos {self.position}]")
                return result
        raise ValueError(f"Character {c} not found in wiring during backward encoding")

    def step(self):
        prev_pos = self.position
        self.position = string.ascii_uppercase[(string.ascii_uppercase.index(self.position) + 1) % 26]
        logger.debug(f"  Stepping rotor from {prev_pos} to {self.position} (notch at {self.notch})")
        return self.position == self.notch


class Reflector:
    def __init__(self, wiring: str):
        self.wiring = wiring

    def reflect(self, c: str) -> str:
        result = self.wiring[string.ascii_uppercase.index(c)]
        logger.debug(f"  Reflector: {c} -> {result}")
        return result


class Plugboard:
    def __init__(self, swaps: Dict[str, str]):
        self.mapping = {c: c for c in string.ascii_uppercase}
        for a, b in swaps.items():
            self.mapping[a] = b
            self.mapping[b] = a

    def swap(self, c: str) -> str:
        result = self.mapping.get(c, c)
        if c != result:
            logger.debug(f"  Plugboard: {c} -> {result}")
        return result


class EnigmaMachine:
    def __init__(self, rotors: list, reflector: Reflector, plugboard: Plugboard):
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard

    def encode_letter(self, c: str) -> str:
        if c not in string.ascii_uppercase:
            return c

        logger.debug(f"\nEncoding letter: {c}")

        # Step the rotors (right to left)
        rotate_next = self.rotors[-1].step()
        if rotate_next and len(self.rotors) > 1:
            rotate_next = self.rotors[-2].step()
            if rotate_next and len(self.rotors) > 2:
                self.rotors[-3].step()

        # Plugboard in
        c = self.plugboard.swap(c)

        # Forward through rotors
        for rotor in reversed(self.rotors):
            c = rotor.encode_forward(c)

        # Reflect
        c = self.reflector.reflect(c)

        # Backward through rotors
        for rotor in self.rotors:
            c = rotor.encode_backward(c)

        # Plugboard out
        c = self.plugboard.swap(c)

        logger.debug(f"  Final encoded letter: {c}")
        return c

    def encode_message(self, message: str) -> str:
        message = message.upper().replace(' ', '')
        return ''.join(self.encode_letter(c) for c in message)


# Example rotors and reflector
ROTOR_WIRINGS = {
    'I':    ('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),
    'II':   ('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III':  ('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV':   ('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V':    ('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
}

REFLECTOR_B = 'YRUHQSLDPXNGOKMIEBFZCWVJAT'


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    # Setup example
    rotors = [
        Rotor(*ROTOR_WIRINGS['I'], position='A'),
        Rotor(*ROTOR_WIRINGS['II'], position='A'),
        Rotor(*ROTOR_WIRINGS['III'], position='A')
    ]
    reflector = Reflector(REFLECTOR_B)
    plugboard = Plugboard({'A': 'B', 'C': 'D'})

    # Create the machine
    machine = EnigmaMachine(rotors, reflector, plugboard)

    # Encode a message
    encoded = machine.encode_message("HELLOWORLD")
    print("\nEncoded:", encoded)


if __name__ == "__main__":
    main()
