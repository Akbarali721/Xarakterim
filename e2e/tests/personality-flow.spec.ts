import { expect, test, type ConsoleMessage, type Page, type Response } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";

const CONSOLE_ERRORS: string[] = [];
const API_ERRORS: string[] = [];
const ROOT = path.resolve(__dirname, "..", "..");
const LOOKUP = path.resolve(__dirname, "..", "lookup_share.py");

function lookupShare(token: string): { shareCode: string; resultType: string; variant: string } {
  const out = execFileSync("python", [LOOKUP, token], {
    cwd: ROOT,
    env: process.env,
    encoding: "utf-8",
  })
    .trim()
    .split(/\r?\n/);
  return { shareCode: out[0], resultType: out[1] || "", variant: out[2] || "" };
}


function trackPage(page: Page) {
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() === "error") {
      CONSOLE_ERRORS.push(msg.text());
    }
  });
  page.on("pageerror", (err) => {
    CONSOLE_ERRORS.push(String(err));
  });
  page.on("response", (response: Response) => {
    const status = response.status();
    const url = response.url();
    if (status >= 400 && url.includes("/personality")) {
      API_ERRORS.push(`${status} ${response.request().method()} ${url}`);
    }
  });
}

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth + 1;
  });
  expect(overflow, "horizontal overflow").toBeFalsy();
}

async function completePersonalityTest(page: Page) {
  await page.goto("/personality");
  await expect(page.locator("#landing-title")).toBeVisible();

  // Jins tanlash olib tashlangan — to'g'ridan-to'g'ri boshlash.
  await page.locator('form[action="/personality/begin"] button[type="submit"]').click();
  await expect(page.locator("#start-btn")).toBeVisible();
  await page.locator("#start-btn").click();

  // Intent: maqsad tanlash (yosh bosqichi yo'q).
  await expect(page.locator(".mbti-intent-form")).toBeVisible();
  await page.locator('input[name="intent"][value="curiosity"]').check({ force: true });
  await page.locator(".mbti-intent-submit").click();

  await expect(page.locator("#answer-form")).toBeVisible();
  await expect(page.locator(".mbti-progress-label")).toContainText("1 / 24");

  for (let i = 0; i < 24; i += 1) {
    await expect(page.locator("#answer-form")).toBeVisible();
    const progress = page.locator(".mbti-progress-label");
    await expect(progress).toContainText(`${i + 1} / 24`);
    await assertNoHorizontalOverflow(page);

    // Birinchi variant — yashirin radio uchun label bosiladi.
    await page.locator("label.mbti-option").first().click();
    await expect(page.locator("#next-question-button")).toBeEnabled();
    await page.locator("#next-question-button").click();
  }

  // Loading → natija
  await page.waitForURL(/\/personality\/result\//, { timeout: 60_000 });
  if (page.url().includes("/loading")) {
    await page.waitForURL(/\/personality\/result\/[^/]+$/, { timeout: 60_000 });
  }
  await expect(page.locator(".mbti-result-page")).toBeVisible({ timeout: 30_000 });
}

test.beforeEach(async ({ page }) => {
  CONSOLE_ERRORS.length = 0;
  API_ERRORS.length = 0;
  trackPage(page);
});

test("full V2 personality flow, result, reload, share, premium modal", async ({ page }, testInfo) => {
  await completePersonalityTest(page);

  const resultUrl = page.url();
  const tokenMatch = resultUrl.match(/\/personality\/result\/([a-f0-9]+)/);
  expect(tokenMatch).toBeTruthy();
  const token = tokenMatch![1];

  // Natija ko'rinishi
  await expect(page.locator(".mbti-summary")).toBeVisible();
  await expect(page.locator(".mbti-formed")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Bugun sinab ko‘ring|Bugun sinab ko'ring/ })).toBeVisible();
  await expect(page.locator(".mbti-premium-locked-note")).toBeVisible();
  await assertNoHorizontalOverflow(page);

  const title = page.locator("h1.mbti-flow-title");
  await expect(title).toBeVisible();
  const titleText = (await title.innerText()).trim();
  expect(titleText.length).toBeGreaterThan(3);

  // Yangilashdan keyin o'zgarmasligi
  await page.reload();
  await expect(page.locator(".mbti-result-page")).toBeVisible();
  await expect(page.locator("h1.mbti-flow-title")).toHaveText(titleText);
  expect(page.url()).toContain(token);

  // Share: saqlangan share_code orqali /r/ (Telegram xabari yuborilmaydi).
  const meta = lookupShare(token);
  expect(meta.variant).toBe("V2");
  expect(meta.shareCode.length).toBeGreaterThan(4);

  const sharePage = await page.context().newPage();
  trackPage(sharePage);
  await sharePage.goto(`/r/${meta.shareCode}`);
  await expect(sharePage.locator(".mbti-share-card")).toBeVisible();
  await expect(sharePage.locator(".mbti-result-type")).toContainText(meta.resultType);
  await assertNoHorizontalOverflow(sharePage);
  await sharePage.close();

  // Referral tugmasi mavjud (DEV_MODE da t.me havola bo'lishi mumkin) — bosiladi, yuborilmaydi.
  if (await page.locator("#referral-share-btn").count()) {
    await expect(page.locator("#referral-url")).toBeAttached();
  }

  // Premium tugmasi — modal ochiladi; Telegram deep-link bor, lekin chek yuborilmaydi.
  await page.locator("#open-payment-modal").click();
  await expect(page.locator("#payment-modal")).toBeVisible();
  await expect(page.locator("#payment-test-code")).toBeVisible();
  await expect(page.locator(".mbti-telegram-pay-btn")).toBeVisible();
  await page.locator("#close-payment-modal").click();
  await expect(page.locator("#payment-modal")).toBeHidden();

  // CSP `script-src 'self'` telegram.org skriptini bloklaydi (mahsulotdagi ma'lum
  // ziddiyat). Foydalanuvchi oqimi shunga bog'liq emas — bu yerda shovqinni filtrlash.
  const seriousConsole = CONSOLE_ERRORS.filter((line) => {
    if (line.includes("favicon")) return false;
    if (
      line.includes("telegram.org/js/telegram-web-app.js") &&
      line.includes("Content Security Policy")
    ) {
      return false;
    }
    return true;
  });
  expect(seriousConsole, `console errors: ${seriousConsole.join(" | ")}`).toEqual([]);
  expect(API_ERRORS, `api errors: ${API_ERRORS.join(" | ")}`).toEqual([]);

  const shot = testInfo.outputPath(`result-${testInfo.project.name}.png`);
  await page.screenshot({ path: shot, fullPage: true });
});

test("question page layout stays usable at project viewport", async ({ page }) => {
  await page.goto("/personality");
  await page.locator('form[action="/personality/begin"] button[type="submit"]').click();
  await page.locator("#start-btn").click();
  await page.locator('input[name="intent"][value="self_understanding"]').check({ force: true });
  await page.locator(".mbti-intent-submit").click();

  await expect(page.locator(".mbti-progress-track")).toBeVisible();
  await expect(page.locator("label.mbti-option")).toHaveCount(4);
  await expect(page.locator("#next-question-button")).toBeVisible();
  await assertNoHorizontalOverflow(page);

  const optionBox = await page.locator("label.mbti-option").first().boundingBox();
  expect(optionBox).toBeTruthy();
  expect(optionBox!.width).toBeGreaterThan(200);
});
