from ridecast.features import canonical_to_source, source_to_canonical


def test_source_unit_round_trip():
    source = (0.5, 0.55, 0.2)
    assert canonical_to_source(*source_to_canonical(*source)) == source
