from datetime import date, timedelta


def create_client(client, admin_headers, status="ativo"):
    res = client.post("/clients", json={"corporate_name": "Cliente Teste Alertas LTDA", "status": status}, headers=admin_headers)
    assert res.status_code == 201, res.text
    return res.json()


def create_critical_risk(client, admin_headers, client_id):
    res = client.post(
        f"/clients/{client_id}/risks",
        json={"category": "adocao", "description": "Baixo engajamento", "impact": "alto", "probability": "alta"},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_critical_risk_triggers_alert_and_auto_creates_task(client, admin_headers):
    created = create_client(client, admin_headers)
    create_critical_risk(client, admin_headers, created["id"])

    alerts_res = client.get("/alerts/active", headers=admin_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    risk_alerts = [a for a in alerts if a["event_type"] == "risco_critico" and a["client_id"] == created["id"]]
    assert len(risk_alerts) == 1

    tasks_res = client.get(f"/clients/{created['id']}/tasks", headers=admin_headers)
    auto_tasks = [t for t in tasks_res.json() if t["origin"] == "alerta_risco_critico"]
    assert len(auto_tasks) == 1


def test_alert_task_creation_is_deduplicated_on_repeated_evaluation(client, admin_headers):
    created = create_client(client, admin_headers)
    create_critical_risk(client, admin_headers, created["id"])

    # avaliar duas vezes não deve duplicar a tarefa
    client.get("/alerts/active", headers=admin_headers)
    client.get("/alerts/active", headers=admin_headers)

    tasks_res = client.get(f"/clients/{created['id']}/tasks", headers=admin_headers)
    auto_tasks = [t for t in tasks_res.json() if t["origin"] == "alerta_risco_critico"]
    assert len(auto_tasks) == 1


def test_mitigated_risk_does_not_trigger_alert(client, admin_headers):
    created = create_client(client, admin_headers)
    risk = create_critical_risk(client, admin_headers, created["id"])

    update_res = client.patch(f"/risks/{risk['id']}", json={"status": "mitigado"}, headers=admin_headers)
    assert update_res.status_code == 200

    alerts = client.get("/alerts/active", headers=admin_headers).json()
    risk_alerts = [a for a in alerts if a["event_type"] == "risco_critico" and a["client_id"] == created["id"]]
    assert risk_alerts == []


def test_upcoming_renewal_triggers_alert(client, admin_headers):
    created = create_client(client, admin_headers)
    end_date = (date.today() + timedelta(days=30)).isoformat()
    res = client.post(
        f"/clients/{created['id']}/renewals",
        json={"contract_end_date": end_date},
        headers=admin_headers,
    )
    assert res.status_code == 201

    alerts = client.get("/alerts/active", headers=admin_headers).json()
    renewal_alerts = [a for a in alerts if a["event_type"] == "renovacao_proxima" and a["client_id"] == created["id"]]
    assert len(renewal_alerts) == 1


def test_renewal_risk_alert_requires_renewal_and_critical_risk_together(client, admin_headers):
    created = create_client(client, admin_headers)
    client_id = created["id"]

    # só o risco crítico, sem renovação próxima: não deve gerar renovacao_risco
    create_critical_risk(client, admin_headers, client_id)
    alerts = client.get("/alerts/active", headers=admin_headers).json()
    assert not [a for a in alerts if a["event_type"] == "renovacao_risco" and a["client_id"] == client_id]

    # agora com renovação próxima também: deve gerar
    end_date = (date.today() + timedelta(days=20)).isoformat()
    client.post(f"/clients/{client_id}/renewals", json={"contract_end_date": end_date}, headers=admin_headers)

    alerts = client.get("/alerts/active", headers=admin_headers).json()
    renewal_risk_alerts = [a for a in alerts if a["event_type"] == "renovacao_risco" and a["client_id"] == client_id]
    assert len(renewal_risk_alerts) == 1


def test_far_future_renewal_does_not_trigger_alert(client, admin_headers):
    created = create_client(client, admin_headers)
    end_date = (date.today() + timedelta(days=200)).isoformat()
    client.post(f"/clients/{created['id']}/renewals", json={"contract_end_date": end_date}, headers=admin_headers)

    alerts = client.get("/alerts/active", headers=admin_headers).json()
    renewal_alerts = [a for a in alerts if a["event_type"] == "renovacao_proxima" and a["client_id"] == created["id"]]
    assert renewal_alerts == []
