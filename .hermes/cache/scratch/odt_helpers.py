"""ODT XML builder helpers for the Projeto Aplicado IV rewrite."""

def esc(s):
    """Escape text for XML body, but don't double-escape already-escaped entities."""
    if s is None:
        return ""
    # Use regex with negative lookahead: don't escape & if it's already part of an entity
    import re as _re
    s = _re.sub(r'&(?![a-zA-Z]+;)', '&amp;', s)
    s = s.replace('<', '&lt;').replace('>', '&gt;')
    return s


def para(text, style="Text_20_body"):
    return '<text:p text:style-name="{s}">{t}</text:p>'.format(s=style, t=text)


def h1(text):
    return '<text:h text:style-name="Heading_20_1" text:outline-level="1">{t}</text:h>'.format(t=esc(text))


def h2(text):
    return '<text:h text:style-name="Heading_20_2" text:outline-level="2">{t}</text:h>'.format(t=esc(text))


def h3(text):
    return '<text:h text:style-name="Heading_20_3" text:outline-level="3">{t}</text:h>'.format(t=esc(text))


def h4(text):
    return '<text:h text:style-name="Heading_20_4" text:outline-level="4">{t}</text:h>'.format(t=esc(text))


def bullets(items):
    # Caller is responsible for escaping text — items may contain raw XML markup
    items_xml = "".join(
        '<text:list-item><text:p text:style-name="List_20_Bullet">{x}</text:p></text:list-item>'.format(x=x)
        for x in items
    )
    return '<text:list text:style-name="List_20_Bullet">{body}</text:list>'.format(body=items_xml)


def numbered(items):
    # Caller is responsible for escaping text — items may contain raw XML markup
    items_xml = "".join(
        '<text:list-item><text:p text:style-name="List_20_Paragraph">{x}</text:p></text:list-item>'.format(x=x)
        for x in items
    )
    return '<text:list text:style-name="List_20_Paragraph">{body}</text:list>'.format(body=items_xml)


def table(header_cols, rows_data):
    """Build an ODT table.

    header_cols: list of header text strings.
    rows_data:   list of rows, each a list of cell text strings.
    """
    n = len(header_cols)
    h_cells = "".join(
        '<table:table-cell table:style-name="Table_20_Heading">'
        '<text:p text:style-name="Table_20_Heading">'
        '<text:span text:style-name="Strong">{c}</text:span>'
        '</text:p></table:table-cell>'.format(c=esc(c))
        for c in header_cols
    )
    body_rows = ""
    for row_data in rows_data:
        r_cells = "".join(
            '<table:table-cell table:style-name="Table_20_Contents">'
            '<text:p text:style-name="Table_20_Contents">{c}</text:p>'
            '</table:table-cell>'.format(c=esc(c))
            for c in row_data
        )
        body_rows += '<table:table-row>{cells}</table:table-row>'.format(cells=r_cells)
    return (
        '<table:table table:style-name="Table_20_Contents">'
        '<table:table-column table:style-name="Table_20_Contents" table:number-columns-repeated="{n}"/>'
        '<table:table-header-row>{h}</table:table-header-row>'
        '{body}'
        '</table:table>'
    ).format(n=n, h=h_cells, body=body_rows)