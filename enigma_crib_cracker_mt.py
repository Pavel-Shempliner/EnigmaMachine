from enigma_machine_sim import EnigmaMachine, Rotor, Reflector, Plugboard, ROTOR_WIRINGS, REFLECTOR_B
import string
import itertools
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

logger = logging.getLogger(__name__)

def crack_chunk(rotor_ids, positions, ciphertext, crib, plugboard_pairs):
    reflector = Reflector(REFLECTOR_B)
    found = []

    for pos in positions:
        rotors = [
            Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=pos[0]),
            Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=pos[1]),
            Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=pos[2]),
        ]
        plugboard = Plugboard(plugboard_pairs or {})
        machine = EnigmaMachine(rotors, reflector, plugboard)
        decoded = machine.encode_message(ciphertext)

        for i in range(len(decoded) - len(crib) + 1):
            segment = decoded[i:i+len(crib)]
            if crib == segment:
                if all(ciphertext[i + j] != crib[j] for j in range(len(crib))):
                    found.append(((rotor_ids, pos), decoded))
                    break
    return found

def crack_with_crib_mt(ciphertext, crib, plugboard_pairs=None):
    crib = crib.upper()
    ciphertext = ciphertext.upper()

    rotor_orders = list(itertools.permutations(ROTOR_WIRINGS.keys(), 3))
    positions = [a + b + c for a in string.ascii_uppercase for b in string.ascii_uppercase for c in string.ascii_uppercase]

    logger.info(f"Total combinations to try: {len(rotor_orders) * len(positions)}")

    num_threads = cpu_count()
    logger.info(f"Using {num_threads} threads")

    chunk_size = len(positions) // num_threads
    found = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for rotor_ids in rotor_orders:
            for i in range(0, len(positions), chunk_size):
                chunk = positions[i:i+chunk_size]
                futures.append(executor.submit(crack_chunk, rotor_ids, chunk, ciphertext, crib, plugboard_pairs))

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
            result = future.result()
            if result:
                found.extend(result)

    # with open("decoded_matches_mt.txt", "w") as f:
    #     for (rotor_ids, pos), decoded in found:
    #         f.write(f"Rotors: {rotor_ids}, Position: {pos}, Decoded: {decoded}\n")

    return found


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    plugboard_settings = {'A': 'B', 'C': 'D'}
    plaintext = "HELLO WORLD"
    print(f"{plaintext=}")

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
    test_machine.reset_rotors()
    print(f"Decrypted message - {test_machine.encode_message(ciphertext)}")

    crib = "HELLO"
    matches = crack_with_crib_mt(ciphertext, crib, plugboard_settings)

    for (rotor_ids, pos), decoded in matches:
        print(f"Match at rotors {rotor_ids} with position {pos}: {decoded}")
