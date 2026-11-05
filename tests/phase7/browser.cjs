const { chromium } = require("playwright");
const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const cp = require("node:child_process");
const assert = require("node:assert/strict");

function totp(secret) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const bits = [...secret]
    .map((c) => alphabet.indexOf(c).toString(2).padStart(5, "0"))
    .join("");
  const bytes = [];
  for (let index = 0; index + 8 <= bits.length; index += 8)
    bytes.push(parseInt(bits.slice(index, index + 8), 2));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const digest = crypto
    .createHmac("sha1", Buffer.from(bytes))
    .update(counter)
    .digest();
  const offset = digest[19] & 15;
  return String((digest.readUInt32BE(offset) & 0x7fffffff) % 1000000).padStart(
    6,
    "0",
  );
}

async function main() {
  const origin = "http://localhost:38080";
  const email =
    "ui_" + crypto.randomUUID().replaceAll("-", "") + "@synthetic.invalid";
  const password = "Synthetic-password-32!";
  const steps = [];
  let userId,
    browser,
    stage = "register",
    passed = false;
  let failure;
  try {
    const registered = await fetch(origin + "/business/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Synthetic UI", email, password }),
    });
    assert.equal(registered.status, 200);
    userId = (await registered.json()).user.id;
    assert(Number.isSafeInteger(userId) && userId > 0);
    browser = await chromium.launch({
      executablePath:
        process.env.PLAYWRIGHT_EXECUTABLE_PATH ||
        (process.env.PLAYWRIGHT_BUNDLED_BROWSER
          ? undefined
          : "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
      headless: true,
      args: [
        "--disable-background-networking",
        "--no-first-run",
        "--no-default-browser-check",
      ],
    });
    const context = await browser.newContext({ acceptDownloads: true });
    const page = await context.newPage();
    stage = "browser-login";
    await page.goto(origin + "/login");
    await page.locator('input[name="email"]').fill(email);
    await page.locator('input[name="password"]').fill(password);
    await page
      .getByRole("button", { name: "Iniciar SesiÃ³n", exact: true })
      .click();
    await page.waitForURL("**/customer", { timeout: 25000 });
    const oldSession = await (
      await context.request.get(origin + "/api/auth/session")
    ).json();
    steps.push("browser credential login through NextAuth/GraphQL/Go");
    stage = "mfa-enrollment";
    await page.goto(origin + "/login/2fa");
    await page.locator('input[type="password"]').fill(password);
    const enrollmentResponse = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/logic/enable-2fa") &&
        response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Iniciar activaciÃ³n MFA" }).click();
    const enrollment = await (await enrollmentResponse).json();
    const secret = new URL(enrollment.otpauth_url).searchParams.get("secret");
    assert(secret);
    if (Date.now() % 30000 > 26000) await page.waitForTimeout(4500);
    await page
      .locator('input[autocomplete="one-time-code"]')
      .fill(totp(secret));
    await page.getByRole("button", { name: "Verifica y activa" }).click();
    await page
      .getByText("Guarda tus cÃ³digos de recuperaciÃ³n", { exact: true })
      .waitFor();
    const codes = (await page.locator("pre").innerText()).trim().split("\n");
    assert.equal(new Set(codes).size, 10);
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Descargar cÃ³digos" }).click();
    const download = await downloadPromise;
    assert.equal(
      (await fs.readFile(await download.path(), "utf8")).trim(),
      codes.join("\n"),
    );
    assert.equal(
      (
        await fetch(origin + "/business/api/me", {
          headers: { Authorization: "Bearer " + oldSession.accessToken },
        })
      ).status,
      401,
    );
    steps.push(
      "real MFA enrollment, one-time code display/download and prior-session rejection",
    );
    stage = "recovery";
    await page
      .getByRole("button", { name: "Ya los guardÃ©; iniciar sesiÃ³n" })
      .click();
    await page.waitForURL("**/login", { timeout: 15000 });
    await page.locator('input[name="email"]').fill(email);
    await page.locator('input[name="password"]').fill(password);
    await page.getByRole("button", { name: "PerdÃ­ mi autenticador" }).click();
    await page
      .getByText("CÃ³digo de recuperaciÃ³n guardado", { exact: true })
      .locator("..")
      .locator("input")
      .fill(codes[0]);
    const recoveryResponse = page.waitForResponse(
      (response) =>
        response.url().endsWith("/api/logic/mfa/recover") &&
        response.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Recuperar acceso", exact: true })
      .click();
    assert.equal((await recoveryResponse).status(), 200);
    await page
      .getByRole("button", { name: "Iniciar SesiÃ³n", exact: true })
      .click();
    await page.waitForURL("**/customer", { timeout: 25000 });
    steps.push("offline recovery form and successful subsequent browser login");
    stage = "operations";
    await page.goto(origin + "/operations");
    await page
      .getByRole("heading", { name: "Reservas, pagos y correo locales" })
      .waitFor();
    await page
      .getByRole("button", { name: "Consultar reservas", exact: true })
      .click();
    await page
      .getByRole("alert")
      .filter({ hasText: "Appointment not found" })
      .waitFor();
    await page.goto(origin + "/chatbot");
    await page.getByRole("heading", { name: "Chatbot", exact: true }).waitFor();
    steps.push(
      "operations and chat pages render, authorize and present controlled empty state",
    );
    stage = "uncertain-operation-review";
    const conversation = "ui_" + crypto.randomUUID();
    const operation = crypto.randomUUID();
    const message = "cancelar 999999";
    const digest = crypto.createHash("sha256").update(message).digest("hex");
    const seeded = cp.spawnSync(
      "docker",
      [
        "exec",
        "-i",
        "fullstyle-portfolio-postgres-1",
        "psql",
        "-U",
        "synthetic",
        "-d",
        "fullstyle_synthetic",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        `INSERT INTO chat_turn(user_id,session_id,operation_id,message,message_hash,state,content_expires_at) VALUES(${userId},'${conversation}','${operation}','${message}','${digest}','uncertain',now()-interval '1 day')`,
      ],
      { encoding: "utf8" },
    );
    assert.equal(
      seeded.status,
      0,
      "Owned synthetic chat fixture could not be created",
    );
    let sends = 0;
    page.on("request", (request) => {
      if (request.url().endsWith("/chat/send")) sends++;
    });
    await page
      .getByLabel("ConversaciÃ³n (guarda el identificador para continuar)", {
        exact: true,
      })
      .fill(conversation);
    await page.getByRole("button", { name: "Cargar historial" }).click();
    await page.getByText("Estado: uncertain", { exact: true }).waitFor();
    await page.getByLabel("Ya consultÃ© el estado de mi reserva").check();
    await page
      .getByLabel("Nota de revisiÃ³n")
      .fill("Consulted my empty bookings; outcome reviewed");
    await page.getByRole("button", { name: "Registrar revisiÃ³n" }).click();
    await page.getByText("Estado: reviewed", { exact: true }).waitFor();
    assert.equal(sends, 0);
    const currentSession = await (
      await context.request.get(origin + "/api/auth/session")
    ).json();
    const deadline = Date.now() + 70000;
    let redacted = false;
    while (Date.now() < deadline) {
      const result = await context.request.get(
        origin + `/chatbot/api/v1/chat/history/${conversation}`,
        { headers: { Authorization: "Bearer " + currentSession.accessToken } },
      );
      assert.equal(result.status(), 200);
      const history = await result.json();
      assert.equal(history.turns.length, 1);
      assert.equal(history.turns[0].state, "reviewed");
      if (history.turns[0].message === "") {
        redacted = true;
        break;
      }
      await page.waitForTimeout(1000);
    }
    assert(
      redacted,
      "Scheduled retention did not redact the expired reviewed content",
    );
    steps.push(
      "uncertain outcome reviewed through UI without resend; scheduled retention preserves one deduplication tombstone",
    );
    passed = true;
  } catch (error) {
    failure = { stage, message: error.message.slice(0, 1200) };
  } finally {
    if (browser) await browser.close();
    if (userId) {
      const sql = `BEGIN; DELETE FROM session_revocation WHERE subject='${userId}'; DELETE FROM client WHERE id=${userId}; DELETE FROM userr WHERE id=${userId} AND email='${email}'; COMMIT;`;
      const result = cp.spawnSync(
        "docker",
        [
          "exec",
          "-i",
          "fullstyle-portfolio-postgres-1",
          "psql",
          "-U",
          "synthetic",
          "-d",
          "fullstyle_synthetic",
          "-v",
          "ON_ERROR_STOP=1",
          "-c",
          sql,
        ],
        { encoding: "utf8" },
      );
      if (result.status !== 0) {
        passed = false;
        failure = {
          stage: "cleanup",
          message: "Owned synthetic account cleanup failed",
        };
      }
    }
    const report = {
      checked_utc: new Date().toISOString(),
      passed,
      steps,
      failure,
      synthetic_only: true,
      browser: "headless Microsoft Edge, fresh disposable profile",
      providers_contacted: false,
    };
    await fs.writeFile(
      ".quality/reports/additional-browser.json",
      JSON.stringify(report, null, 2) + "\n",
    );
    console.log(JSON.stringify(report));
  }
  process.exitCode = passed ? 0 : 1;
}
main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
