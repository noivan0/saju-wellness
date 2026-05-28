from locust import HttpUser, task, between

class SajuUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(3)
    def saju_calculate(self):
        self.client.get("/api/saju?year=1990&month=5&day=15&hour=10")

    @task(2)
    def fortune_daily(self):
        self.client.get("/api/fortune/daily?year=1990&month=5&day=15")

    @task(2)
    def saju_analyze(self):
        self.client.post(
            "/api/saju/analyze",
            json={
                "year": 1990,
                "month": 5,
                "day": 15,
                "hour": 10,
                "mood_level": 3
            },
        )

    @task(1)
    def health(self):
        self.client.get("/health")