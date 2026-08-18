from app.models.user import RoleName


def create_client(client, admin_headers, status="em_onboarding"):
    res = client.post(
        "/clients",
        json={"corporate_name": "Cliente Teste Handoff LTDA", "status": status},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_accept_delivery_handoff_activates_client_and_starts_onboarding(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]
    assert created["status"] == "em_onboarding"

    handoff_res = client.post(
        f"/clients/{client_id}/delivery-handoffs",
        json={"business_objective": "Reduzir tempo de atendimento"},
        headers=admin_headers,
    )
    assert handoff_res.status_code == 201, handoff_res.text
    handoff_id = handoff_res.json()["id"]
    assert handoff_res.json()["accepted_at"] is None

    onboarding_before = client.get(f"/clients/{client_id}/onboarding", headers=admin_headers)
    assert onboarding_before.json()["journey"] is None

    accept_res = client.post(f"/delivery-handoffs/{handoff_id}/accept", headers=admin_headers)
    assert accept_res.status_code == 200, accept_res.text
    assert accept_res.json()["accepted_at"] is not None

    client_after = client.get(f"/clients/{client_id}", headers=admin_headers)
    assert client_after.json()["status"] == "ativo"

    onboarding_after = client.get(f"/clients/{client_id}/onboarding", headers=admin_headers)
    assert onboarding_after.json()["journey"] is not None


def test_accept_delivery_handoff_twice_fails(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]
    handoff_res = client.post(f"/clients/{client_id}/delivery-handoffs", json={}, headers=admin_headers)
    handoff_id = handoff_res.json()["id"]

    first = client.post(f"/delivery-handoffs/{handoff_id}/accept", headers=admin_headers)
    assert first.status_code == 200

    second = client.post(f"/delivery-handoffs/{handoff_id}/accept", headers=admin_headers)
    assert second.status_code == 400


def test_accept_delivery_handoff_already_active_client_does_not_error(client, admin_headers):
    """Cliente já ativo (ex.: reaceite de um handoff adicional) não deve
    quebrar por já estar no status alvo."""
    created = create_client(client, admin_headers, status="ativo")
    client_id = created["id"]
    handoff_res = client.post(f"/clients/{client_id}/delivery-handoffs", json={}, headers=admin_headers)
    handoff_id = handoff_res.json()["id"]

    accept_res = client.post(f"/delivery-handoffs/{handoff_id}/accept", headers=admin_headers)
    assert accept_res.status_code == 200

    client_after = client.get(f"/clients/{client_id}", headers=admin_headers)
    assert client_after.json()["status"] == "ativo"


def test_projetos_role_cannot_accept_delivery_handoff(client, admin_headers, make_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]
    handoff_res = client.post(f"/clients/{client_id}/delivery-handoffs", json={}, headers=admin_headers)
    handoff_id = handoff_res.json()["id"]

    projetos_headers = make_headers(RoleName.PROJETOS)
    res = client.post(f"/delivery-handoffs/{handoff_id}/accept", headers=projetos_headers)
    assert res.status_code == 403
