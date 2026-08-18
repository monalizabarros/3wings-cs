"""Cobre o disparo de e-mail em alertas críticos (satisfacao_negativa,
risco_critico, renovacao_risco) — sem tocar em SMTP de verdade: mocka
`app.services.alerts.send_email`."""

from datetime import date, timedelta
from unittest.mock import patch


def create_client(client, admin_headers, owner_user_id=None):
    res = client.post(
        "/clients",
        json={"corporate_name": "Cliente Teste E-mail LTDA", "status": "ativo", "owner_user_id": owner_user_id},
        headers=admin_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def get_admin_user_id(db):
    from app.models.user import User

    return db.query(User).filter(User.email == "admin@3wings.com.br").first().id


def test_critical_risk_alert_sends_email_to_client_owner(client, admin_headers, db):
    admin_id = get_admin_user_id(db)
    created = create_client(client, admin_headers, owner_user_id=admin_id)

    with patch("app.services.alerts.send_email") as mock_send:
        res = client.post(
            f"/clients/{created['id']}/risks",
            json={"category": "adocao", "description": "Baixo engajamento", "impact": "alto", "probability": "alta"},
            headers=admin_headers,
        )
        assert res.status_code == 201

        client.get("/alerts/active", headers=admin_headers)

    mock_send.assert_called_once()
    to_arg, subject_arg, body_arg = mock_send.call_args[0]
    assert to_arg == "admin@3wings.com.br"
    assert "Cliente Teste E-mail LTDA" in subject_arg
    assert "risco_critico" in body_arg


def test_email_not_sent_again_on_repeated_evaluation(client, admin_headers, db):
    admin_id = get_admin_user_id(db)
    created = create_client(client, admin_headers, owner_user_id=admin_id)

    with patch("app.services.alerts.send_email") as mock_send:
        client.post(
            f"/clients/{created['id']}/risks",
            json={"category": "adocao", "description": "Baixo engajamento", "impact": "alto", "probability": "alta"},
            headers=admin_headers,
        )
        client.get("/alerts/active", headers=admin_headers)
        client.get("/alerts/active", headers=admin_headers)
        client.get("/alerts/active", headers=admin_headers)

    assert mock_send.call_count == 1


def test_no_email_sent_when_client_has_no_owner(client, admin_headers):
    created = create_client(client, admin_headers, owner_user_id=None)

    with patch("app.services.alerts.send_email") as mock_send:
        client.post(
            f"/clients/{created['id']}/risks",
            json={"category": "adocao", "description": "Baixo engajamento", "impact": "alto", "probability": "alta"},
            headers=admin_headers,
        )
        client.get("/alerts/active", headers=admin_headers)

    mock_send.assert_not_called()


def test_non_critical_alert_does_not_send_email(client, admin_headers, db):
    """sem_contato tem auto_create_task=False no seed — não deve gerar
    tarefa nem e-mail."""
    admin_id = get_admin_user_id(db)
    created = create_client(client, admin_headers, owner_user_id=admin_id)

    end_date = (date.today() + timedelta(days=30)).isoformat()
    with patch("app.services.alerts.send_email") as mock_send:
        client.post(f"/clients/{created['id']}/renewals", json={"contract_end_date": end_date}, headers=admin_headers)
        client.get("/alerts/active", headers=admin_headers)

    # renovacao_proxima tem auto_create_task=False — só renovacao_risco tem True
    mock_send.assert_not_called()


def test_send_email_is_noop_without_smtp_configured():
    from app.services.email import send_email

    assert send_email("alguem@example.com", "Assunto", "Corpo") is False
