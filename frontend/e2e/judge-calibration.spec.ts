import { test, expect } from "@playwright/test";

const runFixture = [
    {
        run_id: "run_12345678",
        dataset_name: "demo",
        model_name: "gpt-5-mini",
        pass_rate: 0.8,
        total_test_cases: 10,
        passed_test_cases: 8,
        started_at: "2026-01-27T00:00:00Z",
        finished_at: null,
        metrics_evaluated: ["faithfulness", "answer_relevancy"],
        total_cost_usd: null,
        phoenix_precision: null,
        phoenix_drift: null,
        phoenix_experiment_url: null,
    },
];

const historyFixture = [
    {
        calibration_id: "judge_calibration_run_12345678_20260127_000001",
        run_id: "run_12345678",
        labels_source: "feedback",
        method: "isotonic",
        metrics: ["faithfulness"],
        holdout_ratio: 0.2,
        seed: 42,
        total_labels: 20,
        total_samples: 30,
        gate_passed: true,
        gate_threshold: 0.6,
        created_at: "2026-01-27T00:00:01Z",
    },
];

const calibrationResponse = {
    calibration_id: "judge_calibration_run_12345678_20260127_000002",
    status: "ok",
    started_at: "2026-01-27T00:00:02Z",
    finished_at: "2026-01-27T00:00:03Z",
    duration_ms: 1200,
    artifacts: { dir: "reports/calibration/artifacts/judge_calibration_run_12345678_20260127_000002" },
    summary: {
        calibration_id: "judge_calibration_run_12345678_20260127_000002",
        run_id: "run_12345678",
        labels_source: "feedback",
        method: "isotonic",
        metrics: ["faithfulness"],
        holdout_ratio: 0.2,
        seed: 42,
        total_labels: 20,
        total_samples: 30,
        gate_passed: true,
        gate_threshold: 0.6,
        notes: [],
        created_at: "2026-01-27T00:00:02Z",
    },
    metrics: [
        {
            metric: "faithfulness",
            method: "isotonic",
            sample_count: 30,
            label_count: 20,
            mae: 0.12,
            pearson: 0.71,
            spearman: 0.69,
            temperature: null,
            parameters: {},
            gate_passed: true,
            warning: null,
        },
    ],
    case_results: {
        faithfulness: [
            {
                test_case_id: "tc-1",
                raw_score: 0.62,
                calibrated_score: 0.67,
                label: 0.7,
                label_source: "feedback",
            },
        ],
    },
    warnings: [],
};

test("judge calibration page renders and runs", async ({ page }) => {
    await page.route("**/api/v1/runs/", async (route) => {
        await route.fulfill({ json: runFixture });
    });
    await page.route("**/api/v1/calibration/judge/history?limit=20", async (route) => {
        await route.fulfill({ json: historyFixture });
    });
    await page.route("**/api/v1/calibration/judge", async (route) => {
        const request = route.request();
        if (request.method() === "POST") {
            await route.fulfill({ json: calibrationResponse });
            return;
        }
        await route.fallback();
    });

    await page.goto("/calibration");
    await expect(page.getByRole("heading", { name: "Judge Calibration" })).toBeVisible();
    await expect(page.getByText("히스토리")).toBeVisible();

    await page.getByRole("combobox").first().selectOption({ label: "demo · run_12345678" });
    await expect(page.getByRole("button", { name: "faithfulness" })).toBeVisible();

    await page.getByRole("button", { name: "Judge 보정 실행" }).click();
    await expect(page.getByText("결과 요약")).toBeVisible();
    await expect(page.getByText("30")).toBeVisible();
    await expect(page.getByText("faithfulness")).toBeVisible();
});
