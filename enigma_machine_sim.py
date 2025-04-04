import logging
import string
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
        # Adjust for position offset (opposite direction as forward path)
        adjusted_c_idx = (string.ascii_uppercase.index(c) + pos_offset) % 26
        adjusted_c = string.ascii_uppercase[adjusted_c_idx]

        # Find where this letter would be output in the wiring
        wired_idx = self.wiring.find(adjusted_c)

        # Adjust back for position offset
        result_idx = (wired_idx - pos_offset) % 26
        result = string.ascii_uppercase[result_idx]

        logger.debug(
            f"  Rotor {self.wiring[:4]} (bwd): {c} -> {result} [pos {self.position}]"
        )
        return result


    def step(self):
        was_at_notch = self.position == self.notch
        prev_pos = self.position
        self.position = string.ascii_uppercase[(string.ascii_uppercase.index(self.position) + 1) % 26]
        logger.debug(f"  Stepping rotor from {prev_pos} to {self.position} (notch at {self.notch})")
        return was_at_notch

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
        self._initial_positions = [rotor.position for rotor in rotors]
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard

    def encode_letter(self, c: str) -> str:
        if c not in string.ascii_uppercase:
            return c

        logger.debug(f"\nEncoding letter: {c}")

        # Step the rotors (right to left)
        if len(self.rotors) >= 1:
            step_right = self.rotors[-1].step()
        else:
            step_right = False

        if len(self.rotors) >= 2:
            step_middle = self.rotors[-2].step() if step_right else False
        else:
            step_middle = False

        if len(self.rotors) >= 3 and step_middle:
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

    def reset_rotors(self):
        for rotor, initial_pos in zip(self.rotors, self._initial_positions):
            rotor.position = initial_pos

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
    plugboard = Plugboard({"A": "B", "C": "D"})

    # Create the machine
    machine = EnigmaMachine(rotors, reflector, plugboard)

    # Setup example
    rotors_test = [
        Rotor(*ROTOR_WIRINGS["I"], position="A"),
        Rotor(*ROTOR_WIRINGS["II"], position="A"),
        Rotor(*ROTOR_WIRINGS["III"], position="A"),
    ]
    reflector_test = Reflector(REFLECTOR_B)
    plugboard_test = Plugboard({'A': 'B', 'C': 'D'})

    # Create the machine
    machine_test = EnigmaMachine(rotors_test, reflector_test, plugboard_test)

    # Encode a message
    encoded = machine.encode_message("HELLO WORLD")
    print("\nEncoded:", encoded)
    decoded = machine_test.encode_message(encoded)
    print("\nDecoded:", decoded)


if __name__ == "__main__":
    main()
