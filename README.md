# Enigma Machine Simulator

A Python-based simulator for the WWII-era Enigma machine, supporting rotor selection, plugboard configuration, and accurate encryption logic.

## Features
- Authentic simulation of a 3-rotor Enigma machine
- Configurable rotors, plugboard swaps, and reflector
- Accurate rotor stepping and encoding logic
- Support for encode-decode symmetry
- Includes test harness to verify correctness
- Logging support to debug the encoding process

## Usage

### Encoding a message
```python
from enigma_machine_sim import EnigmaMachine, Rotor, Reflector, Plugboard, ROTOR_WIRINGS, REFLECTOR_B

rotors = [
    Rotor(*ROTOR_WIRINGS['I'], position='A'),
    Rotor(*ROTOR_WIRINGS['II'], position='A'),
    Rotor(*ROTOR_WIRINGS['III'], position='A')
]

reflector = Reflector(REFLECTOR_B)
plugboard = Plugboard({'A': 'B', 'C': 'D'})
machine = EnigmaMachine(rotors, reflector, plugboard)

plaintext = "HELLOWORLD"
ciphertext = machine.encode_message(plaintext)
print("Encoded:", ciphertext)

machine.reset_rotors()
decoded = machine.encode_message(ciphertext)
print("Decoded:", decoded)
```

### Cracking a message (with crib)
```python
from enigma_crib_cracker import crack_with_crib

ciphertext = "..."  # Replace with encoded message
crib = "HELLO"
found_matches = crack_with_crib(ciphertext, crib, plugboard_pairs={'A': 'B', 'C': 'D'})
```

### Multithreaded cracking
```python
from enigma_crib_cracker_mt import crack_with_crib_mt

matches = crack_with_crib_mt(ciphertext, crib, plugboard_pairs={'A': 'B', 'C': 'D'})
```

## File Structure
- `enigma_machine_sim.py`: Main simulation logic
- `enigma_crib_cracker.py`: Single-threaded Enigma cracker using known crib
- `enigma_crib_cracker_mt.py`: Multithreaded version for faster cracking

## Requirements
- Python 3.7+
- tqdm (for progress bars)

## License
This project is for educational and non-commercial use.

---

Built to explore historical cryptography and test cracking techniques used during WWII.
