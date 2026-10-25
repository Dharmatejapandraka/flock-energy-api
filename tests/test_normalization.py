from app.normalization import clean_value, parse_html_tables

def test_clean_value_normalizes_simple_values():
    assert clean_value(" 124.50 ") == 124.5
    assert clean_value("17") == 17
    assert clean_value(" yes ") is True
    assert clean_value("   ") is None
    assert clean_value("MTR-001") == "MTR-001"

def test_parse_html_table():
    html = """
    <html><body><table>
      <tr><th>Meter ID</th><th>Consumption</th></tr>
      <tr><td>MTR-001</td><td>124.50</td></tr>
    </table></body></html>
    """
    assert parse_html_tables(html) == [{"Meter ID": "MTR-001", "Consumption": 124.5}]
