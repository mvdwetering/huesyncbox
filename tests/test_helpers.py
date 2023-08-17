from custom_components.huesyncbox.helpers import (
    LinearRangeConverter,
    get_group_from_area_name,
)


def test_linear_range_converter():
    lrc = LinearRangeConverter([-1, 1], [-11, 11])
    assert lrc.to_x(-11) == -1
    assert lrc.to_x(11) == 1
    assert lrc.to_x(0) == 0
    assert lrc.to_y(-1) == -11
    assert lrc.to_y(1) == 11
    assert lrc.to_y(0) == 0


def test_group_from_area_name(mock_api):
    assert get_group_from_area_name(mock_api, "does not exist") is None

    group = get_group_from_area_name(mock_api, "Name 1")
    assert group.id == "id1"
