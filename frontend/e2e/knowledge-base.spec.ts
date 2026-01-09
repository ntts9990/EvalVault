import { test, expect } from "@playwright/test";

test.describe("Knowledge Base", () => {
    test.beforeEach(async ({ page }) => {
        let statsCalls = 0;
        await page.route("**/api/v1/knowledge/stats", async (route) => {
            statsCalls += 1;
            const payload =
                statsCalls < 2
                    ? { num_entities: 0, num_relations: 0, status: "not_built" }
                    : { num_entities: 12, num_relations: 24, status: "available" };
            await route.fulfill({ json: payload });
        });

        await page.route("**/api/v1/knowledge/upload", async (route) => {
            await route.fulfill({ json: { message: "uploaded", files: ["doc.txt"] } });
        });

        await page.route("**/api/v1/knowledge/build", async (route) => {
            await route.fulfill({ json: { status: "queued", job_id: "job-123" } });
        });

        let jobCalls = 0;
        await page.route("**/api/v1/knowledge/jobs/*", async (route) => {
            jobCalls += 1;
            const status = jobCalls < 2 ? "running" : "completed";
            const progress = jobCalls < 2 ? "45%" : "100%";
            await route.fulfill({
                json: { status, progress, message: status },
            });
        });
    });

    test("should upload documents and build knowledge graph", async ({ page }) => {
        await page.goto("/knowledge");

        await expect(page.getByRole("heading", { name: "Knowledge Base" })).toBeVisible();
        await expect(page.getByText("KG Status")).toBeVisible();

        await page.setInputFiles("#file-upload", {
            name: "doc.txt",
            mimeType: "text/plain",
            buffer: Buffer.from("hello world"),
        });

        await expect(page.getByText(/Selected Files/)).toBeVisible();

        await Promise.all([
            page.waitForRequest("**/api/v1/knowledge/upload"),
            page.getByRole("button", { name: "Upload Files" }).click(),
        ]);

        await expect(page.getByText(/Selected Files/)).toHaveCount(0);

        await page.getByRole("button", { name: "Start Build Process" }).click();

        await expect(page.getByText("Building...")).toBeVisible();
        await expect(page.getByText("45%")).toBeVisible();
        await expect(page.getByText("pending")).toBeVisible();

        await expect(page.getByRole("button", { name: "Start Build Process" })).toBeVisible({
            timeout: 5000,
        });
        await expect(page.getByText("Ready")).toBeVisible();
    });
});
