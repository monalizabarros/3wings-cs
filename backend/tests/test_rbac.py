from app.models.user import RoleName


def test_comercial_cannot_view_tasks(client, make_headers):
    headers = make_headers(RoleName.COMERCIAL)
    res = client.get("/tasks", headers=headers)
    assert res.status_code == 403


def test_suporte_cannot_view_tasks(client, make_headers):
    headers = make_headers(RoleName.SUPORTE)
    res = client.get("/tasks", headers=headers)
    assert res.status_code == 403


def test_produto_cannot_create_client(client, make_headers):
    headers = make_headers(RoleName.PRODUTO)
    res = client.post("/clients", json={"corporate_name": "Não deveria existir"}, headers=headers)
    assert res.status_code == 403


def test_admin_bypasses_permission_matrix(client, admin_headers):
    res = client.get("/tasks", headers=admin_headers)
    assert res.status_code == 200


def test_inactive_user_cannot_login(client, db, make_headers):
    headers = make_headers(RoleName.CS, email="inativo@3wings.com.br")
    assert headers  # login funcionou com usuário ativo

    from app.models.user import User

    user = db.query(User).filter(User.email == "inativo@3wings.com.br").first()
    user.is_active = False
    db.commit()

    res = client.post("/auth/login", data={"username": "inativo@3wings.com.br", "password": "senha123"})
    assert res.status_code == 403


def test_only_admin_role_can_delete_users(client, admin_headers, make_headers):
    gestor_headers = make_headers(RoleName.GESTOR_CS)
    # Gestor de CS não tem can_delete em 'users' pela matriz padrão do seed
    res = client.get("/users", headers=admin_headers)
    target_id = next(u["id"] for u in res.json()["items"] if u["email"] != "admin@3wings.com.br")

    denied = client.delete(f"/users/{target_id}", headers=gestor_headers)
    assert denied.status_code == 403
