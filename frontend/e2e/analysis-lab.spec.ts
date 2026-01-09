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

const mockLlmErrorResult = {
    intent: "generate_summary",
    is_complete: true,
    duration_ms: 1600,
    pipeline_id: "pipeline-llm-error",
    started_at: "2026-01-09T10:06:00Z",
    finished_at: "2026-01-09T10:06:02Z",
    final_output: {
        report: {
            report: "# Summary Report\n\n- Fallback summary was used.",
            llm_used: true,
            llm_model: "gpt-4o-mini",
            llm_error: "Rate limit exceeded",
        },
    },
    node_results: {
        summary_report: {
            status: "completed",
            duration_ms: 240,
            output: {
                report: "# Summary Report\n\n- Fallback summary was used.",
            },
        },
    },
};

const mockPartialFailureResult = {
    intent: "generate_summary",
    is_complete: false,
    duration_ms: 900,
    pipeline_id: "pipeline-partial",
    started_at: "2026-01-09T10:06:10Z",
    finished_at: "2026-01-09T10:06:11Z",
    final_output: {
        report: {
            report: "# Summary Report\n\n- Partial result.",
        },
    },
    node_results: {
        summary_report: {
            status: "failed",
            duration_ms: 120,
            error: "Timeout while generating summary",
            output: {
                report: "# Summary Report\n\n- Partial result.",
            },
        },
    },
};

const largeReportText = `# Summary Report\n\n${"A".repeat(6200)}`;
const mockLargeReportResult = {
    intent: "generate_summary",
    is_complete: true,
    duration_ms: 1900,
    pipeline_id: "pipeline-large",
    started_at: "2026-01-09T10:06:20Z",
    finished_at: "2026-01-09T10:06:22Z",
    final_output: {
        report: {
            report: largeReportText,
        },
    },
    node_results: {
        summary_report: {
            status: "completed",
            duration_ms: 320,
            output: {
                report: largeReportText,
            },
        },
    },
};

const mockNoReportResult = {
    intent: "generate_summary",
    is_complete: true,
    duration_ms: 700,
    pipeline_id: "pipeline-no-report",
    started_at: "2026-01-09T10:06:30Z",
    finished_at: "2026-01-09T10:06:31Z",
    final_output: {
        metrics: {
            accuracy: 0.5,
        },
    },
    node_results: {
        summary_report: {
            status: "completed",
            duration_ms: 200,
            output: {
                summary: {
                    accuracy: 0.5,
                },
            },
        },
    },
};

test.describe("Analysis Lab", () => {
    test.beforeEach(async ({ page }) => {
        await page.route("**/api/v1/config/**", async (route) => {
            await route.fulfill({ json: {} });
        });
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
        const statusCard = page.getByText("상태", { exact: true }).locator("..");
        await expect(statusCard.getByText("완료", { exact: true })).toBeVisible();
    });

    test("should show LLM error banner and badge", async ({ page }) => {
        await page.route("**/api/v1/pipeline/analyze", async (route) => {
            await route.fulfill({ json: mockLlmErrorResult });
        });

        await page.goto("/analysis");
        await page.getByRole("button", { name: /성능 요약/ }).click();

        const reportCard = page.getByText("보고서 상태", { exact: true }).locator("..");
        await expect(
            reportCard.getByText("LLM 오류(대체 보고서)", { exact: true })
        ).toBeVisible();
        await expect(
            page.getByText(/LLM 오류로 대체 보고서를 사용했습니다/)
        ).toBeVisible();
        await expect(page.getByText("모델 gpt-4o-mini")).toBeVisible();
    });

    test("should highlight partial node failures", async ({ page }) => {
        await page.route("**/api/v1/pipeline/analyze", async (route) => {
            await route.fulfill({ json: mockPartialFailureResult });
        });

        await page.goto("/analysis");
        await page.getByRole("button", { name: /성능 요약/ }).click();

        await expect(
            page.getByText("일부 단계에서 오류가 발생했습니다. 실행 로그를 확인하세요.")
        ).toBeVisible();

        const nodeDetails = page.locator("details").filter({ hasText: "Summary Report" }).first();
        await nodeDetails.locator("summary").first().click();
        await expect(
            nodeDetails.getByText("Timeout while generating summary", { exact: true })
        ).toBeVisible();
    });

    test("should show large report toggle", async ({ page }) => {
        await page.route("**/api/v1/pipeline/analyze", async (route) => {
            await route.fulfill({ json: mockLargeReportResult });
        });

        await page.goto("/analysis");
        await page.getByRole("button", { name: /성능 요약/ }).click();

        await expect(page.getByRole("button", { name: "전체 보기" })).toBeVisible();
        await page.getByRole("button", { name: "전체 보기" }).click();
        await expect(page.getByRole("button", { name: "요약 보기" })).toBeVisible();
        await expect(page.getByRole("button", { name: "마크다운 렌더링" })).toBeVisible();
        await page.getByRole("button", { name: "마크다운 렌더링" }).click();
        await expect(page.getByRole("button", { name: "경량 보기" })).toBeVisible();
    });

    test("should mark missing report", async ({ page }) => {
        await page.route("**/api/v1/pipeline/analyze", async (route) => {
            await route.fulfill({ json: mockNoReportResult });
        });

        await page.goto("/analysis");
        await page.getByRole("button", { name: /성능 요약/ }).click();

        const reportCard = page.getByText("보고서 상태", { exact: true }).locator("..");
        await expect(
            reportCard.getByText("보고서 없음", { exact: true })
        ).toBeVisible();
    });
});
