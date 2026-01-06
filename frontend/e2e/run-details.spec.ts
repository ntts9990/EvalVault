import { test, expect } from '@playwright/test';

const mockRunDetails = {
    "summary": {
        "run_id": "run-123",
        "dataset_name": "test-dataset-v1",
        "model_name": "gpt-4-turbo",
        "pass_rate": 0.50,
        "total_test_cases": 2,
        "passed_test_cases": 1,
        "started_at": "2023-10-27T10:00:00Z",
        "finished_at": "2023-10-27T10:05:00Z",
        "metrics_evaluated": ["accuracy"],
        "total_cost_usd": 0.15,
        "phoenix_precision": 0.92,
        "phoenix_drift": 0.01,
        "phoenix_experiment_url": "http://localhost:6006/projects/1"
    },
    "results": [
        {
            "test_case_id": "tc-1",
            "question": "What is RAG?",
            "answer": "Retrieval Augmented Generation.",
            "ground_truth": "RAG implies retrieving context...",
            "contexts": ["Context 1 about RAG"],
            "metrics": [
                { "name": "accuracy", "score": 1.0, "passed": true, "reason": "Exact match" }
            ]
        },
        {
            "test_case_id": "tc-2",
            "question": "Explain consistency.",
            "answer": "Consistency means...",
            "ground_truth": "Consistency...",
            "contexts": ["Context 2"],
            "metrics": [
                { "name": "accuracy", "score": 0.0, "passed": false, "reason": "Wrong answer" }
            ]
        }
    ]
};

test.describe('Run Details', () => {
    test.beforeEach(async ({ page }) => {
        // Note: API calls are mocked with /api/v1 prefix
        await page.route('**/api/v1/runs/run-123', async route => {
            await route.fulfill({ json: mockRunDetails });
        });

        await page.route('**/api/v1/runs/run-123/improvement*', async route => {
            await route.fulfill({ json: { run_id: 'run-123', improvements: [], summary: 'Good job' } });
        });

        await page.route('**/api/v1/runs/run-123/report*', async route => {
            await route.fulfill({ json: { run_id: 'run-123', content: '# Report', created_at: new Date().toISOString() } });
        });
    });

    test('should display run summary details', async ({ page }) => {
        await page.goto('/runs/run-123');

        await expect(page.getByText('test-dataset-v1')).toBeVisible();
        await expect(page.getByText('gpt-4-turbo')).toBeVisible();
        await expect(page.getByText('50.0%')).toBeVisible();
    });

    test('should display test cases and expand details on click', async ({ page }) => {
        await page.goto('/runs/run-123');

        await expect(page.getByText('What is RAG?')).toBeVisible();
        await expect(page.getByText('Explain consistency.')).toBeVisible();

        // Initial State: Ground Truth should NOT be visible (it's inside the expanded area)
        await expect(page.getByText('Ground Truth', { exact: true })).not.toBeVisible();

        // Click to expand
        await page.getByText('What is RAG?').click();

        // Now Ground Truth should be visible
        await expect(page.getByText('Ground Truth', { exact: true })).toBeVisible();
        await expect(page.getByText('RAG implies retrieving context...')).toBeVisible();
    });

    test('should switch to performance tab', async ({ page }) => {
        await page.goto('/runs/run-123');

        // Click Performance Tab
        await page.getByRole('button', { name: 'Performance' }).click();

        // Verify content specific to Performance tab
        await expect(page.getByText('Evaluation Speed')).toBeVisible();
        await expect(page.getByText('Estimated Cost')).toBeVisible();
    });
});
