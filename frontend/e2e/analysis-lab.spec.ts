import { test, expect } from "@playwright/test";

const mockIntents = [
    {
        intent: "generate_summary",
        label: "성능 요약",
        category: "report",
        description: "실행 결과를 요약합니다.",
        sample_query: "요약해줘",
        available: true,
        missing_modules: [],
        nodes: [
            {
                id: "summary_report",
                name: "Summary Report",
                module: "report",
                depends_on: [],
            },
        ],
    },
];

const mockRuns = [
    {
        run_id: "run-123",
        dataset_name: "test-dataset-v1",
        model_name: "gpt-4-turbo",
        pass_rate: 0.85,
        total_test_cases: 20,
        passed_test_cases: 17,
        started_at: "2026-01-09T10:00:00Z",
        finished_at: "2026-01-09T10:05:00Z",
        metrics_evaluated: ["accuracy", "relevance"],
        total_cost_usd: 0.15,
        phoenix_precision: 0.92,
        phoenix_drift: 0.01,
        phoenix_experiment_url: "http://localhost:6006/projects/1",
    },
];

const mockAnalysisResult = {
    intent: "generate_summary",
    is_complete: true,
    duration_ms: 1200,
    pipeline_id: "pipeline-123",
    started_at: "2026-01-09T10:06:00Z",
    finished_at: "2026-01-09T10:06:01Z",
    final_output: {
        report: {
            report: "# Summary Report\n\n- Overall health is stable.",
        },
    },
    node_results: {
        summary_report: {
            status: "completed",
            duration_ms: 220,
            output: {
                report: "# Summary Report\n\n- Overall health is stable.",
            },
        },
    },
};

test.describe("Analysis Lab", () => {
    test.beforeEach(async ({ page }) => {
        await page.route("**/api/v1/pipeline/intents", async (route) => {
            await route.fulfill({ json: mockIntents });
        });
        await page.route("**/api/v1/runs/", async (route) => {
            await route.fulfill({ json: mockRuns });
        });
        await page.route("**/api/v1/pipeline/results?*", async (route) => {
            await route.fulfill({ json: [] });
        });
    });

    test("should run analysis and show results", async ({ page }) => {
        await page.route("**/api/v1/pipeline/analyze", async (route) => {
            await route.fulfill({ json: mockAnalysisResult });
        });

        await page.goto("/analysis");

        await expect(page.getByRole("heading", { name: "분석 실험실" })).toBeVisible();
        await expect(page.getByText("실행 대상 선택")).toBeVisible();
        await expect(page.getByRole("button", { name: /성능 요약/ })).toBeVisible();

        await page.getByRole("button", { name: /성능 요약/ }).click();

        await expect(page.getByRole("heading", { name: "성능 요약 결과" })).toBeVisible();
        const resultOutput = page
            .getByRole("heading", { name: "결과 출력" })
            .locator("..")
            .locator("..");
        await expect(resultOutput).toBeVisible();
        await expect(resultOutput.getByRole("heading", { name: "Summary Report" })).toBeVisible();
        const statusCard = page.getByText("상태").locator("..");
        await expect(statusCard.getByText("완료")).toBeVisible();
    });
});
