from enigma_crib_cracker import crack_with_crib
from enigma_machine_sim import (
    REFLECTOR_B,
    ROTOR_WIRINGS,
    EnigmaMachine,
    Plugboard,
    Reflector,
    Rotor,
)

rotor_ids = ('I', 'II', 'III')
positions = ('A', 'A', 'A')
plugboard_pairs = {'A': 'B', 'C': 'D'}
reflector = Reflector(REFLECTOR_B)
crib = "HELLO"
message = "HELLOWORLD"


def build_machine():
    rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=positions[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=positions[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=positions[2]),
    ]
    plugboard = Plugboard(plugboard_pairs)
    return EnigmaMachine(rotors, reflector, plugboard)


def test_cracker_finds_correct_settings():
    machine = build_machine()
    ciphertext = machine.encode_message(message)
    matches = crack_with_crib(ciphertext, crib, plugboard_pairs=plugboard_pairs)

    assert any(
        decoded.startswith(crib) and rotor_ids == match[0][0] and positions == match[0][1]
        for match, decoded in matches
    ), "Cracker failed to find the correct rotor config for given crib."
