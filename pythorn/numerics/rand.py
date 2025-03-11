import random


def skew(skew_at=0.6, weight=0.9, minimum=0, maximum=100, is_int=False):
    """
    Generates a random percentage skewed towards `skew_at`.
    The generation has a skew of two points, the first is the declared `skew_at`,
    the second is `(skew_at/2) + (minimum/100)` this second skew is called the
    `mix_skew`.

    The default skew is a skew at 60% with a weight of 90% for a range of 0-100%
    with a return of a float.

    :param skew_at: The point around which values are skewed (0-1).
    :param weight: The probability that values fall below `skew_at` (0-1). If this value is zero, then no skew. If this value is one then it will be heavily skewed, but values beyond `skew_at` are still possible.
    :param minimum: The lowest percent that can be given. (0-100)
    :param maximum: The largest percent that can be given. (0-100)
    :param is_int: Whether to return the random percent as an integer.
    :return: A skewed random percentage within [minimum, maximum].
    """
    if not (0 <= skew_at <= 1):
        raise ValueError("skew_at must be between 0 and 1")
    if not (0 <= weight <= 1):
        raise ValueError("weight must be between 0 and 1")
    if not (0 <= minimum < maximum <= 100):
        raise ValueError("minimum and maximum must satisfy 0 <= minimum < maximum <= 100")

    base_value = random.uniform(0, 1)  # Generate a base random value between 0 and 1

    if skew_at == 0 or skew_at == 1 or weight == 0:
        ret = base_value
    else:
        # Apply a custom transformation to skew the values
        check = random.random()
        skew_weight = (skew_at / weight)
        if check < weight:
            if base_value < minimum / 100:
                base_value = base_value * skew_weight * maximum
            if base_value > skew_at:
                base_value = base_value * skew_weight
        else:
            base_value = 1 - (1 - skew_weight) * (1 - base_value)
        if base_value > 1:
            base_value = skew_at / base_value

        mix_skew = (skew_at / 2) + (minimum / 100)

        if mix_skew < base_value <= skew_at:
            # Spread values more evenly across the skewed range
            # Further reduce clustering with a combination of exponentiation and a secondary random factor
            base_value = mix_skew + ((random.uniform(0, 1) ** 1.1) * (skew_at - mix_skew) * random.uniform(1.3, 1.6))

        ret = base_value

    ret *= maximum
    if is_int:
        ret = int(round(ret))
        minimum = int(minimum)
        maximum = int(maximum)
    if ret < minimum:
        ret = ret / minimum
        ret *= 100
        ret = int(ret)
    return min(max(ret, minimum), maximum)