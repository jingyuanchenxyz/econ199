def normalize_coefficients(a, b, c, q):
    """ Normalize line coefficients to the smallest equivalent form under field properties. """
    if a == 0 and b == 0:
        return None  # not good line
    if a == 0:
        # vertical line, normalize by 'b'
        inv = pow(b, q-2, q)  # multiplicative inverse modulo q
        return (0, 1, (c * inv) % q)
    # normalize by 'a'
    inv = pow(a, q-2, q)
    return (1, (b * inv) % q, (c * inv) % q)

def count_distinct_lines(q):
    lines = set()
    for a in range(q):
        for b in range(q):
            for c in range(q):
                if a == 0 and b == 0:
                    continue  # skip invalid line
                norm_line = normalize_coefficients(a, b, c, q)
                if norm_line:
                    lines.add(norm_line)
    return len(lines)

#test cases 
for q in [2, 3, 4, 5, 7, 8, 10, 11, 13, 16, 17, 19, 23, 29, 31, 50]:
    num_lines = count_distinct_lines(q)
    expected_lines = q**2 + q
    print(f"Distinct lines in AG(2, {q}): {num_lines} (Computed), {expected_lines} (Expected)")



def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def normalize_slope(a, b, q):
    if b == 0:
        return (1, 0)  # all vertical lines normalized to this slope
    # normalize by finding the smallest k that makes ka or kb == 1 mod q
    inv_b = pow(b, q-2, q)  # Using Fermat's Little Theorem to find the inverse of b mod q
    normalized_a = (a * inv_b) % q
    return (normalized_a, 1)

def distinct_lines_and_parallel_classes_in_AG2q(q):
    parallel_classes = {}

    for a in range(q):
        for b in range(q):
            if a == 0 and b == 0:
                continue
            normalized_slope = normalize_slope(a, b, q)
            if normalized_slope not in parallel_classes:
                parallel_classes[normalized_slope] = set()

            for c in range(q):
                parallel_classes[normalized_slope].add(c)  # Just storing c as lines

    print(f"Total parallel classes: {len(parallel_classes)} (Expected: {q + 1})")
    for slope, cs in parallel_classes.items():
        print(f"Slope {slope}: {len(cs)} lines (Expected: {q})")
        assert len(cs) == q, f"Class for slope {slope} does not have exactly {q} lines"

    return len(parallel_classes), sum(len(cs) for cs in parallel_classes.values())

#test cases
for q in [2, 3, 4, 5, 7, 8, 10, 11, 13, 16, 17, 19, 23, 29, 31, 50]:
    classes, num_lines = distinct_lines_and_parallel_classes_in_AG2q(q)
    expected_lines = q**2 + q
    print(f"For q = {q}: Total distinct lines = {num_lines} (Computed), {expected_lines} (Expected)")

