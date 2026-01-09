import { test, expect } from "@playwright/test";

const mockFacts = [
    {
        fact_id: "fact-001",
        subject: "보험 계약",
        predicate: "포함",
        object: "면책 조항",
        domain: "insurance",
        verification_score: 0.92,
        created_at: new Date().toISOString(),
    },
];

const mockBehaviors = [
    {
        behavior_id: "behavior-001",
        description: "청구 조건 설명을 요약합니다.",
        success_rate: 0.87,
        use_count: 12,
    },
];

test.describe("Domain Memory", () => {
    test.beforeEach(async ({ page }) => {
        await page.route("**/api/v1/domain/facts?*", async (route) => {
            await route.fulfill({ json: mockFacts });
        });
        await page.route("**/api/v1/domain/behaviors?*", async (route) => {
            await route.fulfill({ json: mockBehaviors });
        });
    });

    test("should switch tabs and show domain memory data", async ({ page }) => {
        await page.goto("/domain");

        await expect(page.getByRole("heading", { name: "Domain Memory" })).toBeVisible();
        await expect(page.getByText("Verified Facts")).toBeVisible();
        await expect(page.getByText("보험 계약")).toBeVisible();

        await page.getByRole("button", { name: "Behaviors" }).click();
        await expect(page.getByText("청구 조건 설명을 요약합니다.")).toBeVisible();
        await expect(page.getByText("Uses: 12")).toBeVisible();

        await page.getByRole("button", { name: "Insights" }).click();
        await expect(page.getByText("Fact Verification Trend")).toBeVisible();
        await expect(page.getByText("Memory Health")).toBeVisible();
    });
});
