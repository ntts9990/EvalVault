import { test, expect } from "@playwright/test";

const baseRun = {
    summary: {
        run_id: "run-123",
        dataset_name: "test-dataset-v1",
        model_name: "gpt-4-turbo",
        pass_rate: 0.9,
        total_test_cases: 1,
        passed_test_cases: 1,
        started_at: "2026-01-09T10:00:00Z",
        finished_at: "2026-01-09T10:05:00Z",
        metrics_evaluated: ["accuracy"],
        total_cost_usd: 0.1,
        phoenix_precision: null,
        phoenix_drift: null,
        phoenix_experiment_url: null,
    },
    results: [
        {
            test_case_id: "tc-1",
            question: "What is RAG?",
            answer: "Retrieval Augmented Generation.",
            ground_truth: "RAG includes retrieval.",
            contexts: ["Context"],
            metrics: [
                { name: "accuracy", score: 1.0, passed: true, reason: "Exact match" },
            ],
        },
    ],
};

const targetRun = {
    summary: {
        run_id: "run-124",
        dataset_name: "test-dataset-v1",
        model_name: "gpt-4-turbo",
        pass_rate: 0.5,
        total_test_cases: 2,
        passed_test_cases: 1,
        started_at: "2026-01-10T10:00:00Z",
        finished_at: "2026-01-10T10:06:00Z",
        metrics_evaluated: ["accuracy"],
        total_cost_usd: 0.12,
        phoenix_precision: null,
        phoenix_drift: null,
        phoenix_experiment_url: null,
    },
    results: [
        {
            test_case_id: "tc-1",
            question: "What is RAG?",
            answer: "RAG is a model.",
            ground_truth: "RAG includes retrieval.",
            contexts: ["Context"],
            metrics: [
                { name: "accuracy", score: 0.2, passed: false, reason: "Mismatch" },
            ],
        },
        {
            test_case_id: "tc-2",
            question: "Define LLM.",
            answer: "Large language model.",
            ground_truth: "Large language model.",
            contexts: ["Context"],
            metrics: [
                { name: "accuracy", score: 1.0, passed: true, reason: "Exact match" },
            ],
        },
    ],
};

const mockComparison = {
    base: baseRun,
    target: targetRun,
    metric_deltas: [
        { name: "accuracy", base: 1.0, target: 0.6, delta: -0.4 },
    ],
    case_counts: {
        regressions: 1,
        improvements: 0,
        same_pass: 0,
        same_fail: 0,
        new: 1,
        removed: 0,
    },
    pass_rate_delta: -0.4,
    total_cases_delta: 1,
};

test.describe("Compare Runs", () => {
    test.beforeEach(async ({ page }) => {
        await page.route("**/api/v1/runs/compare**", async (route) => {
            await route.fulfill({ json: mockComparison });
        });
    });

    test("should render comparison view and filter regressions", async ({ page }) => {
        await page.goto("/compare?base=run-123&target=run-124");

        await expect(page.getByRole("heading", { name: "Run Comparison" })).toBeVisible();
        await expect(page.getByText("Pass Rate Change")).toBeVisible();
        await expect(page.getByText("Test Case Comparison")).toBeVisible();

        await page.getByRole("button", { name: "Regressions" }).click();
        await expect(page.getByText("Regression", { exact: true })).toBeVisible();
    });
});
