from enigma_machine_sim import EnigmaMachine, Rotor, Reflector, Plugboard, ROTOR_WIRINGS, REFLECTOR_B
import string
import itertools
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# Crib-cracking utility for Enigma

def crack_with_crib(ciphertext, crib, plugboard_pairs=None):
    crib = crib.upper()
    ciphertext = ciphertext.upper()

    # Generate all rotor order permutations (5 choose 3, ordered)
    rotor_orders = list(itertools.permutations(ROTOR_WIRINGS.keys(), 3))

    # Create all rotor starting positions (17,576 total)
    positions = [a + b + c for a in string.ascii_uppercase
                             for b in string.ascii_uppercase
                             for c in string.ascii_uppercase]

    reflector = Reflector(REFLECTOR_B)
    found = []
    total_combinations = len(rotor_orders) * len(positions)

    logger.info(f"Total combinations to try: {total_combinations}")

    for rotor_ids in tqdm(rotor_orders, desc="Rotor Orders"):
        for pos in positions:
            # Setup rotors fresh each time
            rotors = [
                Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=pos[0]),
                Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=pos[1]),
                Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=pos[2]),
            ]

            plugboard = Plugboard(plugboard_pairs or {})
            machine = EnigmaMachine(rotors, reflector, plugboard)
            decoded = machine.encode_message(ciphertext)

            # Debug: check for any character mapping to itself
            for original, transformed in zip(ciphertext, decoded):
                if original == transformed:
                    logger.debug(f"[Warning] Self-mapping detected: {original} -> {transformed} at rotor setting {rotor_ids} pos {pos}")

            # Check segments of decoded message for crib match
            for i in range(len(decoded) - len(crib) + 1):
                segment = decoded[i:i+len(crib)]
                if crib == segment:
                    # Enigma can't map a letter to itself: check ciphertext vs crib at same position
                    if all(ciphertext[i + j] != crib[j] for j in range(len(crib))):
                        found.append(((rotor_ids, pos), decoded))
                        logger.info(f"[Match] Rotors: {rotor_ids}, Pos: {pos}, Decoded: {decoded}")
                        break
                    else:
                        logger.debug(f"[Skip] Self-reflection at pos {i}: crib={crib}, ct segment={ciphertext[i:i+len(crib)]}")

    # Save all matches to a file
    with open("decoded_matches.txt", "w") as f:
        for (rotor_ids, pos), decoded in found:
            f.write(f"Rotors: {rotor_ids}, Position: {pos}, Decoded: {decoded}\n")

    return found


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    plugboard_settings = {'A': 'B', 'C': 'D'}
    plaintext = "HELLOWORLD"

    # Generate known-good ciphertext
    test_rotors = [
        Rotor(*ROTOR_WIRINGS['I'], position='A'),
        Rotor(*ROTOR_WIRINGS['II'], position='A'),
        Rotor(*ROTOR_WIRINGS['III'], position='A')
    ]
    test_reflector = Reflector(REFLECTOR_B)
    test_plugboard = Plugboard(plugboard_settings)
    test_machine = EnigmaMachine(test_rotors, test_reflector, test_plugboard)
    ciphertext = test_machine.encode_message(plaintext)
    print("Generated Ciphertext:", ciphertext)

    crib = "HELLO"
    matches = crack_with_crib(ciphertext, crib, plugboard_settings)

    for (rotor_ids, pos), decoded in matches:
        print(f"Match at rotors {rotor_ids} with position {pos}: {decoded}")
