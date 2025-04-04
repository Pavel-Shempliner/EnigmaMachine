import pytest
from enigma_machine_sim import EnigmaMachine, Rotor, Reflector, Plugboard, ROTOR_WIRINGS, REFLECTOR_B

rotor_ids = ('I', 'II', 'III')
positions = ('A', 'A', 'A')
plugboard_pairs = {'A': 'B', 'C': 'D'}
reflector = Reflector(REFLECTOR_B)
message = "HELLOWORLD"

def build_machine(pos):
    rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=pos[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=pos[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=pos[2])
    ]
    plugboard = Plugboard(plugboard_pairs)
    return EnigmaMachine(rotors, reflector, plugboard)

def test_encode_decode_cycle():
    machine = build_machine(positions)
    encoded = machine.encode_message(message)
    machine.reset_rotors()
    decoded = machine.encode_message(encoded)
    assert decoded == message

def test_self_mapping():
    machine = build_machine(positions)
    encoded = machine.encode_message(message)
    for i, c in enumerate(message):
        assert c != encoded[i], f"Self-mapping occurred at index {i}: {c} -> {encoded[i]}"

def test_repeatability():
    machine1 = build_machine(positions)
    machine2 = build_machine(positions)
    out1 = machine1.encode_message(message)
    out2 = machine2.encode_message(message)
    assert out1 == out2, "Same configuration should produce same output"
