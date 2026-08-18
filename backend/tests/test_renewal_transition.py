from datetime import date, timedelta


def create_client(client, admin_headers, status="ativo"):
    res = client.post(
        "/clients",
        json={"corporate_name": "Cliente Teste Renovação LTDA", "status": status},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def create_renewal(client, admin_headers, client_id, days_ahead=30, value=50000):
    end_date = (date.today() + timedelta(days=days_ahead)).isoformat()
    res = client.post(
        f"/clients/{client_id}/renewals",
        json={"contract_end_date": end_date, "renewal_value": value},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_renewal_propagates_date_to_client(client, admin_headers):
    created = create_client(client, admin_headers)
    renewal = create_renewal(client, admin_headers, created["id"], days_ahead=45)

    client_after = client.get(f"/clients/{created['id']}", headers=admin_headers)
    assert client_after.json()["renewal_date"] == renewal["contract_end_date"]


def test_complete_renewal_renewed_reactivates_client(client, admin_headers):
    created = create_client(client, admin_headers, status="em_risco")
    renewal = create_renewal(client, admin_headers, created["id"])

    next_end_date = (date.today() + timedelta(days=365)).isoformat()
    res = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": True, "next_contract_end_date": next_end_date},
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "renovado"

    client_after = client.get(f"/clients/{created['id']}", headers=admin_headers).json()
    assert client_after["status"] == "ativo"
    assert client_after["renewal_date"] == next_end_date


def test_complete_renewal_not_renewed_churns_client_and_creates_record(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]
    renewal = create_renewal(client, admin_headers, client_id, value=80000)

    res = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": False, "churn_category": "preco", "churn_description": "Cliente achou caro"},
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "nao_renovado"

    client_after = client.get(f"/clients/{client_id}", headers=admin_headers).json()
    assert client_after["status"] == "churn"
    assert client_after["renewal_date"] is None  # não deve mais disparar alerta de renovação

    churn_records = client.get("/churn-records", headers=admin_headers).json()
    matching = [c for c in churn_records["items"] if c["client_id"] == client_id]
    assert len(matching) == 1
    assert matching[0]["category"] == "preco"
    assert matching[0]["lost_value"] == 80000
    assert matching[0]["renewal_id"] == renewal["id"]


def test_complete_renewal_twice_fails(client, admin_headers):
    created = create_client(client, admin_headers)
    renewal = create_renewal(client, admin_headers, created["id"])

    first = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": False, "churn_category": "outro"},
        headers=admin_headers,
    )
    assert first.status_code == 200

    second = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": False, "churn_category": "outro"},
        headers=admin_headers,
    )
    assert second.status_code == 400


def test_complete_renewal_renewed_without_next_date_fails(client, admin_headers):
    created = create_client(client, admin_headers)
    renewal = create_renewal(client, admin_headers, created["id"])

    res = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": True},
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_complete_renewal_not_renewed_without_category_fails(client, admin_headers):
    created = create_client(client, admin_headers)
    renewal = create_renewal(client, admin_headers, created["id"])

    res = client.post(
        f"/renewals/{renewal['id']}/complete",
        json={"renewed": False},
        headers=admin_headers,
    )
    assert res.status_code == 400
