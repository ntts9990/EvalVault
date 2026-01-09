import { test, expect } from "@playwright/test";

const mockResultA = {
    result_id: "analysis-a",
    intent: "generate_summary",
    label: "Summary A",
    query: "요약해줘",
    run_id: "run-123",
    profile: "dev",
    tags: ["baseline"],
    duration_ms: 1200,
    is_complete: true,
    created_at: "2026-01-09T10:00:00Z",
    started_at: "2026-01-09T10:00:00Z",
    finished_at: "2026-01-09T10:00:02Z",
    pipeline_id: "pipe-a",
    final_output: {
        metrics: { score: 0.75, precision: 0.9 },
        priority_summary: {
            bottom_cases: [
                {
                    test_case_id: "tc-1",
                    failed_metrics: ["faithfulness"],
                },
            ],
            impact_cases: [],
        },
    },
    node_results: {
        statistical: { status: "completed" },
        report: { status: "failed", error: "LLM error" },
    },
};

const mockResultB = {
    result_id: "analysis-b",
    intent: "generate_summary",
    label: "Summary B",
    query: "요약해줘",
    run_id: "run-456",
    profile: "prod",
    tags: ["candidate"],
    duration_ms: 980,
    is_complete: true,
    created_at: "2026-01-10T10:00:00Z",
    started_at: "2026-01-10T10:00:00Z",
    finished_at: "2026-01-10T10:00:02Z",
    pipeline_id: "pipe-b",
    final_output: {
        metrics: { score: 0.82, precision: 0.94 },
        priority_summary: {
            bottom_cases: [
                {
                    test_case_id: "tc-2",
                    failed_metrics: ["faithfulness", "answer_relevancy"],
                },
            ],
            impact_cases: [
                {
                    test_case_id: "tc-3",
                    failed_metrics: ["context_precision"],
                },
            ],
        },
    },
    node_results: {
        statistical: { status: "completed" },
        report: { status: "completed" },
    },
};

test.describe("Analysis Compare", () => {
    test.beforeEach(async ({ page }) => {
        await page.route("**/api/v1/pipeline/results/**", async (route) => {
            const url = new URL(route.request().url());
            const id = url.pathname.split("/").pop();
            if (id === "analysis-a") {
                await route.fulfill({ json: mockResultA });
                return;
            }
            if (id === "analysis-b") {
                await route.fulfill({ json: mockResultB });
                return;
            }
            await route.fulfill({ status: 404, json: { detail: "Not found" } });
        });
    });

    test("should compare saved analysis results", async ({ page }) => {
        await page.goto("/analysis/compare?left=analysis-a&right=analysis-b");

        await expect(page.getByRole("heading", { name: "분석 결과 비교" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Summary A" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Summary B" })).toBeVisible();
        await expect(page.getByText("노드 상태 비교")).toBeVisible();
        await expect(page.getByText("A · 실패")).toBeVisible();
        await expect(page.getByText("B · 완료")).toBeVisible();
        await expect(page.getByText("우선순위 케이스 변화")).toBeVisible();
        await expect(page.getByText("메트릭 차이")).toBeVisible();
        await expect(page.getByText("metrics.score", { exact: true })).toBeVisible();
    });
});
