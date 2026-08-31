"""CRUD tests: create/read/update/delete + validation + RBAC + authorization."""

from __future__ import annotations


def _valid_payload(**overrides):
    payload = {
        "studentName": "CRUD Test Student",
        "age": 21,
        "studentState": "Karnataka",
        "institutionId": "INS001",
        "courseId": "CRS001",
        "loanAmountRequestedInr": 800000,
        "parentMonthlyIncomeInr": 120000,
        "existingMonthlyObligationsInr": 15000,
        "creditScore": 710,
        "employmentType": "Salaried",
        "applicationChannel": "Website",
    }
    payload.update(overrides)
    return payload


class TestRead:
    def test_list_applications(self, client, admin_headers):
        resp = client.get("/api/applications", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 150
        assert isinstance(body["data"], list)
        row = body["data"][0]
        # Flask-compatible camelCase keys.
        for key in ("id", "studentName", "applicationStatus", "attentionLevel"):
            assert key in row, key

    def test_list_with_search_and_filters(self, client, admin_headers):
        resp = client.get("/api/applications", headers=admin_headers, params={
            "search": "EDU10", "status": "all", "sortBy": "applicationDate", "sortDir": "desc",
        })
        assert resp.status_code == 200
        assert resp.json()["count"] > 0

    def test_list_paginated(self, client, admin_headers):
        resp = client.get("/api/applications", headers=admin_headers, params={
            "page": 1, "pageSize": 10,
        })
        body = resp.json()
        assert body["pageSize"] == 10
        assert len(body["data"]) == 10
        assert body["totalPages"] >= 15
        assert body["count"] >= 150

    def test_get_single(self, client, admin_headers):
        resp = client.get("/api/applications/EDU1001", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == "EDU1001"

    def test_get_missing_404(self, client, admin_headers):
        assert client.get("/api/applications/EDU9999", headers=admin_headers).status_code == 404

    def test_requires_authentication(self, client):
        assert client.get("/api/applications").status_code == 401


class TestCreate:
    def test_create_valid(self, client, admin_headers):
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload())
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["id"].startswith("EDU")
        assert body["applicationStatus"] == "Submitted"
        # Attention level recomputed server-side.
        assert body["attentionLevel"] in ("Low Attention", "Review Required", "High Attention")

    def test_create_missing_required_field(self, client, admin_headers):
        payload = _valid_payload()
        payload.pop("studentName")
        resp = client.post("/api/applications", headers=admin_headers, json=payload)
        assert resp.status_code == 422

    def test_create_invalid_values(self, client, admin_headers):
        # Age out of range
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload(age=12))
        assert resp.status_code == 422
        # Loan amount below minimum
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload(loanAmountRequestedInr=100))
        assert resp.status_code == 422
        # Credit score out of range
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload(creditScore=9999))
        assert resp.status_code == 422

    def test_create_unknown_references(self, client, admin_headers):
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload(institutionId="INS999"))
        assert resp.status_code == 422
        resp = client.post("/api/applications", headers=admin_headers, json=_valid_payload(courseId="CRS999"))
        assert resp.status_code == 422

    def test_create_readonly_role_forbidden(self, client, analyst_headers):
        resp = client.post("/api/applications", headers=analyst_headers, json=_valid_payload())
        assert resp.status_code == 403

    def test_create_unauthenticated(self, client):
        resp = client.post("/api/applications", json=_valid_payload())
        assert resp.status_code == 401


class TestUpdate:
    def test_patch_status(self, client, admin_headers):
        create = client.post("/api/applications", headers=admin_headers, json=_valid_payload())
        app_id = create.json()["id"]
        resp = client.patch(f"/api/applications/{app_id}", headers=admin_headers,
                            json={"applicationStatus": "Approved"})
        assert resp.status_code == 200
        assert resp.json()["applicationStatus"] == "Approved"

    def test_patch_invalid_status(self, client, admin_headers):
        create = client.post("/api/applications", headers=admin_headers, json=_valid_payload())
        app_id = create.json()["id"]
        resp = client.patch(f"/api/applications/{app_id}", headers=admin_headers,
                            json={"applicationStatus": "Flying"})
        assert resp.status_code == 422

    def test_put_full_update(self, client, admin_headers):
        create = client.post("/api/applications", headers=admin_headers, json=_valid_payload())
        app_id = create.json()["id"]
        resp = client.put(f"/api/applications/{app_id}", headers=admin_headers,
                          json={"studentName": "Updated Name", "creditScore": 780})
        assert resp.status_code == 200
        body = resp.json()
        assert body["studentName"] == "Updated Name"
        assert body["creditScore"] == 780
        # Untouched fields preserved.
        assert body["institutionId"] == "INS001"

    def test_put_missing_404(self, client, admin_headers):
        resp = client.put("/api/applications/EDU9999", headers=admin_headers,
                          json={"studentName": "Nobody"})
        assert resp.status_code == 404

    def test_update_readonly_role_forbidden(self, client, analyst_headers):
        resp = client.patch("/api/applications/EDU1001", headers=analyst_headers,
                            json={"applicationStatus": "Approved"})
        assert resp.status_code == 403


class TestDelete:
    def test_delete_flow(self, client, admin_headers):
        create = client.post("/api/applications", headers=admin_headers, json=_valid_payload())
        app_id = create.json()["id"]
        assert client.delete(f"/api/applications/{app_id}", headers=admin_headers).status_code == 200
        # Gone for real.
        assert client.get(f"/api/applications/{app_id}", headers=admin_headers).status_code == 404
        # Deleting again → 404.
        assert client.delete(f"/api/applications/{app_id}", headers=admin_headers).status_code == 404

    def test_delete_readonly_role_forbidden(self, client, analyst_headers):
        assert client.delete("/api/applications/EDU1001", headers=analyst_headers).status_code == 403

    def test_delete_unauthenticated(self, client):
        assert client.delete("/api/applications/EDU1001").status_code == 401


class TestAnalyticsCompat:
    """The original Flask analytics endpoints keep working."""

    def test_kpis_shape(self, client, admin_headers):
        body = client.get("/api/kpis", headers=admin_headers).json()
        for key in ("totalApplications", "approved", "underReview", "rejected"):
            assert key in body

    def test_charts_and_insights(self, client, admin_headers):
        assert client.get("/api/charts", headers=admin_headers).status_code == 200
        insights = client.get("/api/insights", headers=admin_headers).json()
        assert len(insights) == 5

    def test_data_quality(self, client, admin_headers):
        body = client.get("/api/data-quality", headers=admin_headers).json()
        assert body["totalIssues"] >= 8

    def test_filters(self, client, admin_headers):
        body = client.get("/api/filters", headers=admin_headers).json()
        assert "institutions" in body and "courses" in body and "statuses" in body
