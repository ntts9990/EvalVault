import { test, expect } from '@playwright/test';

test.describe('Evaluation Studio', () => {
    test.beforeEach(async ({ page }) => {
        // Mock options calls with /api/v1
        await page.route('**/api/v1/runs/', async route => {
            await route.fulfill({ json: [] });
        });
        await page.route('**/api/v1/runs/options/datasets', async route => {
            await route.fulfill({ json: [{ name: 'dataset1', path: '/path/to/d1', type: 'json', size: 100 }] });
        });
        await page.route('**/api/v1/runs/options/models?*', async route => {
            await route.fulfill({ json: [{ id: 'gpt-4', name: 'GPT-4' }] });
        });

        // Config call needed for provider selection logic
        await page.route('**/api/v1/config/', async route => {
            await route.fulfill({ json: { llm_provider: 'openai' } });
        });

        await page.route('**/api/v1/runs/options/metrics', async route => {
            await route.fulfill({ json: ['accuracy', 'relevance'] });
        });

        await page.route('**/api/v1/runs/new-run-id', async route => {
            await route.fulfill({
                json: {
                    summary: {
                        run_id: 'new-run-id',
                        dataset_name: 'dataset1',
                        model_name: 'gpt-4',
                        pass_rate: 1.0,
                        total_test_cases: 1,
                        passed_test_cases: 1,
                        started_at: new Date().toISOString(),
                        finished_at: new Date().toISOString(),
                        metrics_evaluated: ['accuracy'],
                        total_cost_usd: 0.01,
                        phoenix_precision: null,
                        phoenix_drift: null,
                        phoenix_experiment_url: null
                    },
                    results: []
                }
            });
        });
    });

    test('should load form options', async ({ page }) => {
        await page.goto('/studio');

        await expect(page.getByRole('heading', { name: 'Evaluation Studio' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Start Evaluation' })).toBeVisible();

        // Check if datasets are loaded
        await expect(page.getByText('dataset1')).toBeVisible();
        await expect(page.getByText('GPT-4', { exact: true })).toBeVisible();
    });

    test('should start evaluation when form is filled and start button is clicked', async ({ page }) => {
        await page.goto('/studio');

        // Mock the start call with stream events
        await page.route('**/api/v1/runs/start', async route => {
            const resultEvent = {
                type: 'result',
                data: { run_id: 'new-run-id', status: 'running' }
            };
            await route.fulfill({
                body: JSON.stringify(resultEvent) + '\n'
            });
        });

        // 1. Select Dataset
        // The dataset is a div with onClick in the grid.
        await page.locator('text=dataset1').click();

        // 2. Select Model
        // The model is a div with onClick in the grid.
        await page.getByText('GPT-4', { exact: true }).click();

        // 3. Click Start
        await page.getByRole('button', { name: 'Start Evaluation' }).click();

        // 4. Verify navigation to the new run page
        // The component has a 500ms delay, standard 5000ms timeout should be fine, but maybe increase if needed.
        await expect(page).toHaveURL(/\/runs\/new-run-id/, { timeout: 10000 });
    });
});
