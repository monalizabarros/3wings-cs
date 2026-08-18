from datetime import date


def create_client(client, admin_headers):
    res = client.post("/clients", json={"corporate_name": "Cliente Teste Health Score LTDA", "status": "ativo"}, headers=admin_headers)
    assert res.status_code == 201, res.text
    return res.json()


def get_indicator_id(client, admin_headers, key):
    res = client.get("/health-score-indicators", headers=admin_headers)
    matches = [i for i in res.json() if i["key"] == key]
    assert len(matches) == 1
    return matches[0]["id"]


def set_indicator_source(client, admin_headers, key, source):
    indicator_id = get_indicator_id(client, admin_headers, key)
    res = client.patch(f"/health-score-indicators/{indicator_id}", json={"source": source}, headers=admin_headers)
    assert res.status_code == 200, res.text


def test_indicator_excluded_when_no_data_available(client, admin_headers):
    created = create_client(client, admin_headers)
    res = client.post(f"/clients/{created['id']}/health-score/calculate", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["components"] == []
    assert body["score"] == 50.0
    assert body["classification"] == "amarelo"


def test_suporte_indicator_uses_average_satisfaction_when_set_to_auto(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]

    ticket_res = client.post(
        f"/clients/{client_id}/support-tickets",
        json={"subject": "Erro ao exportar relatório", "severity": "alta", "opened_at": date.today().isoformat()},
        headers=admin_headers,
    )
    ticket_id = ticket_res.json()["id"]
    client.patch(f"/support-tickets/{ticket_id}", json={"status": "resolvido", "satisfaction_score": 5}, headers=admin_headers)

    set_indicator_source(client, admin_headers, "suporte", "auto")

    res = client.post(f"/clients/{client_id}/health-score/calculate", headers=admin_headers)
    body = res.json()
    suporte_component = next(c for c in body["components"] if c["key"] == "suporte")
    assert suporte_component["value"] == 100.0  # nota 5/5 normalizada para 0-100


def test_suporte_indicator_stays_manual_by_default(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]

    ticket_res = client.post(
        f"/clients/{client_id}/support-tickets",
        json={"subject": "Ticket", "severity": "baixa", "opened_at": date.today().isoformat()},
        headers=admin_headers,
    )
    client.patch(f"/support-tickets/{ticket_res.json()['id']}", json={"satisfaction_score": 3}, headers=admin_headers)

    # sem alternar para 'auto', o indicador não deve puxar o dado do ticket
    res = client.post(f"/clients/{client_id}/health-score/calculate", headers=admin_headers)
    keys = [c["key"] for c in res.json()["components"]]
    assert "suporte" not in keys


def test_negative_survey_creates_followup_task_and_feeds_satisfaction_indicator(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]

    res = client.post(
        f"/clients/{client_id}/surveys",
        json={"type": "nps", "score": 3, "survey_date": date.today().isoformat()},
        headers=admin_headers,
    )
    assert res.status_code == 201

    tasks = client.get(f"/clients/{client_id}/tasks", headers=admin_headers).json()
    followups = [t for t in tasks if t["origin"] == "satisfacao_negativa"]
    assert len(followups) == 1
    assert followups[0]["priority"] == "alta"

    health = client.post(f"/clients/{client_id}/health-score/calculate", headers=admin_headers).json()
    satisfacao_component = next(c for c in health["components"] if c["key"] == "satisfacao")
    assert satisfacao_component["value"] == 30.0  # NPS 3/10 normalizado


def test_deterioration_reasons_compare_last_two_snapshots(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]

    set_indicator_source(client, admin_headers, "suporte", "auto")
    ticket_res = client.post(
        f"/clients/{client_id}/support-tickets",
        json={"subject": "Ticket", "severity": "baixa", "opened_at": date.today().isoformat()},
        headers=admin_headers,
    )
    ticket_id = ticket_res.json()["id"]

    client.patch(f"/support-tickets/{ticket_id}", json={"satisfaction_score": 5}, headers=admin_headers)
    client.post(f"/clients/{client_id}/health-score/calculate", headers=admin_headers)

    client.patch(f"/support-tickets/{ticket_id}", json={"satisfaction_score": 1}, headers=admin_headers)
    client.post(f"/clients/{client_id}/health-score/calculate", headers=admin_headers)

    reasons = client.get(f"/clients/{client_id}/health-score/deterioration-reasons", headers=admin_headers).json()
    suporte_reason = next(r for r in reasons if r["key"] == "suporte")
    assert suporte_reason["drop"] > 0
