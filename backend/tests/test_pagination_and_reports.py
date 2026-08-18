from datetime import date, timedelta


def create_clients(client, admin_headers, n, start_date=None):
    for i in range(n):
        client.post(
            "/clients",
            json={
                "corporate_name": f"Cliente Paginação {i:02d} LTDA",
                "status": "ativo",
                "relationship_start_date": start_date.isoformat() if start_date else None,
            },
            headers=admin_headers,
        )


def test_clients_list_is_paginated(client, admin_headers):
    create_clients(client, admin_headers, 30)

    page1 = client.get("/clients?page=1&page_size=25", headers=admin_headers).json()
    assert page1["total"] == 30
    assert len(page1["items"]) == 25
    assert page1["page"] == 1

    page2 = client.get("/clients?page=2&page_size=25", headers=admin_headers).json()
    assert len(page2["items"]) == 5

    ids_page1 = {c["id"] for c in page1["items"]}
    ids_page2 = {c["id"] for c in page2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


def test_report_date_filter_excludes_out_of_range_clients(client, admin_headers):
    in_range = date(2026, 3, 15)
    out_of_range = date(2026, 6, 15)
    create_clients(client, admin_headers, 1, start_date=in_range)
    create_clients(client, admin_headers, 1, start_date=out_of_range)

    res = client.get("/reports/carteira.csv?start_date=2026-03-01&end_date=2026-03-31", headers=admin_headers)
    assert res.status_code == 200
    lines = [line for line in res.text.strip().split("\n") if line]
    assert len(lines) == 2  # header + 1 cliente dentro do período


def test_report_without_date_filter_returns_all(client, admin_headers):
    create_clients(client, admin_headers, 3, start_date=date(2026, 1, 1))

    res = client.get("/reports/carteira.csv", headers=admin_headers)
    lines = [line for line in res.text.strip().split("\n") if line]
    assert len(lines) == 4  # header + 3 clientes
