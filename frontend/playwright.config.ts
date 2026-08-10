import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for UI integration and E2E browser tests.
 * - ui-integration: FE-only flows (pages, store, navigation)
 * - e2e: full journeys that include APIs/services when available
 *
 * Note: `--slow-mo` is not a Playwright CLI flag. When running `--headed`,
 * we apply launchOptions.slowMo here so actions are easier to follow.
 */
function isHeadedMode() {
  // Workers inherit env; argv is only reliable in the main process.
  if (process.argv.includes('--headed') || process.argv.includes('--debug')) {
    process.env.HEADED_MODE = '1'
  }
  return process.env.HEADED_MODE === '1' || process.env.PWDEBUG === '1'
}

const headed = isHeadedMode()

export default defineConfig({
  fullyParallel: !headed,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: headed ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    launchOptions: headed ? { slowMo: 400 } : undefined,
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 3000',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'ui-integration',
      testDir: './e2e/ui-integration',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'e2e',
      testDir: './e2e/system',
      testMatch: /.*\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
