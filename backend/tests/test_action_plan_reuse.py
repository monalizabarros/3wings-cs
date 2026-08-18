"""Cobre os dois pontos em que módulos diferentes reaproveitam o mesmo
ActionPlan (Bloco 10) em vez de criar um modelo próprio: plano de
recuperação de risco (Bloco 13) e plano de ação de QBR (Bloco 16)."""

from datetime import date


def create_client(client, admin_headers):
    res = client.post("/clients", json={"corporate_name": "Cliente Teste Planos LTDA", "status": "ativo"}, headers=admin_headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_risk_recovery_plan_creates_action_plan_and_links_it(client, admin_headers):
    created = create_client(client, admin_headers)
    risk_res = client.post(
        f"/clients/{created['id']}/risks",
        json={"category": "financeiro", "description": "Atraso no pagamento", "impact": "alto", "probability": "media"},
        headers=admin_headers,
    )
    risk = risk_res.json()
    assert risk["action_plan_id"] is None

    plan_res = client.post(f"/risks/{risk['id']}/recovery-plan", headers=admin_headers)
    assert plan_res.status_code == 201, plan_res.text
    plan = plan_res.json()
    assert plan["client_id"] == created["id"]

    risk_after = client.get(f"/clients/{created['id']}/risks", headers=admin_headers).json()[0]
    assert risk_after["action_plan_id"] == plan["id"]

    # segunda tentativa deve falhar (já existe plano vinculado)
    second = client.post(f"/risks/{risk['id']}/recovery-plan", headers=admin_headers)
    assert second.status_code == 400


def test_qbr_action_plan_creates_action_plan_and_links_it(client, admin_headers):
    created = create_client(client, admin_headers)
    qbr_res = client.post(
        f"/clients/{created['id']}/qbrs",
        json={"scheduled_date": date.today().isoformat(), "agenda": "Revisão trimestral"},
        headers=admin_headers,
    )
    qbr = qbr_res.json()
    assert qbr["action_plan_id"] is None

    complete_res = client.post(
        f"/qbrs/{qbr['id']}/complete",
        json={"achievements": "Migração concluída", "next_period_goals": "Expandir uso do módulo X"},
        headers=admin_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "realizado"

    plan_res = client.post(f"/qbrs/{qbr['id']}/action-plan", headers=admin_headers)
    assert plan_res.status_code == 201, plan_res.text
    plan = plan_res.json()
    assert plan["client_id"] == created["id"]
    assert "QBR" in plan["title"]

    second = client.post(f"/qbrs/{qbr['id']}/action-plan", headers=admin_headers)
    assert second.status_code == 400


def test_qbr_cannot_be_completed_twice(client, admin_headers):
    created = create_client(client, admin_headers)
    qbr_res = client.post(
        f"/clients/{created['id']}/qbrs",
        json={"scheduled_date": date.today().isoformat()},
        headers=admin_headers,
    )
    qbr_id = qbr_res.json()["id"]

    first = client.post(f"/qbrs/{qbr_id}/complete", json={}, headers=admin_headers)
    assert first.status_code == 200

    second = client.post(f"/qbrs/{qbr_id}/complete", json={}, headers=admin_headers)
    assert second.status_code == 400
