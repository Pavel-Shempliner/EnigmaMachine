import itertools
import logging
import string
import random
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

from enigma_machine_sim import (
    REFLECTOR_B,
    ROTOR_WIRINGS,
    EnigmaMachine,
    Plugboard,
    Reflector,
    Rotor,
)
from tqdm import tqdm

logger = logging.getLogger(__name__)


def random_initial_plugboard(num_pairs):
    """
    Generate a random plugboard configuration with the specified number of pairs.
    (num_pairs * 2 letters will be paired, the remaining letters stay unpaired.)
    """
    letters = list(string.ascii_uppercase)
    random.shuffle(letters)
    plugboard = {}
    for i in range(num_pairs):
        a = letters[2 * i]
        b = letters[2 * i + 1]
        plugboard[a] = b
        plugboard[b] = a
    return plugboard


def decrypt_message(ciphertext, rotor_ids, rotor_position, plugboard_config):
    """
    Decrypt the ciphertext using the specified rotor order, rotor starting positions,
    and plugboard configuration.
    """
    reflector = Reflector(REFLECTOR_B)
    rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids[0]], position=rotor_position[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[1]], position=rotor_position[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids[2]], position=rotor_position[2]),
    ]
    machine = EnigmaMachine(rotors, reflector, Plugboard(plugboard_config))
    return machine.encode_message(ciphertext)


def score_text(text, crib):
    """
    A simple scoring function that gives a bonus if the crib is found and
    rewards "English-like" text (here, crudely measured by vowel frequency).
    """
    score = 0
    if crib in text:
        score += 1000  # Crib bonus
    vowels = "AEIOU"
    score += sum(text.count(v) for v in vowels)
    return score


def generate_neighbor(plugboard):
    """
    Generate a neighboring plugboard configuration by swapping letters between two pairs.
    The plugboard is a dict mapping letters to their partner.
    """
    # Extract pairs (each pair appears once)
    pairs = []
    seen = set()
    for k, v in plugboard.items():
        if k not in seen:
            pairs.append((k, v))
            seen.add(k)
            seen.add(v)
    # If we don't have at least two pairs, no swap can be done.
    if len(pairs) < 2:
        return plugboard

    p1, p2 = random.sample(pairs, 2)
    # Choose one of two swap strategies.
    if random.random() < 0.5:
        new_pair1 = (p1[0], p2[0])
        new_pair2 = (p1[1], p2[1])
    else:
        new_pair1 = (p1[0], p2[1])
        new_pair2 = (p1[1], p2[0])
    # Prevent self-mappings.
    if new_pair1[0] == new_pair1[1] or new_pair2[0] == new_pair2[1]:
        return plugboard

    new_plugboard = plugboard.copy()
    # Remove the old mappings.
    for a, b in [p1, p2]:
        new_plugboard.pop(a, None)
        new_plugboard.pop(b, None)
    # Insert the new pairs (bidirectionally).
    new_plugboard[new_pair1[0]] = new_pair1[1]
    new_plugboard[new_pair1[1]] = new_pair1[0]
    new_plugboard[new_pair2[0]] = new_pair2[1]
    new_plugboard[new_pair2[1]] = new_pair2[0]
    return new_plugboard


def simulated_annealing_plugboard_search(
    ciphertext,
    crib,
    rotor_ids,
    rotor_position,
    initial_plugboard,
    num_iterations=10000,
    start_temp=10.0,
    cooling_rate=0.0001,
):
    """
    Given a rotor candidate (order and starting positions), use simulated annealing to search
    for a plugboard configuration that yields a decryption containing the crib.
    """
    current_plugboard = initial_plugboard
    current_decryption = decrypt_message(
        ciphertext, rotor_ids, rotor_position, current_plugboard
    )
    current_score = score_text(current_decryption, crib)
    best_plugboard = current_plugboard
    best_score = current_score
    temp = start_temp

    for iteration in range(num_iterations):
        neighbor = generate_neighbor(current_plugboard)
        neighbor_decryption = decrypt_message(
            ciphertext, rotor_ids, rotor_position, neighbor
        )
        neighbor_score = score_text(neighbor_decryption, crib)
        delta = neighbor_score - current_score

        # Accept the neighbor if it improves the score or with a probability
        if delta > 0 or random.random() < math.exp(delta / temp):
            current_plugboard = neighbor
            current_score = neighbor_score

        if current_score > best_score:
            best_plugboard = current_plugboard
            best_score = current_score

        temp *= 1 - cooling_rate
        # Optional early exit if the crib is already found.
        if crib in decrypt_message(
            ciphertext, rotor_ids, rotor_position, best_plugboard
        ):
            break

    return best_plugboard, best_score


def search_rotor_candidate(
    ciphertext,
    crib,
    rotor_ids,
    rotor_position,
    num_plugboard_pairs,
    num_iterations,
    start_temp,
    cooling_rate,
):
    """
    For a given rotor candidate (order and positions), perform plugboard search via simulated annealing.
    Returns the candidate settings and decryption if the crib is found.
    """
    initial_plugboard = random_initial_plugboard(num_plugboard_pairs)
    best_plugboard, best_score = simulated_annealing_plugboard_search(
        ciphertext,
        crib,
        rotor_ids,
        rotor_position,
        initial_plugboard,
        num_iterations,
        start_temp,
        cooling_rate,
    )
    decrypted = decrypt_message(ciphertext, rotor_ids, rotor_position, best_plugboard)
    if crib in decrypted:
        return ((rotor_ids, rotor_position, best_plugboard), decrypted)
    return None


def crack_with_crib_rotor_plugboard_mt(
    ciphertext,
    crib,
    num_plugboard_pairs=1,
    num_iterations=10000,
    start_temp=10.0,
    cooling_rate=0.0001,
    limit_positions=None,
):
    """
    Combined multithreaded rotor/position search with plugboard optimization.

    Parameters:
      - ciphertext: The ciphertext to be decrypted.
      - crib: Known plaintext fragment.
      - num_plugboard_pairs: Number of plugboard pairs to search (affects candidate space).
      - num_iterations, start_temp, cooling_rate: Parameters for simulated annealing.
      - limit_positions: (Optional) Limit on the number of rotor positions to test (for demo purposes).

    Returns:
      A list of candidate settings (rotor order, starting positions, plugboard config) that yield a decryption
      containing the crib.
    """
    crib = crib.upper()
    ciphertext = ciphertext.upper()

    # Generate all rotor orders (usually 3 rotors selected from available ones)
    rotor_orders = list(itertools.permutations(ROTOR_WIRINGS.keys(), 3))
    # Full rotor positions search space (26^3 possibilities)
    all_positions = [
        a + b + c
        for a in string.ascii_uppercase
        for b in string.ascii_uppercase
        for c in string.ascii_uppercase
    ]
    # Optionally, limit the number of positions for demonstration purposes.
    if limit_positions is not None and limit_positions < len(all_positions):
        positions = random.sample(all_positions, limit_positions)
    else:
        positions = all_positions

    num_threads = cpu_count()
    results = []
    futures = []
    with ProcessPoolExecutor(max_workers=num_threads) as executor:
        for rotor_ids in rotor_orders:
            for pos in positions:
                futures.append(
                    executor.submit(
                        search_rotor_candidate,
                        ciphertext,
                        crib,
                        rotor_ids,
                        pos,
                        num_plugboard_pairs,
                        num_iterations,
                        start_temp,
                        cooling_rate,
                    )
                )
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing"
        ):
            result = future.result()
            if result is not None:
                results.append(result)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # For demonstration, set up a known Enigma configuration.
    rotor_ids_true = ("I", "II", "III")
    rotor_position_true = "AAA"
    true_plugboard = {"A": "B", "B": "A", "C": "D", "D": "C"}
    plaintext = "HELLOWORLD"

    test_rotors = [
        Rotor(*ROTOR_WIRINGS[rotor_ids_true[0]], position=rotor_position_true[0]),
        Rotor(*ROTOR_WIRINGS[rotor_ids_true[1]], position=rotor_position_true[1]),
        Rotor(*ROTOR_WIRINGS[rotor_ids_true[2]], position=rotor_position_true[2]),
    ]
    test_reflector = Reflector(REFLECTOR_B)
    test_plugboard = Plugboard(true_plugboard)
    test_machine = EnigmaMachine(test_rotors, test_reflector, test_plugboard)
    ciphertext = test_machine.encode_message(plaintext)
    print("Generated Ciphertext:", ciphertext)

    crib = "HELLO"
    # For demo purposes, limit the number of positions to test.
    results = crack_with_crib_rotor_plugboard_mt(
        ciphertext,
        crib,
        num_plugboard_pairs=1,
        num_iterations=5000,
        start_temp=10.0,
        cooling_rate=0.0001,
        limit_positions=100,  # Restrict positions for a quicker demo
    )

    for ((rotor_ids, pos, plugboard), decrypted) in results:
        print(f"Match found: Rotors: {rotor_ids}, Position: {pos}, Plugboard: {plugboard}, Decrypted: {decrypted}")
