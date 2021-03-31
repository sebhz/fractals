#!/usr/bin/python3
"""
Ancillary functions used for attractor generation and rendering.
"""
import logging
import random
import math
import operator

MODULUS = lambda p: sum([v * v for v in p])
SQ_DIST = lambda p1, p2: MODULUS([v[1] - v[0] for v in zip(p1, p2)])
OVERITERATE_FACTOR = 32


def get_ideal_iteration_number(geometry, subsampling_rate=1):
    """
    Computes the number of iterations necessary to have the attractor
    "look good", when rendered.

    Arguments:
        attractor_type: type of the attractor. Now unused.
        geometry: a (w,h) tuple giving the final picture width and height in pixels
        subsampling_rate: the subsampling rate (usually 1, 2 or 3)

    Returns the correct number of iteration to have the attractor look reasonably good.
    """

    px_size = subsampling_rate * subsampling_rate * geometry[0] * geometry[1]
    return int(OVERITERATE_FACTOR * px_size)


def scale_bounds(bounding_box, window_dim, pct=0.05):
    """
    Pads and enlarges a window to center it in a larger window whose aspect ratio is given.

    Arguments:
        bounding_box: the window to scale, as a (x0, y0, z0, x1, y1, z1) tuple.
            x0, y0 are the coordinates of the bottom left point
            x1, y1 are the coordinates of the top right point
        window_dim: the window dimension, as a (w, h) tuple
            w and h are respectively the width and height of the screen
        pct: the percentage of padding to be applied in both direction

    Returns a tuple (X0, Y0, X1, Y1) representing bounding_box padded by pct % in
    both directions, enlarged to have the same aspect ratio as window_dim, so that
    the original bounding box is now centered in the new window.
    """
    hoff = (bounding_box[4] - bounding_box[1]) * float(pct) / 2
    woff = (bounding_box[3] - bounding_box[0]) * float(pct) / 2
    # Enlarge our bb by pct %
    new_bounding_box = (
        bounding_box[0] - woff,
        bounding_box[1] - hoff,
        bounding_box[3] + woff,
        bounding_box[4] + hoff,
    )

    b_ar = (new_bounding_box[3] - new_bounding_box[1]) / (
        new_bounding_box[2] - new_bounding_box[0]
    )  # New bb aspect ratio
    # Window aspect ratio
    s_ar = window_dim[1] / window_dim[0]

    try:
        ratio = s_ar / b_ar
    except ZeroDivisionError as exception:
        logging.debug("Exception caught when enlarging window")
        logging.debug(
            "Bounding box: %s - window: %s - hoff: %f - woff: %f - \
                       new_bounding_box: %s - b_ar: %f",
            str(bounding_box),
            str(window_dim),
            hoff,
            woff,
            str(new_bounding_box),
            b_ar,
        )
        raise exception

    if (
        b_ar < s_ar
    ):  # Enlarge bb height to get the right AR - keep it centered vertically
        yoff = (new_bounding_box[3] - new_bounding_box[1]) * (ratio - 1) / 2
        return (
            new_bounding_box[0],
            new_bounding_box[1] - yoff,
            new_bounding_box[2],
            new_bounding_box[3] + yoff,
        )
    if (
        b_ar > s_ar
    ):  # Enlarge window width to get the right AR - keep it centered horizontally
        xoff = (new_bounding_box[2] - new_bounding_box[0]) * (1 / ratio - 1) / 2
        return (
            new_bounding_box[0] - xoff,
            new_bounding_box[1],
            new_bounding_box[2] + xoff,
            new_bounding_box[3],
        )

    # Nothing to do. Return our enlarged bb
    return new_bounding_box


def linear_reg(x, y):
    """
    Good old linear regresssion formula.
    Yes I know, numpy, etc...
    """
    n_samples = len(x)
    sum_xy = sum([v[0] * v[1] for v in zip(x, y)])
    sum_x2 = sum(map(lambda v: v ** 2, x))
    sum_y2 = sum(map(lambda v: v ** 2, y))
    sum_x = sum(x)
    sum_y = sum(y)

    slope = (n_samples * sum_xy - sum_x * sum_y) / (n_samples * sum_x2 - sum_x * sum_x)
    rsquare = slope * math.sqrt(
        (n_samples * sum_x2 - sum_x * sum_x) / (n_samples * sum_y2 - sum_y * sum_y)
    )

    return (slope, rsquare)


def box_count(att_map, origin, box_side):
    """
    Get a dict of boxes of side box_side pixels needed
    to cover the attractor map att_map.
    att_map is a frequency map, indexed by pixel (x, y, z) tuples
    """
    boxes = dict()
    for point in att_map.keys():
        box_c = tuple(
            [
                int((coord_pt - coord_origin) / box_side)
                for coord_pt, coord_origin in zip(point, origin)
            ]
        )
        boxes[box_c] = True
    return boxes


def get_attractor_bounding_box(att):
    """
    Get an attractor map bounding box
    [min coordinate] + [max_coordinate] of the cube
    needed to enclose an attractor, in a cryptic
    pythonic way
    """
    att_points = list(att.keys())
    att_dim = len(att_points[0])  # Attractor dimension - always 2 in current version

    bounding_box = [
        [f(att_points, key=operator.itemgetter(i))[i] for i in range(0, att_dim)]
        for f in (min, max)
    ]

    return bounding_box


def compute_box_counting_dimension(att, scaling_factor=1.5):
    """
    Computes an estimate of the Minkowski-Bouligand dimension (a.k.a box-counting)
    See https://en.wikipedia.org/wiki/Minkowski%E2%80%93Bouligand_dimension

    Algorithm:
        - Use cubic boxes
        - Start with boxes whose side S = bounding_box_diagonal/4
        - Until S < bounding_box_diagonal/256
            {
            * Choose a random origin inside the bounding box
            * Compute the number of boxes needed to cover the attractor (aligned on the origin)
            }
            In theory this should be done several time varying orientation and origin of
            the boxes, and we should get the minimum. We just take one box count for performance
            Store S, N
            S = S/scaling_factor
        - Perform a linear regression log(N), log(1/S). The slope is the dimension
    """
    bounding_box = get_attractor_bounding_box(att)
    diagonal = math.sqrt(SQ_DIST(*bounding_box))
    divider = 4
    box_count_trials = 1
    (log_n, log_invs) = (list(), list())
    logging.debug("Starting box-counting dimension computation.")
    while divider < 256:
        box_side = diagonal / divider
        min_num_boxes = len(att.keys())
        for _ in range(0, box_count_trials):  # Do something n times...
            origin = [
                random.randint(bounding_box[0][i], bounding_box[1][i])
                for i in range(0, len(bounding_box[0]))
            ]
            boxes = box_count(att, origin, box_side)
            min_num_boxes = min(min_num_boxes, len(boxes))
        log_n.append(math.log(min_num_boxes))
        log_invs.append(math.log(1 / box_side))
        divider *= scaling_factor
    try:
        (slope, rsquare) = linear_reg(log_invs, log_n)
        logging.debug("Box-counting dimension: %.3f (rsquare: %.2f)", slope, rsquare)
        return slope
    except ValueError:
        logging.error(
            "Math error when trying to compute box-counting dimension. Setting it to 0."
        )
        return 0.0


def compute_correlation_dimension(att):
    """
    Computes an estimate of the correlation dimension "a la Julien Sprott"
    Estimates the probability that 2 points in the attractor are close enough
    """
    base = 10
    radius_ratio = 0.001
    diagonal2 = SQ_DIST(*get_attractor_bounding_box(att))
    d_1 = 4 * radius_ratio * diagonal2
    d_2 = float(d_1) / base / base
    n_1, n_2 = (0, 0)
    points = list(att.keys())
    num_points = len(points)

    for point in points:  # Iterate on each attractor point
        other_point = points[
            random.randint(0, num_points - 1)
        ]  # Pick another point at random
        sq_dist = SQ_DIST(point, other_point)
        if sq_dist == 0:
            continue  # Oops we picked the same point twice
        if sq_dist < d_1:
            n_2 += 1  # Distance within a big circle
        if sq_dist > d_2:
            continue  # But out of a small circle
        n_1 += 1

    try:
        return math.log(float(n_2) / n_1, base)
    except ZeroDivisionError:
        logging.error("Math error when trying to compute dimension. Setting it to 0.")
        return 0.0  # Impossible to find small circles... very scattered points


def compute_true_correlation_dimension(att, max_points=4096):
    """
    Computes an estimate of the correlation dimension with the naive
    algorithm. See https://en.wikipedia.org/wiki/Correlation_dimension
    VERY inefficient and time consuming -> O(N²)
    """
    points = list(att.keys())
    diagonal2 = SQ_DIST(*get_attractor_bounding_box(att))

    bins_epsilon2 = [diagonal2 / x / x for x in (4, 8, 16, 32, 64, 128, 256, 512)]
    bins = {epsilon2: 0 for epsilon2 in bins_epsilon2}

    num_points = min(max_points, len(points))
    logging.debug(
        "Starting true correlation dimension computation on %d points.", num_points
    )

    for i in range(0, num_points - 1):
        p_1 = points[i]
        for j in range(i + 1, num_points):
            p_2 = points[j]
            d_2 = SQ_DIST(p_1, p_2)
            for epsilon2 in bins_epsilon2:
                if d_2 < epsilon2:
                    bins[epsilon2] += 1

    bins_log = dict()
    for epsilon2, freq in bins.items():
        try:
            bins_log[math.log(math.sqrt(epsilon2))] = math.log(
                freq / num_points / num_points
            )
        except ValueError:
            pass  # if a bin is empty

    (slope, rsquare) = linear_reg(list(bins_log.keys()), list(bins_log.values()))
    logging.debug("Correlation dimension: %.3f (rsquare: %.2f)", slope, rsquare)

    return slope
