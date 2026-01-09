import { test, expect } from '@playwright/test';

const now = new Date();
const dayMs = 24 * 60 * 60 * 1000;
const mockRuns = [
    {
        "run_id": "run-123",
        "dataset_name": "test-dataset-v1",
        "model_name": "gpt-4-turbo",
        "pass_rate": 0.855,
        "total_test_cases": 20,
        "passed_test_cases": 17,
        "started_at": new Date(now.getTime() - dayMs * 2).toISOString(),
        "finished_at": new Date(now.getTime() - dayMs * 2 + 5 * 60 * 1000).toISOString(),
        "metrics_evaluated": ["accuracy", "relevance"],
        "total_cost_usd": 0.15,
        "phoenix_precision": 0.92,
        "phoenix_drift": 0.01,
        "phoenix_experiment_url": "http://localhost:6006/projects/1"
    },
    {
        "run_id": "run-124",
        "dataset_name": "test-dataset-v2",
        "model_name": "claude-3-opus",
        "pass_rate": 0.90,
        "total_test_cases": 20,
        "passed_test_cases": 18,
        "started_at": new Date(now.getTime() - dayMs * 5).toISOString(),
        "finished_at": new Date(now.getTime() - dayMs * 5 + 10 * 60 * 1000).toISOString(),
        "metrics_evaluated": ["accuracy", "faithfulness"],
        "total_cost_usd": 0.25,
        "phoenix_precision": 0.95,
        "phoenix_drift": 0.0,
        "phoenix_experiment_url": null
    }
];

test.describe('Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        // Mock the runs API call
        await page.route('**/api/v1/runs/', async route => {
            await route.fulfill({ json: mockRuns });
        });
    });

    test('should display the dashboard with run list', async ({ page }) => {
        await page.goto('/');

        // Check for title or main heading - Updated to match Component
        await expect(page.getByText('Evaluation Overview')).toBeVisible();

        // Check if runs are displayed
        await expect(page.getByText('test-dataset-v1')).toBeVisible();
        await expect(page.getByText('test-dataset-v2')).toBeVisible();
        await expect(page.getByText('gpt-4-turbo')).toBeVisible();
    });

    test('should navigate to run details when clicking a run', async ({ page }) => {
        await page.goto('/');

        // Mock the details call for when we click
        await page.route('**/api/v1/runs/run-123', async route => {
            await route.fulfill({
                json: {
                    summary: mockRuns[0],
                    results: []
                }
            });
        });

        // Handle potential duplicate calls or ensuring route is set up before click

        const runRow = page.locator('text=test-dataset-v1').first();
        await runRow.click();

        // Verify URL change
        await expect(page).toHaveURL(/\/runs\/run-123/);
    });

    test('should enable compare button when two runs are selected', async ({ page }) => {
        await page.goto('/');

        const runCards = page.locator('.group.relative');
        // Click the checkbox area (top right) for the first two cards
        await runCards.nth(0).locator('.absolute.top-4.right-4').click();
        await runCards.nth(1).locator('.absolute.top-4.right-4').click();

        // Check if Compare button appears
        const compareBtn = page.getByRole('button', { name: 'Compare' });
        await expect(compareBtn).toBeVisible();
        await expect(compareBtn).toBeEnabled();

        // Click compare
        await compareBtn.click();

        // Verify navigation
        await expect(page).toHaveURL(/\/compare\?base=.*&target=.*/);
    });
});
